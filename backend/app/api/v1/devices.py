from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, require_role
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate
from app.services.device_service import DeviceService
from app.services.adb_manager import ADBManager
from app.services.device_discovery import DeviceDiscoveryService
from app.services.device_sync import device_sync_service
from app.services.adb_watcher import adb_engine
from app.services.call_detector import CallDetectionEngine
from app.services.call_detector.auto_answer import AutoAnswerService
from app.services.event_bus import event_bus
from app.services.websocket import ws_manager

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("/adb-status", response_model=SuccessResponse[dict])
async def get_global_adb_status(
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    try:
        health = await adb_engine.health_check()
        devices = await adb_engine.list_devices()
        connected = [d for d in devices if d.state == "device"]
        unauthorized = [d for d in devices if d.state == "unauthorized"]
        offline = [d for d in devices if d.state == "offline"]

        server_running = health.get("server_running", False)
        is_healthy = health.get("is_healthy", False)

        if not server_running:
            status_label = "disconnected"
        elif not is_healthy:
            status_label = "error"
        elif unauthorized:
            status_label = "unauthorized"
        else:
            status_label = "active"

        return SuccessResponse(
            data={
                "server_running": server_running,
                "server_status": status_label,
                "devices_found": health.get("devices_found", 0),
                "connected_devices": len(connected),
                "unauthorized_devices": len(unauthorized),
                "offline_devices": len(offline),
                "is_healthy": is_healthy,
                "last_check": health.get("last_check", ""),
            }
        )
    except Exception as e:
        return SuccessResponse(
            data={
                "server_running": False,
                "server_status": "error",
                "devices_found": 0,
                "connected_devices": 0,
                "unauthorized_devices": 0,
                "offline_devices": 0,
                "is_healthy": False,
                "last_check": "",
                "error": str(e),
            }
        )


async def _sync_devices_live(db: Session) -> None:
    """ADB is the source of truth — reconcile DB before serving device lists."""
    await device_sync_service.sync(db)


@router.post("/cleanup", response_model=SuccessResponse[dict])
async def cleanup_devices(
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[dict]:
    """Cleanup stale and duplicate devices."""
    service = DeviceService(db)
    
    stale_result = service.cleanup_stale_devices()
    dup_result = service.cleanup_duplicate_devices()
    
    return SuccessResponse(
        message="Device cleanup completed",
        data={
            **stale_result,
            **dup_result,
        },
    )


@router.post("/sync", response_model=SuccessResponse[dict])
async def sync_devices(
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    result = await device_sync_service.sync(db)
    return SuccessResponse(
        message="Devices synchronized with ADB",
        data={
            "connected_count": result.connected_count,
            "total_count": result.total_registered,
            "adb_devices_found": result.adb_devices_found,
            "updated": result.updated,
            "disconnected": result.disconnected,
        },
    )


@router.get("/", response_model=SuccessResponse[list[DeviceRead]])
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    sync: bool = Query(False, description="Reconcile with ADB before returning"),  # ✅ Changed to False (was True)
    adb_present_only: bool = Query(
        False,
        description="Only return devices currently visible to ADB as connected",
    ),
    search: str | None = Query(None, description="Search by name, serial, manufacturer, model, or android version"),
    connected_only: bool = Query(False, description="Only return connected devices"),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[DeviceRead]]:
    sync_result = None
    if sync:
        sync_result = await device_sync_service.sync(db)
    service = DeviceService(db)
    if adb_present_only:
        if sync_result and sync_result.adb_devices_found == 0:
            return SuccessResponse(data=[])
        devices = service.get_connected_devices()
        return SuccessResponse(data=devices[:limit])
    if connected_only:
        devices = service.get_connected_devices()
    else:
        devices = service.get_all_devices(skip=skip, limit=limit)
    if search:
        search_lower = search.lower()
        devices = [
            d for d in devices
            if (d.device_name and search_lower in d.device_name.lower())
            or (d.serial_number and search_lower in d.serial_number.lower())
            or (d.manufacturer and search_lower in d.manufacturer.lower())
            or (d.model and search_lower in d.model.lower())
            or (d.android_version and search_lower in d.android_version.lower())
        ]
    return SuccessResponse(data=devices)


@router.get("/connected", response_model=SuccessResponse[list[DeviceRead]])
async def list_connected_devices(
    sync: bool = Query(True, description="Reconcile with ADB before returning"),
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[list[DeviceRead]]:
    sync_result = await device_sync_service.sync(db) if sync else None
    if sync_result and sync_result.adb_devices_found == 0:
        return SuccessResponse(data=[])
    service = DeviceService(db)
    devices = service.get_connected_devices()
    return SuccessResponse(data=devices)


@router.get("/{device_id}", response_model=SuccessResponse[DeviceRead])
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[DeviceRead]:
    service = DeviceService(db)
    device = service.get_device(device_id)
    return SuccessResponse(data=device)


@router.post("/", response_model=SuccessResponse[DeviceRead])
def register_device(
    request: DeviceCreate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[DeviceRead]:
    service = DeviceService(db)
    device = service.register_device(request)
    return SuccessResponse(message="Device registered", data=device)


@router.put("/{device_id}", response_model=SuccessResponse[DeviceRead])
def update_device(
    device_id: int,
    request: DeviceUpdate,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[DeviceRead]:
    service = DeviceService(db)
    device = service.update_device(device_id, request)
    return SuccessResponse(message="Device updated", data=device)


@router.delete("/{device_id}", response_model=SuccessResponse[None])
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[None]:
    service = DeviceService(db)
    service.delete_device(device_id)
    return SuccessResponse(message="Device deleted")


@router.post("/discover", response_model=SuccessResponse[list[dict]])
async def discover_devices(
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[list[dict]]:
    adb = ADBManager()
    discovery = DeviceDiscoveryService(db, adb)
    devices = await discovery.discover_devices()
    return SuccessResponse(
        message=f"Discovered {len(devices)} device(s)", data=devices
    )


@router.post("/{device_id}/heartbeat", response_model=SuccessResponse[DeviceRead])
def device_heartbeat(
    device_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[DeviceRead]:
    service = DeviceService(db)
    device = service.update_heartbeat(device_id)
    return SuccessResponse(data=device)


@router.get("/{device_id}/call-state", response_model=SuccessResponse[dict])
async def get_device_call_state(
    device_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    from app.services.adb_watcher import adb_engine
    from app.services.call_detector import CallDetectionEngine
    from app.services.event_bus import event_bus

    service = DeviceService(db)
    device = service.get_device(device_id)
    if not device.serial_number:
        return SuccessResponse(data={"state": "unknown", "device_id": device_id})

    engine = CallDetectionEngine(adb_engine, event_bus)
    state = engine.get_call_state(device.serial_number)
    active_call = engine.get_active_call(device.serial_number)
    return SuccessResponse(
        data={
            "device_id": device_id,
            "serial": device.serial_number,
            "call_state": state,
            "active_call": active_call,
        }
    )


@router.post("/{device_id}/auto-answer", response_model=SuccessResponse[dict])
async def auto_answer_call(
    device_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_role("admin")),
) -> SuccessResponse[dict]:
    from app.services.adb_watcher import adb_engine
    from app.services.call_detector.auto_answer import AutoAnswerService
    from app.services.event_bus import event_bus

    service = DeviceService(db)
    device = service.get_device(device_id)
    if not device.serial_number:
        return SuccessResponse(
            success=False,
            message="Device has no serial number",
            data={},
        )

    answer_service = AutoAnswerService(adb_engine, event_bus)
    result = await answer_service.attempt_answer(device.serial_number)
    return SuccessResponse(
        message="Auto-answer attempted" if result["success"] else "Auto-answer failed",
        data=result,
    )


@router.get("/{device_id}/adb-status", response_model=SuccessResponse[dict])
async def get_adb_status(
    device_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    service = DeviceService(db)
    device = service.get_device(device_id)
    if not device.serial_number:
        return SuccessResponse(data={"status": "unknown"})

    is_online = await adb_engine.is_online(device.serial_number)
    return SuccessResponse(
        data={
            "device_id": device_id,
            "serial": device.serial_number,
            "is_online": is_online,
            "server_running": adb_engine.is_server_running,
        }
    )


@router.post("/{device_id}/refresh", response_model=SuccessResponse[DeviceRead])
async def refresh_device(
    device_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[DeviceRead]:
    service = DeviceService(db)
    device = service.get_device(device_id)
    if not device.serial_number:
        return SuccessResponse(
            success=False,
            message="Device has no serial number",
            data=device,
        )

    try:
        info = await adb_engine.get_device_info(device.serial_number)
        from app.repositories.device_repository import DeviceRepository
        repo = DeviceRepository(db)
        from datetime import UTC, datetime
        now = datetime.now(UTC)
        is_online = info.state == "device"
        repo.update(
            device_id,
            is_connected=is_online,
            status="connected" if is_online else "disconnected",
            manufacturer=info.manufacturer or device.manufacturer,
            model=info.model or device.model,
            android_version=info.android_version or device.android_version,
            battery_level=info.battery_level if info.battery_level >= 0 else device.battery_level,
            charging=info.charging if info.charging is not None else device.charging,
            screen_state=info.screen_state if info.screen_state != "unknown" else device.screen_state,
            device_ip=info.device_ip or device.device_ip,
            last_seen=now,
            heartbeat_at=now,
            adb_status=info.state,
        )
        updated = service.get_device(device_id)
        return SuccessResponse(message="Device refreshed", data=updated)
    except Exception as e:
        return SuccessResponse(
            success=False,
            message=f"Failed to refresh device: {str(e)}",
            data=device,
        )


@router.post("/{device_id}/reconnect", response_model=SuccessResponse[dict])
async def reconnect_device(
    device_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    service = DeviceService(db)
    device = service.get_device(device_id)
    if not device.serial_number:
        return SuccessResponse(
            success=False,
            message="Device has no serial number",
            data={},
        )

    try:
        is_online = await adb_engine.wait_for_device(device.serial_number, timeout=10)
        if is_online:
            info = await adb_engine.get_device_info(device.serial_number)
            from app.repositories.device_repository import DeviceRepository
            repo = DeviceRepository(db)
            from datetime import UTC, datetime
            now = datetime.now(UTC)
            repo.update(
                device_id,
                is_connected=True,
                status="connected",
                manufacturer=info.manufacturer or device.manufacturer,
                model=info.model or device.model,
                android_version=info.android_version or device.android_version,
                battery_level=info.battery_level if info.battery_level >= 0 else device.battery_level,
                charging=info.charging if info.charging is not None else device.charging,
                screen_state=info.screen_state if info.screen_state != "unknown" else device.screen_state,
                device_ip=info.device_ip or device.device_ip,
                last_seen=now,
                heartbeat_at=now,
                adb_status="device",
            )
            return SuccessResponse(
                message="Device reconnected successfully",
                data={"device_id": device_id, "is_online": True},
            )
        else:
            return SuccessResponse(
                success=False,
                message="Device is not responding. Check USB connection and USB debugging.",
                data={"device_id": device_id, "is_online": False},
            )
    except Exception as e:
        return SuccessResponse(
            success=False,
            message=f"Reconnect failed: {str(e)}",
            data={"device_id": device_id, "is_online": False},
        )


@router.post("/{device_id}/diagnostics", response_model=SuccessResponse[dict])
async def run_diagnostics(
    device_id: int,
    db: Session = Depends(get_db),
    _: int = Depends(get_current_user_id),
) -> SuccessResponse[dict]:
    service = DeviceService(db)
    device = service.get_device(device_id)
    if not device.serial_number:
        return SuccessResponse(
            success=False,
            message="Device has no serial number",
            data={},
        )

    serial = device.serial_number
    diagnostics: dict[str, object] = {
        "device_id": device_id,
        "serial": serial,
    }

    try:
        is_online = await adb_engine.is_online(serial)
        diagnostics["adb_online"] = is_online
    except Exception as e:
        diagnostics["adb_online"] = False
        diagnostics["adb_error"] = str(e)

    try:
        info = await adb_engine.get_device_info(serial)
        diagnostics["manufacturer"] = info.manufacturer
        diagnostics["model"] = info.model
        diagnostics["android_version"] = info.android_version
        diagnostics["battery_level"] = info.battery_level
        diagnostics["charging"] = info.charging
        diagnostics["screen_state"] = info.screen_state
        diagnostics["usb_connected"] = info.usb_connected
        diagnostics["device_ip"] = info.device_ip
        diagnostics["adb_state"] = info.state
    except Exception as e:
        diagnostics["info_error"] = str(e)

    try:
        from app.services.call_detector import CallDetectionEngine
        engine = CallDetectionEngine(adb_engine, event_bus)
        call_state = engine.get_call_state(serial)
        diagnostics["call_state"] = call_state
    except Exception as e:
        diagnostics["call_state_error"] = str(e)

    return SuccessResponse(
        message="Diagnostics completed",
        data=diagnostics,
    )
