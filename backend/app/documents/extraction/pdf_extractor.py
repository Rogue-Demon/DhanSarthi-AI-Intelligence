"""
PDF text extractor implementation using pypdf.
"""

from __future__ import annotations

import io
from pypdf import PdfReader
from app.documents.extraction.base import DocumentTextExtractor, ExtractionOutput, PageContent
from app.documents.exceptions import ExtractionFailedError
from app.documents.ocr import get_ocr_provider


class PDFDocumentExtractor(DocumentTextExtractor):
    """Parses text and basic page structure from machine-readable and scanned PDFs."""

    def extract(self, data: bytes) -> ExtractionOutput:
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = []
            full_text_parts = []
            ocr_required = True

            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                cleaned_text = text.strip()
                if cleaned_text:
                    ocr_required = False

                pages.append(
                    PageContent(
                        page_number=idx,
                        text=cleaned_text,
                        tables=[]
                    )
                )
                full_text_parts.append(cleaned_text)

            if not pages:
                raise ExtractionFailedError("PDF contains no readable pages.")

            # If all pages yield no direct text, run OCR provider
            if ocr_required:
                provider = get_ocr_provider()
                ocr_res = provider.process_pdf(data)
                if ocr_res.raw_text and ocr_res.raw_text.strip():
                    pages = [
                        PageContent(
                            page_number=p.page_number,
                            text=p.raw_text,
                            tables=[]
                        )
                        for p in ocr_res.pages
                    ]
                    full_text_parts = [p.raw_text for p in ocr_res.pages]
                    ocr_required = False

            return ExtractionOutput(
                pages=pages,
                raw_text="\n--- PAGE BREAK ---\n".join(full_text_parts),
                page_count=len(pages),
                ocr_required=ocr_required
            )
        except Exception as exc:
            if isinstance(exc, ExtractionFailedError):
                raise
            raise ExtractionFailedError(f"Failed to parse PDF document: {str(exc)}") from exc

