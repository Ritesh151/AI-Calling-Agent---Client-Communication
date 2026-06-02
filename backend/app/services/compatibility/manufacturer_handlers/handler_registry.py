from __future__ import annotations

import logging
from typing import Any

from app.services.compatibility.manufacturer_handlers.generic_handler import (
    GenericAndroidHandler,
)
from app.services.compatibility.manufacturer_handlers.manufacturer_handler import (
    ManufacturerHandler,
)
from app.services.compatibility.manufacturer_handlers.motorola_handler import MotorolaHandler
from app.services.compatibility.manufacturer_handlers.oneplus_handler import OnePlusHandler
from app.services.compatibility.manufacturer_handlers.oppo_handler import OppoHandler
from app.services.compatibility.manufacturer_handlers.pixel_handler import PixelHandler
from app.services.compatibility.manufacturer_handlers.realme_handler import RealmeHandler
from app.services.compatibility.manufacturer_handlers.samsung_handler import SamsungHandler
from app.services.compatibility.manufacturer_handlers.vivo_handler import VivoHandler
from app.services.compatibility.manufacturer_handlers.xiaomi_handler import XiaomiHandler

logger = logging.getLogger(__name__)


class HandlerRegistry:
    _handlers: dict[str, type[ManufacturerHandler]] = {
        "samsung": SamsungHandler,
        "xiaomi": XiaomiHandler,
        "oneplus": OnePlusHandler,
        "google": PixelHandler,
        "pixel": PixelHandler,
        "motorola": MotorolaHandler,
        "oppo": OppoHandler,
        "vivo": VivoHandler,
        "realme": RealmeHandler,
    }

    _instances: dict[str, ManufacturerHandler] = {}

    @classmethod
    def get_handler(cls, manufacturer: str) -> ManufacturerHandler:
        key = manufacturer.lower().strip()
        handler_cls = cls._handlers.get(key, GenericAndroidHandler)
        if key not in cls._instances:
            cls._instances[key] = handler_cls()
        return cls._instances[key]

    @classmethod
    def resolve_for_device(cls, device_id: str, manufacturer: str) -> ManufacturerHandler:
        handler = cls.get_handler(manufacturer)
        logger.info("Resolved handler %s for device %s (%s)", handler.manufacturer_name, device_id, manufacturer)
        return handler

    @classmethod
    def get_available_handlers(cls) -> list[str]:
        return list(cls._handlers.keys())
