"""
Base interfaces and data containers for DhanSarthi OCR providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field


class OCRWord(BaseModel):
    """Extracted text word with bounding box and confidence score."""
    text: str
    confidence: float
    box: Optional[List[int]] = None  # [x1, y1, x2, y2]


class OCRPageResult(BaseModel):
    """OCR processing result for a single document page."""
    page_number: int
    raw_text: str
    confidence: float
    words: List[OCRWord] = Field(default_factory=list)


class OCRResult(BaseModel):
    """Complete multi-page OCR processing result."""
    pages: List[OCRPageResult] = Field(default_factory=list)
    raw_text: str = ""
    average_confidence: float = 0.0
    provider_name: str = "local"


class BaseOCRProvider(ABC):
    """Abstract base class for OCR document intelligence providers."""

    @abstractmethod
    def process_image(self, image_bytes: bytes) -> OCRResult:
        """Extract text and metadata from image bytes (PNG, JPEG, WEBP)."""
        pass

    @abstractmethod
    def process_pdf(self, pdf_bytes: bytes) -> OCRResult:
        """Extract text and metadata from multi-page PDF document bytes."""
        pass
