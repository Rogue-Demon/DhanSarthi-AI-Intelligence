"""
OCR provider factory. Instantiates concrete provider based on application configuration.
"""

from __future__ import annotations

from app.core.config import settings
from app.documents.ocr.base import BaseOCRProvider
from app.documents.ocr.local_ocr import LocalOCRProvider
from app.documents.ocr.production_ocr import ProductionOCRProvider


def get_ocr_provider() -> BaseOCRProvider:
    """
    Return the configured OCR provider instance.

    Reads settings.document_ai_provider ("local" or "production").
    """
    provider_type = (settings.document_ai_provider or "local").lower().strip()

    if provider_type == "production":
        return ProductionOCRProvider(
            api_key=settings.ai_provider_api_key
        )
    return LocalOCRProvider()
