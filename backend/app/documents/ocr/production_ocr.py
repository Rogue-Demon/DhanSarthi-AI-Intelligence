"""
Production OCR provider interface stub.
Designed for cloud-native deployment (Google Document AI / AWS Textract / Azure Form Recognizer).
"""

from __future__ import annotations

import logging
from app.documents.ocr.base import BaseOCRProvider, OCRResult, OCRPageResult

logger = logging.getLogger(__name__)


class ProductionOCRProvider(BaseOCRProvider):
    """
    Production cloud OCR provider interface.
    Activated when DOCUMENT_AI_PROVIDER=production.
    """

    def __init__(self, api_key: str | None = None, endpoint: str | None = None) -> None:
        self.api_key = api_key
        self.endpoint = endpoint

    def process_image(self, image_bytes: bytes) -> OCRResult:
        """Production OCR processing stub."""
        logger.info("Production OCR provider invoked for image document")
        # Interface hook for production OCR SDK integration
        return OCRResult(
            pages=[OCRPageResult(page_number=1, raw_text="", confidence=0.0)],
            raw_text="",
            average_confidence=0.0,
            provider_name="production"
        )

    def process_pdf(self, pdf_bytes: bytes) -> OCRResult:
        """Production OCR processing stub for PDFs."""
        logger.info("Production OCR provider invoked for PDF document")
        return OCRResult(
            pages=[OCRPageResult(page_number=1, raw_text="", confidence=0.0)],
            raw_text="",
            average_confidence=0.0,
            provider_name="production"
        )
