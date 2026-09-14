"""
DhanSarthi OCR module exports.
"""

from app.documents.ocr.base import BaseOCRProvider, OCRResult, OCRPageResult, OCRWord
from app.documents.ocr.factory import get_ocr_provider
from app.documents.ocr.local_ocr import LocalOCRProvider
from app.documents.ocr.production_ocr import ProductionOCRProvider

__all__ = [
    "BaseOCRProvider",
    "OCRResult",
    "OCRPageResult",
    "OCRWord",
    "get_ocr_provider",
    "LocalOCRProvider",
    "ProductionOCRProvider",
]
