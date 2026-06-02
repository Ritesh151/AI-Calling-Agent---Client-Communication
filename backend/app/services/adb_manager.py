from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings
from app.core.exceptions import AppException


@dataclass
class DeviceInfo:
    serial: str
    manufacturer: str = ""
    model: str = ""
    android_version: str = ""
    android_id: str = ""
    state: str = "disconnected"
    properties: dict[str, str] = field(default_factory=dict)


class ADBManager:
    def __init__(self) -> None:
        self._adb_path: str = "adb"
        self._connected_devices: dict[str, DeviceInfo] = {}
        self._is_connected: bool = False

    async def connect(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                self._adb_path, "start-server",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise AppException(
                    message=f"Failed to start ADB server: {stderr.decode().strip()}",
                    error_code="ADB_CONNECT_ERROR",
                )
            self._is_connected = True
            return True
        except FileNotFoundError:
            raise AppException(
                message="ADB executable not found. Please install Android Debug Bridge.",
                error_code="ADB_NOT_FOUND",
            )

    async def disconnect(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                self._adb_path, "kill-server",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            self._is_connected = False
            self._connected_devices.clear()
            return True
        except FileNotFoundError:
            return False

    async def list_devices(self) -> list[DeviceInfo]:
        proc = await asyncio.create_subprocess_exec(
            self._adb_path, "devices", "-l",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise AppException(
                message=f"Failed to list devices: {stderr.decode().strip()}",
                error_code="ADB_LIST_DEVICES_ERROR",
            )

        devices: list[DeviceInfo] = []
        output = stdout.decode().strip()
        lines = output.split("\n")

        for line in lines[1:]:
            if not line.strip():
                continue
            parts = re.split(r"\s+", line.strip())
            if len(parts) < 2:
                continue
            serial = parts[0]
            state = parts[1]

            info = DeviceInfo(serial=serial, state=state)

            for part in parts[2:]:
                if part.startswith("product:"):
                    pass
                elif part.startswith("model:"):
                    info.model = part.replace("model:", "")
                elif part.startswith("device:"):
                    pass

            if state == "device":
                try:
                    device_info = await self.get_device_info(serial)
                    info.manufacturer = device_info.manufacturer
                    info.model = device_info.model or info.model
                    info.android_version = device_info.android_version
                    info.android_id = device_info.android_id
                except Exception:
                    pass

            devices.append(info)
            self._connected_devices[serial] = info

        return devices

    async def get_device_info(self, serial: str) -> DeviceInfo:
        info = DeviceInfo(serial=serial)

        prop_map = {
            "ro.product.manufacturer": "manufacturer",
            "ro.product.model": "model",
            "ro.build.version.release": "android_version",
            "ro.build.version.sdk": "android_sdk",
        }

        for prop, attr in prop_map.items():
            try:
                value = await self._get_property(serial, prop)
                if value:
                    setattr(info, attr, value)
            except Exception:
                pass

        try:
            info.android_id = await self._get_android_id(serial)
        except Exception:
            pass

        try:
            info.state = await self._get_device_state(serial)
        except Exception:
            info.state = "unknown"

        return info

    async def is_device_online(self, serial: str) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                self._adb_path, "-s", serial, "get-state",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip() == "device"
        except Exception:
            return False

    async def execute_command(self, serial: str, command: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            self._adb_path, "-s", serial, "shell", command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            timeout=settings.DEVICE_TIMEOUT_SECONDS,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise AppException(
                message=f"ADB command failed: {stderr.decode().strip()}",
                error_code="ADB_COMMAND_ERROR",
            )
        return stdout.decode().strip()

    async def _get_property(self, serial: str, prop: str) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                self._adb_path, "-s", serial, "shell", f"getprop {prop}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip()
        except Exception:
            return ""

    async def _get_android_id(self, serial: str) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                self._adb_path, "-s", serial, "shell",
                "settings get secure android_id",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip()
        except Exception:
            return ""

    async def _get_device_state(self, serial: str) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                self._adb_path, "-s", serial, "get-state",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return stdout.decode().strip()
        except Exception:
            return "unknown"

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def get_cached_devices(self) -> dict[str, DeviceInfo]:
        return self._connected_devices.copy()
