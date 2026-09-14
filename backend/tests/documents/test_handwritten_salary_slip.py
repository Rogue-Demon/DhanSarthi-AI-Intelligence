"""
End-to-End Handwritten Salary Slip OCR & Financial Document Intelligence Test.

Validates OCR processing, document classification, field extraction, field-level confidence,
user review candidates, and database import for handwritten salary slips.
"""

from __future__ import annotations

import io
import datetime
from decimal import Decimal
import pytest
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.models.enums import DocumentType, DocumentStatus, Persona, RiskProfile
from app.models.user import User
from app.models.profile import Profile
from app.documents.extraction.image_extractor import ImageDocumentExtractor
from app.documents.classifier import DocumentClassifier
from app.documents.financial_extractor import FinancialDocumentExtractor
from app.services.document_service import DocumentService
from app.services.document_import_service import FinancialDocumentImportService
from app.schemas.document import ConfirmationRequest, IncomeCandidateSchema
from app.models.income import Income


def _seed_user(db: Session, user_id: int) -> User:
    u = User(id=user_id, email=f"slip_{user_id}@test.com", password_hash="hash")
    db.add(u)
    db.add(
        Profile(
            user_id=user_id,
            display_name=f"Salary Slip User {user_id}",
            persona=Persona.PROFESSIONAL,
            country="IN",
            currency="INR",
            risk_profile=RiskProfile.MODERATE,
        )
    )
    db.flush()
    return u


def create_handwritten_salary_slip_image() -> bytes:
    """
    Render a handwritten-style financial salary slip document image in memory.
    Contains:
      Date: 15/09/2026
      Company: DhanSarthi
      Employee ID: 57-5
      Employee Name: Md Aadil Ansari
      Salary: ₹50,000
    """
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    lines = [
        "Document Type: Salary Slip",
        "Date: 15/09/2026",
        "Company: DhanSarthi",
        "Employee ID: 57-5",
        "Employee Name: Md Aadil Ansari",
        "Salary: ₹50,000",
    ]

    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font = ImageFont.load_default()

    y = 50
    for line in lines:
        draw.text((60, y), line, fill=(20, 20, 20), font=font)
        y += 60

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.anyio
async def test_handwritten_salary_slip_end_to_end(db_session: Session):
    """
    Process handwritten salary slip through full document pipeline.
    """
    user = _seed_user(db_session, 9999)
    img_bytes = create_handwritten_salary_slip_image()

    # 1. OCR Extraction
    extractor = ImageDocumentExtractor()
    ocr_out = extractor.extract(img_bytes)

    assert ocr_out.raw_text != ""
    assert "Salary Slip" in ocr_out.raw_text or "DhanSarthi" in ocr_out.raw_text or "50,000" in ocr_out.raw_text

    # 2. Document Classification
    classifier = DocumentClassifier()
    class_res = classifier.classify(ocr_out.raw_text)

    assert class_res.document_type == DocumentType.SALARY_SLIP
    assert class_res.confidence > 0.0

    # 3. Information Field Extraction
    field_extractor = FinancialDocumentExtractor()
    info_res = field_extractor.extract_info(DocumentType.SALARY_SLIP, ocr_out)

    field_map = {f.name: f for f in info_res.fields}

    # Verify extracted fields
    salary_field = field_map.get("salary") or field_map.get("net_salary")
    assert salary_field is not None
    assert salary_field.value in (Decimal("50000.00"), Decimal("50000"))
    assert salary_field.confidence > 0.5

    if "employer" in field_map:
        assert "DhanSarthi" in str(field_map["employer"].value)

    if "employee_id" in field_map:
        assert "57-5" in str(field_map["employee_id"].value)

    if "employee_name" in field_map:
        assert "Md Aadil Ansari" in str(field_map["employee_name"].value)

    if "date" in field_map:
        assert field_map["date"].value == datetime.date(2026, 9, 15)

    # 4. Service Pipeline Test
    doc_service = DocumentService(db_session)
    doc = await doc_service.upload_document(
        user_id=user.id,
        filename="handwritten_salary_slip.png",
        content_type="image/png",
        data=img_bytes
    )

    extraction = await doc_service.process_document(doc.id, user.id)
    assert extraction.document_type == DocumentType.SALARY_SLIP
    assert doc.status in (DocumentStatus.EXTRACTED, DocumentStatus.REVIEW_REQUIRED)

    # 5. Confirmation & Import to Income Table
    import_service = FinancialDocumentImportService(db_session)
    confirm_req = ConfirmationRequest(
        confirmed_income=[
            IncomeCandidateSchema(
                candidate_id="salary",
                source="DhanSarthi",
                amount=Decimal("50000.00"),
                income_date=datetime.date(2026, 9, 15),
                category="Salary",
                description="Imported Handwritten Salary Slip"
            )
        ]
    )

    res = import_service.confirm_and_import(
        document_id=doc.id,
        user_id=user.id,
        req=confirm_req
    )

    assert res.imported_income_count == 1

    # 6. Verify Database Persistence
    inc_record = (
        db_session.query(Income)
        .filter(Income.user_id == user.id, Income.amount == Decimal("50000.00"))
        .first()
    )
    assert inc_record is not None
    assert inc_record.source == "DhanSarthi"
    assert inc_record.income_date == datetime.date(2026, 9, 15)
