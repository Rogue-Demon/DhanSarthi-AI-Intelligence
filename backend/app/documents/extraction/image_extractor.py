"""
Image document extractor backed by DhanSarthi OCR provider interface.
Processes uploaded PNG, JPEG, WEBP images for financial text extraction.
"""

from __future__ import annotations

from app.documents.extraction.base import DocumentTextExtractor, ExtractionOutput, PageContent
from app.documents.ocr import get_ocr_provider


class ImageDocumentExtractor(DocumentTextExtractor):
    """Image document extractor integrating live OCR engine."""

    def extract(self, data: bytes) -> ExtractionOutput:
        provider = get_ocr_provider()
        ocr_res = provider.process_image(data)

        pages = [
            PageContent(
                page_number=p.page_number,
                text=p.raw_text,
                tables=[]
            )
            for p in ocr_res.pages
        ]

        ocr_required = not bool(ocr_res.raw_text and ocr_res.raw_text.strip())

        return ExtractionOutput(
            pages=pages,
            raw_text=ocr_res.raw_text,
            page_count=len(pages) or 1,
            ocr_required=ocr_required
        )
