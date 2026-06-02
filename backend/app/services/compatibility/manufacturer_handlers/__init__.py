from app.services.compatibility.manufacturer_handlers.manufacturer_handler import ManufacturerHandler
from app.services.compatibility.manufacturer_handlers.samsung_handler import SamsungHandler
from app.services.compatibility.manufacturer_handlers.xiaomi_handler import XiaomiHandler
from app.services.compatibility.manufacturer_handlers.oneplus_handler import OnePlusHandler
from app.services.compatibility.manufacturer_handlers.pixel_handler import PixelHandler
from app.services.compatibility.manufacturer_handlers.motorola_handler import MotorolaHandler
from app.services.compatibility.manufacturer_handlers.oppo_handler import OppoHandler
from app.services.compatibility.manufacturer_handlers.vivo_handler import VivoHandler
from app.services.compatibility.manufacturer_handlers.realme_handler import RealmeHandler
from app.services.compatibility.manufacturer_handlers.generic_handler import GenericAndroidHandler
from app.services.compatibility.manufacturer_handlers.handler_registry import HandlerRegistry

__all__ = [
    "ManufacturerHandler",
    "SamsungHandler", "XiaomiHandler", "OnePlusHandler", "PixelHandler",
    "MotorolaHandler", "OppoHandler", "VivoHandler", "RealmeHandler", "GenericAndroidHandler",
    "HandlerRegistry",
]
