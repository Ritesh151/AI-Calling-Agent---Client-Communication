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


async def _sync_devices_live(db: Session) -> None:
    """ADB is the source of truth — reconcile DB before serving device lists."""
    await device_sync_service.sync(db)


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
    sync: bool = Query(True, description="Reconcile with ADB before returning"),
    adb_present_only: bool = Query(
        True,
        description="Only return devices currently visible to ADB as connected",
    ),
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
    devices = service.get_all_devices(skip=skip, limit=limit)
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
