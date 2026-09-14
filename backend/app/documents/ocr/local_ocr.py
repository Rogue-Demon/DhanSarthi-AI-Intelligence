"""
Local OCR provider implementation using RapidOCR / Pillow preprocessing.
Supports handwritten and printed financial documents.
"""

from __future__ import annotations

import io
import logging
from typing import List
from PIL import Image, ImageEnhance, ImageFilter

from app.documents.ocr.base import BaseOCRProvider, OCRResult, OCRPageResult, OCRWord

logger = logging.getLogger(__name__)

# Lazy initialization of RapidOCR engine
_rapid_ocr_engine = None

def _get_rapid_ocr():
    global _rapid_ocr_engine
    if _rapid_ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapid_ocr_engine = RapidOCR()
        except Exception as e:
            logger.warning(f"Could not initialize RapidOCR engine: {e}")
            _rapid_ocr_engine = False
    return _rapid_ocr_engine if _rapid_ocr_engine is not False else None


class LocalOCRProvider(BaseOCRProvider):
    """
    Local zero-cost OCR provider.
    Combines PIL image preprocessing (contrast enhancement, sharpening) with RapidOCR/Tesseract.
    """

    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """
        Enhance document image for better handwritten and low-contrast OCR reading.
        """
        # Convert to RGB if needed
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Increase contrast and sharpness slightly for handwritten text clarity
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.4)
        
        sharpener = ImageEnhance.Sharpness(img)
        img = sharpener.enhance(1.3)

        return img

    def process_image(self, image_bytes: bytes) -> OCRResult:
        """Process image file bytes through local OCR pipeline."""
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
        except Exception as exc:
            logger.error(f"Failed to open image for OCR: {exc}")
            return OCRResult(
                pages=[OCRPageResult(page_number=1, raw_text="", confidence=0.0)],
                raw_text="",
                average_confidence=0.0,
                provider_name="local"
            )

        preprocessed = self._preprocess_image(pil_img)
        
        # Save preprocessed image to memory buffer for OCR engine
        buf = io.BytesIO()
        preprocessed.save(buf, format="PNG")
        prep_bytes = buf.getvalue()

        ocr_engine = _get_rapid_ocr()
        lines: List[str] = []
        words: List[OCRWord] = []
        confidences: List[float] = []

        if ocr_engine:
            try:
                # RapidOCR accepts numpy array or bytes
                import numpy as np
                img_np = np.array(preprocessed)
                results, _ = ocr_engine(img_np)
                
                if results:
                    for res in results:
                        # res is typically [dt_boxes, text, score]
                        if len(res) >= 3:
                            box, text, score = res[0], res[1], float(res[2])
                            text = text.strip()
                            if text:
                                lines.append(text)
                                confidences.append(score)
                                words.append(
                                    OCRWord(
                                        text=text,
                                        confidence=round(score, 4)
                                    )
                                )
            except Exception as e:
                logger.error(f"RapidOCR execution failed: {e}")

        # Fallback to pytesseract if RapidOCR produced nothing or is missing
        if not lines:
            try:
                import pytesseract
                text = pytesseract.image_to_string(preprocessed)
                if text and text.strip():
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    confidences = [0.85] * len(lines)
            except Exception:
                pass

        raw_text = "\n".join(lines)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        page_result = OCRPageResult(
            page_number=1,
            raw_text=raw_text,
            confidence=round(avg_conf, 4),
            words=words
        )

        return OCRResult(
            pages=[page_result],
            raw_text=raw_text,
            average_confidence=round(avg_conf, 4),
            provider_name="local"
        )

    def process_pdf(self, pdf_bytes: bytes) -> OCRResult:
        """Extract text from PDF pages, rendering embedded images to OCR if necessary."""
        pages_results: List[OCRPageResult] = []
        full_text_parts: List[str] = []
        total_conf = 0.0

        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for i, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                words: List[OCRWord] = []
                page_conf = 0.95

                if not text and hasattr(page, "images") and page.images:
                    img_texts = []
                    img_confs = []
                    for img_obj in page.images:
                        try:
                            sub_res = self.process_image(img_obj.data)
                            if sub_res.raw_text:
                                img_texts.append(sub_res.raw_text)
                                img_confs.append(sub_res.average_confidence)
                                for p in sub_res.pages:
                                    words.extend(p.words)
                        except Exception as img_err:
                            logger.warning(f"Failed to run OCR on PDF page image: {img_err}")
                    
                    if img_texts:
                        text = "\n".join(img_texts)
                        page_conf = sum(img_confs) / len(img_confs) if img_confs else 0.8

                if text:
                    full_text_parts.append(text)
                    pages_results.append(
                        OCRPageResult(
                            page_number=i,
                            raw_text=text,
                            confidence=round(page_conf, 4),
                            words=words
                        )
                    )
                    total_conf += page_conf
        except Exception as e:
            logger.warning(f"PDF direct text extraction failed: {e}")

        raw_text = "\n\n".join(full_text_parts)
        avg_conf = total_conf / len(pages_results) if pages_results else 0.0

        return OCRResult(
            pages=pages_results,
            raw_text=raw_text,
            average_confidence=round(avg_conf, 4),
            provider_name="local"
        )

