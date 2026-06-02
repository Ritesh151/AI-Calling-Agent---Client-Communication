from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class ADBCommandStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ADBCommandResult:
    command: str
    status: ADBCommandStatus
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    exit_code: int = -1
    error_message: str = ""


@dataclass
class ADBDeviceInfo:
    serial: str
    state: str = "disconnected"
    manufacturer: str = ""
    model: str = ""
    android_version: str = ""
    android_sdk: str = ""
    android_id: str = ""
    battery_level: int = -1
    charging: bool = False
    screen_state: str = "unknown"
    usb_connected: bool = False
    device_ip: str = ""
    properties: dict[str, str] = field(default_factory=dict)


class ADBEngine:
    COMMAND_WHITELIST = {
        "shell:dumpsys telephony.registry",
        "shell:dumpsys battery",
        "shell:dumpsys power",
        "shell:dumpsys connectivity",
        "shell:dumpsys deviceidle",
        "shell:getprop",
        "shell:settings get secure android_id",
        "shell:service call iphonesubinfo 1",
        "shell:input keyevent KEYCODE_CALL",
        "shell:input keyevent KEYCODE_ENDCALL",
        "shell:input keyevent 5",
        "shell:input keyevent 6",
        "shell:wm size",
        "shell:netstat",
        "shell:ifconfig",
        "shell:ip addr show",
        "shell:cat /proc/stat",
        "shell:cat /proc/meminfo",
        "shell:screenrecord",
        "shell:pkill",
        "shell:cmd media recorder",
        "shell:which",
        "shell:content insert",
        "shell:dumpsys media.audio_flinger",
        "pull",
        "devices",
        "devices -l",
        "start-server",
        "kill-server",
        "get-state",
        "wait-for-device",
    }

    def __init__(self) -> None:
        self._adb_path: str = "adb"
        self._devices: dict[str, ADBDeviceInfo] = {}
        self._server_running: bool = False
        self._command_queue: asyncio.Queue[tuple[str, str, asyncio.Future]] = asyncio.Queue(
            maxsize=settings.ADB_COMMAND_QUEUE_MAX_SIZE
        )
        self._device_locks: dict[str, asyncio.Lock] = {}
        self._queue_worker: asyncio.Task | None = None
        self._running = False
        self._global_lock = asyncio.Lock()

    async def start_server(self) -> bool:
        async with self._global_lock:
            if self._server_running:
                return True
            try:
                result = await self._execute_adb("start-server")
                self._server_running = result.exit_code == 0
                if self._server_running:
                    self._ensure_queue_worker()
                    logger.info("ADB server started")
                else:
                    raise AppException(
                        message=f"Failed to start ADB server: {result.stderr}",
                        error_code="ADB_START_ERROR",
                    )
                return self._server_running
            except FileNotFoundError:
                raise AppException(
                    message="ADB executable not found. Please install Android Debug Bridge.",
                    error_code="ADB_NOT_FOUND",
                )

    async def stop_server(self) -> bool:
        async with self._global_lock:
            try:
                result = await self._execute_adb("kill-server")
                self._server_running = False
                self._devices.clear()
                logger.info("ADB server stopped")
                return result.exit_code == 0
            except Exception:
                self._server_running = False
                return False

    async def restart_server(self) -> bool:
        await self.stop_server()
        await asyncio.sleep(1)
        return await self.start_server()

    async def list_devices(self) -> list[ADBDeviceInfo]:
        result = await self._execute_adb("devices -l")
        if result.status != ADBCommandStatus.SUCCESS:
            raise AppException(
                message=f"Failed to list devices: {result.stderr}",
                error_code="ADB_LIST_ERROR",
            )

        devices: list[ADBDeviceInfo] = []
        lines = result.stdout.strip().split("\n")

        for line in lines[1:]:
            if not line.strip():
                continue
            parts = re.split(r"\s+", line.strip())
            if len(parts) < 2:
                continue
            info = ADBDeviceInfo(serial=parts[0], state=parts[1])
            for part in parts[2:]:
                if part.startswith("model:"):
                    info.model = part.replace("model:", "").replace("_", " ")
            devices.append(info)
            self._devices[info.serial] = info

        return devices

    async def get_device_info(self, serial: str) -> ADBDeviceInfo:
        info = ADBDeviceInfo(serial=serial)
        prop_map = {
            "ro.product.manufacturer": "manufacturer",
            "ro.product.model": "model",
            "ro.build.version.release": "android_version",
            "ro.build.version.sdk": "android_sdk",
            "ro.serialno": "serial",
        }
        props_result = await self._execute_adb(f"shell:getprop", serial=serial)
        if props_result.status == ADBCommandStatus.SUCCESS:
            for line in props_result.stdout.split("\n"):
                match = re.match(r"\[([^\]]+)\]:\s*\[([^\]]*)\]", line.strip())
                if match:
                    key, value = match.groups()
                    if key in prop_map:
                        setattr(info, prop_map[key], value)
                    info.properties[key] = value

        try:
            aid = await self._execute_adb("shell:settings get secure android_id", serial=serial)
            if aid.status == ADBCommandStatus.SUCCESS:
                info.android_id = aid.stdout.strip()
        except Exception:
            pass

        try:
            state = await self._execute_adb("get-state", serial=serial)
            if state.status == ADBCommandStatus.SUCCESS:
                info.state = state.stdout.strip()
        except Exception:
            pass

        await self._update_device_metrics(info)
        return info

    async def _update_device_metrics(self, info: ADBDeviceInfo) -> None:
        try:
            battery = await self._execute_adb("shell:dumpsys battery", serial=info.serial)
            if battery.status == ADBCommandStatus.SUCCESS:
                for line in battery.stdout.split("\n"):
                    l = line.strip()
                    if "level" in l and ":" in l:
                        try:
                            info.battery_level = int(l.split(":")[1].strip())
                        except ValueError:
                            pass
                    if "AC powered" in l and ":" in l:
                        info.charging = "true" in l.split(":")[1].strip().lower()
                    if "USB powered" in l and ":" in l:
                        info.usb_connected = "true" in l.split(":")[1].strip().lower()
        except Exception:
            pass

        try:
            power = await self._execute_adb("shell:dumpsys power", serial=info.serial)
            if power.status == ADBCommandStatus.SUCCESS:
                for line in power.stdout.split("\n"):
                    if "mScreenState" in line or "mWakefulness" in line:
                        if "=" in line:
                            val = line.split("=")[1].strip()
                            if "ON" in val or "AWAKE" in val:
                                info.screen_state = "on"
                            elif "OFF" in val or "DREAM" in val or "DOZE" in val:
                                info.screen_state = "off"
                            else:
                                info.screen_state = val.lower()
        except Exception:
            pass

        try:
            ip = await self._execute_adb("shell:ip addr show", serial=info.serial)
            if ip.status == ADBCommandStatus.SUCCESS:
                for line in ip.stdout.split("\n"):
                    match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", line)
                    if match and not match.group(1).startswith("127."):
                        info.device_ip = match.group(1)
                        break
        except Exception:
            pass

    async def get_android_version(self, serial: str) -> str:
        result = await self._execute_adb("shell:getprop ro.build.version.release", serial=serial)
        return result.stdout.strip() if result.status == ADBCommandStatus.SUCCESS else ""

    async def get_serial(self, serial: str) -> str:
        return serial

    async def get_manufacturer(self, serial: str) -> str:
        result = await self._execute_adb("shell:getprop ro.product.manufacturer", serial=serial)
        return result.stdout.strip() if result.status == ADBCommandStatus.SUCCESS else ""

    async def get_model(self, serial: str) -> str:
        result = await self._execute_adb("shell:getprop ro.product.model", serial=serial)
        return result.stdout.strip() if result.status == ADBCommandStatus.SUCCESS else ""

    async def shell(self, serial: str, command: str) -> ADBCommandResult:
        if not self._is_command_allowed(f"shell:{command}"):
            return ADBCommandResult(
                command=command,
                status=ADBCommandStatus.FAILED,
                error_message=f"Command not whitelisted: {command[:50]}",
            )
        return await self._execute_adb(f"shell:{command}", serial=serial)

    async def execute(self, serial: str, command: str) -> ADBCommandResult:
        if not self._is_command_allowed(command):
            return ADBCommandResult(
                command=command,
                status=ADBCommandStatus.FAILED,
                error_message=f"Command not whitelisted: {command[:50]}",
            )
        return await self._execute_adb(command, serial=serial)

    async def is_online(self, serial: str) -> bool:
        result = await self._execute_adb("get-state", serial=serial)
        return result.status == ADBCommandStatus.SUCCESS and result.stdout.strip() == "device"

    async def wait_for_device(self, serial: str, timeout: int = 30) -> bool:
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if await self.is_online(serial):
                return True
            await asyncio.sleep(1)
        return False

    async def reconnect(self) -> bool:
        try:
            await self._execute_adb("kill-server")
            await asyncio.sleep(2)
            await self._execute_adb("start-server")
            self._server_running = True
            return True
        except Exception as e:
            logger.error("ADB reconnect failed: %s", e)
            return False

    async def health_check(self) -> dict[str, Any]:
        result = await self._execute_adb("devices")
        is_healthy = result.status == ADBCommandStatus.SUCCESS
        return {
            "server_running": self._server_running,
            "is_healthy": is_healthy,
            "devices_found": len(self._devices) if is_healthy else 0,
            "last_check": datetime.now(UTC).isoformat(),
        }

    def _is_command_allowed(self, command: str) -> bool:
        for allowed in self.COMMAND_WHITELIST:
            if command.startswith(allowed):
                return True
        return False

    async def _execute_adb(self, raw_command: str, serial: str | None = None) -> ADBCommandResult:
        start_time = time.monotonic()
        result = ADBCommandResult(command=raw_command, status=ADBCommandStatus.PENDING)

        try:
            args = [self._adb_path]
            if serial and raw_command not in (
                "start-server",
                "kill-server",
                "devices",
                "devices -l",
            ):
                args.extend(["-s", serial])

            is_shell = raw_command.startswith("shell:")
            if is_shell:
                shell_cmd = raw_command[6:]
                args.extend(["shell", shell_cmd])
            else:
                args.extend(raw_command.split())

            logger.debug("ADB execute: %s", " ".join(args))

            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=settings.DEVICE_TIMEOUT_SECONDS
                )
                result.stdout = stdout.decode(errors="replace").strip()
                result.stderr = stderr.decode(errors="replace").strip()
                result.exit_code = proc.returncode or 0
                result.execution_time = time.monotonic() - start_time

                if proc.returncode == 0:
                    result.status = ADBCommandStatus.SUCCESS
                else:
                    result.status = ADBCommandStatus.FAILED
                    result.error_message = result.stderr

            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                result.status = ADBCommandStatus.TIMEOUT
                result.error_message = f"Command timed out after {settings.DEVICE_TIMEOUT_SECONDS}s"
                result.execution_time = time.monotonic() - start_time

        except FileNotFoundError:
            result.status = ADBCommandStatus.FAILED
            result.error_message = "ADB executable not found"
        except Exception as e:
            result.status = ADBCommandStatus.FAILED
            result.error_message = str(e)
            result.execution_time = time.monotonic() - start_time

        return result

    def _ensure_queue_worker(self) -> None:
        if self._queue_worker is None or self._queue_worker.done():
            self._queue_worker = asyncio.create_task(self._queue_processor())

    async def _queue_processor(self) -> None:
        while True:
            try:
                serial, command, future = await asyncio.wait_for(
                    self._command_queue.get(), timeout=1.0
                )
                result = await self._execute_adb(command, serial=serial)
                future.set_result(result)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Queue processor error: %s", e)

    def get_device_lock(self, serial: str) -> asyncio.Lock:
        if serial not in self._device_locks:
            self._device_locks[serial] = asyncio.Lock()
        return self._device_locks[serial]

    @property
    def is_server_running(self) -> bool:
        return self._server_running

    @property
    def connected_devices(self) -> dict[str, ADBDeviceInfo]:
        return self._devices.copy()


adb_engine = ADBEngine()
