from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import psutil

from app.services.adb_watcher import ADBCommandStatus, adb_engine
from app.services.compatibility.adb_reliability.adb_reliability_service import (
    ADBReliabilityService,
    FailureType,
)

logger = logging.getLogger(__name__)


class StressTestResult:
    def __init__(
        self,
        device_id: int,
        duration_hours: int,
        connection_stability: float,
        avg_memory_mb: float,
        max_memory_mb: float,
        failure_rate: float,
        recovery_success_rate: float,
        total_operations: int,
        failed_operations: int,
        recovered_operations: int,
        certificate_retained: bool,
        completed_at: str,
    ) -> None:
        self.device_id = device_id
        self.duration_hours = duration_hours
        self.connection_stability = connection_stability
        self.avg_memory_mb = avg_memory_mb
        self.max_memory_mb = max_memory_mb
        self.failure_rate = failure_rate
        self.recovery_success_rate = recovery_success_rate
        self.total_operations = total_operations
        self.failed_operations = failed_operations
        self.recovered_operations = recovered_operations
        self.certificate_retained = certificate_retained
        self.completed_at = completed_at


class StressTestService:
    def __init__(self, db_session_factory: Any) -> None:
        self.db_session_factory = db_session_factory
        self._running_tests: set[str] = set()

    async def run_stress_test(
        self,
        device_id: int,
        duration_hours: int = 1,
        operations_per_minute: int = 10,
    ) -> StressTestResult:
        str_id = str(device_id)
        if str_id in self._running_tests:
            raise RuntimeError(f"Stress test already running for device {device_id}")
        self._running_tests.add(str_id)

        try:
            return await self._execute_stress_test(device_id, duration_hours, operations_per_minute)
        finally:
            self._running_tests.discard(str_id)

    async def _execute_stress_test(
        self,
        device_id: int,
        duration_hours: int,
        ops_per_min: int,
    ) -> StressTestResult:
        duration_seconds = duration_hours * 3600
        interval = 60.0 / ops_per_min
        start_time = time.time()
        end_time = start_time + duration_seconds

        total_ops = 0
        failed_ops = 0
        recovered_ops = 0
        memory_samples: list[float] = []
        connection_failures = 0
        connection_checks = 0

        test_commands = [
            "echo ok",
            "getprop ro.build.version.sdk",
            "dumpsys battery",
            "dumpsys power | grep mScreenOn",
            "wm size",
        ]

        logger.info(
            "Starting stress test for device %d: %dh, %d ops/min",
            device_id, duration_hours, ops_per_min,
        )

        while time.time() < end_time:
            cmd = test_commands[total_ops % len(test_commands)]
            total_ops += 1

            try:
                result = await adb_engine.shell(str(device_id), cmd)
                connection_checks += 1
                if result.status == ADBCommandStatus.SUCCESS:
                    if result.stdout.strip():
                        pass
                    else:
                        connection_failures += 1
                else:
                    connection_failures += 1
                    recovered = await self._attempt_recovery_quick(device_id)
                    if recovered:
                        recovered_ops += 1
                    else:
                        failed_ops += 1
            except Exception:
                connection_failures += 1
                failed_ops += 1

            mem = psutil.Process().memory_info().rss / (1024 * 1024)
            memory_samples.append(mem)

            elapsed = time.time() - start_time
            remaining = end_time - time.time()
            if total_ops % 50 == 0:
                progress = (elapsed / duration_seconds) * 100
                logger.info(
                    "Stress test %s: %.1f%% complete, ops=%d, fail=%d, recov=%d, mem=%.0fMB",
                    device_id, progress, total_ops, failed_ops, recovered_ops, mem,
                )

            await asyncio.sleep(interval)

        connection_stability = 1.0 - (connection_failures / max(connection_checks, 1))
        failure_rate = failed_ops / max(total_ops, 1)
        recovery_success_rate = recovered_ops / max(failed_ops + recovered_ops, 1)
        avg_memory = sum(memory_samples) / len(memory_samples) if memory_samples else 0
        max_memory = max(memory_samples) if memory_samples else 0

        certificate_retained = connection_stability >= 0.8 and failure_rate < 0.2

        result = StressTestResult(
            device_id=device_id,
            duration_hours=duration_hours,
            connection_stability=round(connection_stability, 3),
            avg_memory_mb=round(avg_memory, 1),
            max_memory_mb=round(max_memory, 1),
            failure_rate=round(failure_rate, 3),
            recovery_success_rate=round(recovery_success_rate, 3),
            total_operations=total_ops,
            failed_operations=failed_ops,
            recovered_operations=recovered_ops,
            certificate_retained=certificate_retained,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "Stress test completed for device %d: stability=%.1f%% fail=%.1f%% mem=%.0fMB cert=%s",
            device_id, connection_stability * 100, failure_rate * 100, avg_memory, certificate_retained,
        )

        return result

    async def _attempt_recovery_quick(self, device_id: int) -> bool:
        try:
            result = await adb_engine.shell(str(device_id), "echo recover")
            return result.status == ADBCommandStatus.SUCCESS
        except Exception:
            return False

    def is_test_running(self, device_id: int) -> bool:
        return str(device_id) in self._running_tests

    def stop_test(self, device_id: int) -> bool:
        return self._running_tests.discard(str(device_id))
