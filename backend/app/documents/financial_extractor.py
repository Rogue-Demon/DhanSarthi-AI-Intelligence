"""
Financial Document Information Extractor.

Extracts structured, typed fields and transactions based on classified document type.
Uses robust regex, text parsing, and table-parsing logic with field-level confidence scoring.
"""

from __future__ import annotations

import re
import uuid
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.models.enums import DocumentType
from app.documents.extraction.base import ExtractionOutput


class ExtractedField(BaseModel):
    """A single extracted metadata field with confidence and source context."""

    name: str
    value: Any  # Decimal, date, str
    confidence: float
    source_page: int = 1
    source_text_ref: str = ""
    inferred: bool = False


class TransactionCandidate(BaseModel):
    """A single transaction row candidate extracted from a statement or bill."""

    candidate_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    date: str
    description: str
    debit: Optional[str] = None
    credit: Optional[str] = None
    balance: Optional[str] = None
    currency: str = "INR"
    source_page: int = 1
    source_row: int = 0
    confidence: float = 1.0


class FinancialExtractionResult(BaseModel):
    """The complete set of extracted fields and transactions from a document."""

    document_type: DocumentType
    fields: List[ExtractedField] = Field(default_factory=list)
    transactions: List[TransactionCandidate] = Field(default_factory=list)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    raw_page_count: int = 1


class FinancialDocumentExtractor:
    """Extracts structured fields and transactions from parsed document contents."""

    def __init__(self) -> None:
        # Currency amount regex matching ₹, Rs, INR, USD, $
        self._amount_pattern = re.compile(r"(?:rs\.?|inr|usd|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", re.IGNORECASE)
        # Date pattern regex matching DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY, DD.MM.YYYY
        self._date_pattern = re.compile(r"\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})\b")

    def extract_info(
        self, doc_type: DocumentType, extraction: ExtractionOutput
    ) -> FinancialExtractionResult:
        """Main dispatch method for extracting financial information."""
        result = FinancialExtractionResult(
            document_type=doc_type,
            raw_page_count=extraction.page_count
        )

        if doc_type == DocumentType.BANK_STATEMENT:
            self._extract_bank_statement(extraction, result)
        elif doc_type == DocumentType.SALARY_SLIP:
            self._extract_salary_slip(extraction, result)
        elif doc_type == DocumentType.LOAN_STATEMENT:
            self._extract_loan_statement(extraction, result)
        elif doc_type == DocumentType.INVESTMENT_STATEMENT:
            self._extract_investment_statement(extraction, result)
        elif doc_type == DocumentType.BILL or doc_type == DocumentType.EXPENSE_RECEIPT:
            self._extract_bill_receipt(extraction, result)
        elif doc_type == DocumentType.INVOICE:
            self._extract_invoice(extraction, result)
        elif doc_type == DocumentType.TAX_DOCUMENT:
            self._extract_tax_document(extraction, result)
        elif doc_type == DocumentType.INSURANCE_DOCUMENT:
            self._extract_insurance_document(extraction, result)
        elif doc_type == DocumentType.BUSINESS_FINANCIAL_DOCUMENT:
            self._extract_business_document(extraction, result)
        else:
            self._extract_generic(extraction, result)

        for f in result.fields:
            if f.name in ("period_start", "date", "document_date") and isinstance(f.value, date):
                if not result.period_start:
                    result.period_start = f.value
            elif f.name == "period_end" and isinstance(f.value, date):
                result.period_end = f.value

        return result

    # ------------------------------------------------------------------
    # Extractor implementations
    # ------------------------------------------------------------------

    def _extract_salary_slip(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        # 1. Date (e.g. Date: 15/09/2026)
        date_match = re.search(r"(?:date|payslip\s*date|issue\s*date|pay\s*date)\s*[:\-]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})", text, re.IGNORECASE)
        if date_match:
            d_val = self._parse_date_stub(date_match.group(1))
            if d_val:
                res.fields.append(
                    ExtractedField(
                        name="date",
                        value=d_val,
                        confidence=0.95,
                        source_text_ref=date_match.group(0).strip()
                    )
                )

        # 2. Company Name / Employer (e.g. Company: DhanSarthi)
        comp_match = re.search(r"(?:company\s*name|company|employer|organization)\s*[:\-]?\s*([a-zA-Z0-9\s,\-\.]+)", text, re.IGNORECASE)
        if comp_match:
            res.fields.append(
                ExtractedField(
                    name="employer",
                    value=comp_match.group(1).strip(),
                    confidence=0.92,
                    source_text_ref=comp_match.group(0).strip()
                )
            )

        # 3. Employee ID (e.g. Employee ID: 57-5)
        emp_id_match = re.search(r"(?:employee\s*id|emp\s*id|emp\s*code|staff\s*id)\s*[:\-]?\s*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
        if emp_id_match:
            res.fields.append(
                ExtractedField(
                    name="employee_id",
                    value=emp_id_match.group(1).strip(),
                    confidence=0.94,
                    source_text_ref=emp_id_match.group(0).strip()
                )
            )

        # 4. Employee Name (e.g. Employee Name: Md Aadil Ansari)
        emp_name_match = re.search(r"(?:employee\s*name|emp\s*name)\s*[:\-]?\s*([a-zA-Z0-9\s\.\-]+)", text, re.IGNORECASE)
        if emp_name_match:
            res.fields.append(
                ExtractedField(
                    name="employee_name",
                    value=emp_name_match.group(1).strip(),
                    confidence=0.93,
                    source_text_ref=emp_name_match.group(0).strip()
                )
            )

        # 5. Salary Field Matching (semantic binding to 'salary', 'net salary', 'gross salary', 'basic salary')
        net_match = re.search(r"\bnet\s*(?:salary|pay|take-home|take\s*home)\b[^\d\n]*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if net_match:
            res.fields.append(
                ExtractedField(
                    name="net_salary",
                    value=self._parse_decimal_stub(net_match.group(1)),
                    confidence=0.96,
                    source_text_ref=net_match.group(0).strip()
                )
            )

        gross_match = re.search(r"\bgross\s*(?:salary|pay|earnings)\b[^\d\n]*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if gross_match:
            res.fields.append(
                ExtractedField(
                    name="gross_salary",
                    value=self._parse_decimal_stub(gross_match.group(1)),
                    confidence=0.95,
                    source_text_ref=gross_match.group(0).strip()
                )
            )

        basic_match = re.search(r"\bbasic\s*(?:salary|pay)\b[^\d\n]*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if basic_match:
            res.fields.append(
                ExtractedField(
                    name="basic_salary",
                    value=self._parse_decimal_stub(basic_match.group(1)),
                    confidence=0.95,
                    source_text_ref=basic_match.group(0).strip()
                )
            )

        # Total Deductions
        ded_match = re.search(r"(?:total\s*deductions?|deductions?)\s*[:\-]?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if ded_match:
            res.fields.append(
                ExtractedField(
                    name="total_deductions",
                    value=self._parse_decimal_stub(ded_match.group(1)),
                    confidence=0.92,
                    source_text_ref=ded_match.group(0).strip()
                )
            )

        # Salary Period
        period_match = re.search(r"(?:salary\s*period|pay\s*period|pay\s*month)\s*[:\-]?\s*([a-zA-Z0-9\s]+)", text, re.IGNORECASE)
        if period_match:
            res.fields.append(
                ExtractedField(
                    name="salary_period",
                    value=period_match.group(1).strip(),
                    confidence=0.90,
                    source_text_ref=period_match.group(0).strip()
                )
            )

        # Generic Salary label match (only if net/gross/basic not matched or standalone "salary:" line)
        salary_label_match = re.search(r"\bsalary\b[^\d\n]*?(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if salary_label_match:
            ref_snippet = salary_label_match.group(0).strip()
            salary_val = self._parse_decimal_stub(salary_label_match.group(1))
            res.fields.append(
                ExtractedField(
                    name="salary",
                    value=salary_val,
                    confidence=0.95,
                    source_text_ref=ref_snippet
                )
            )
            if not net_match:
                res.fields.append(
                    ExtractedField(
                        name="net_salary",
                        value=salary_val,
                        confidence=0.90,
                        source_text_ref=ref_snippet,
                        inferred=True
                    )
                )


    def _extract_bill_receipt(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        # Biller / Merchant
        vendor_match = re.search(r"(?:biller|merchant|vendor|company|store|provider|biller\s*name)\s*[:\-]?\s*([a-zA-Z0-9\s,\-\.]+)", text, re.IGNORECASE)
        if vendor_match:
            res.fields.append(
                ExtractedField(
                    name="vendor",
                    value=vendor_match.group(1).strip(),
                    confidence=0.88,
                    source_text_ref=vendor_match.group(0).strip()
                )
            )

        # Bill Number
        bill_num = re.search(r"(?:bill\s*(?:no\.?|number)|receipt\s*(?:no\.?|number))\s*[:\-]?\s*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
        if bill_num:
            res.fields.append(
                ExtractedField(
                    name="bill_number",
                    value=bill_num.group(1).strip(),
                    confidence=0.92,
                    source_text_ref=bill_num.group(0).strip()
                )
            )

        # Total Amount (Semantic match only)
        tot_match = re.search(r"(?:total\s*amount|total\s*payable|amount\s*due|bill\s*amount|total)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if tot_match:
            res.fields.append(
                ExtractedField(
                    name="total_amount",
                    value=self._parse_decimal_stub(tot_match.group(1)),
                    confidence=0.95,
                    source_text_ref=tot_match.group(0).strip()
                )
            )

        # Bill / Receipt Date
        date_match = re.search(r"(?:bill\s*date|receipt\s*date|date)\s*[:\-]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})", text, re.IGNORECASE)
        if date_match:
            d_val = self._parse_date_stub(date_match.group(1))
            if d_val:
                res.fields.append(ExtractedField(name="bill_date", value=d_val, confidence=0.92, source_text_ref=date_match.group(0).strip()))

    def _extract_invoice(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        # Invoice number
        inv_num = re.search(r"(?:invoice\s*(?:no\.?|number))\s*[:\-]?\s*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
        if inv_num:
            res.fields.append(ExtractedField(name="invoice_number", value=inv_num.group(1).strip(), confidence=0.94, source_text_ref=inv_num.group(0).strip()))

        # Total amount
        tot_match = re.search(r"(?:invoice\s*total|total\s*amount|grand\s*total|total)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if tot_match:
            res.fields.append(ExtractedField(name="total_amount", value=self._parse_decimal_stub(tot_match.group(1)), confidence=0.95, source_text_ref=tot_match.group(0).strip()))

        # Seller / Vendor
        seller_match = re.search(r"(?:seller|vendor|issued\s*by|company)\s*[:\-]?\s*([a-zA-Z0-9\s,\-\.]+)", text, re.IGNORECASE)
        if seller_match:
            res.fields.append(ExtractedField(name="vendor", value=seller_match.group(1).strip(), confidence=0.88, source_text_ref=seller_match.group(0).strip()))

    def _extract_tax_document(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        # PAN / Tax ID
        pan_match = re.search(r"(?:pan\s*(?:no\.?|number)?|tax\s*id)\s*[:\-]?\s*([a-zA-Z0-9]{10})", text, re.IGNORECASE)
        if pan_match:
            res.fields.append(ExtractedField(name="tax_id", value=pan_match.group(1).upper(), confidence=0.95, source_text_ref=pan_match.group(0).strip()))

        # Taxable income
        inc_match = re.search(r"(?:taxable\s*income|gross\s*total\s*income|total\s*income)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if inc_match:
            res.fields.append(ExtractedField(name="taxable_income", value=self._parse_decimal_stub(inc_match.group(1)), confidence=0.92, source_text_ref=inc_match.group(0).strip()))

        # Tax paid / TDS
        tax_paid_match = re.search(r"(?:tax\s*paid|tds\s*deducted|total\s*tax\s*paid)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if tax_paid_match:
            res.fields.append(ExtractedField(name="tax_paid", value=self._parse_decimal_stub(tax_paid_match.group(1)), confidence=0.92, source_text_ref=tax_paid_match.group(0).strip()))

    def _extract_bank_statement(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        account_match = re.search(r"account\s*(?:no\.?|number)\s*[:\-]?\s*([a-zA-Z0-9]+)", text, re.IGNORECASE)
        if account_match:
            raw_ac = account_match.group(1)
            masked = f"XXXXXX{raw_ac[-4:]}" if len(raw_ac) >= 4 else raw_ac
            res.fields.append(ExtractedField(name="account_number", value=masked, confidence=0.9, source_text_ref=account_match.group(0).strip()))

        period_match = re.search(r"(?:statement\s*period|period)\s*[:\-]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})\s*(?:to|and|-)\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})", text, re.IGNORECASE)
        if period_match:
            p_start = self._parse_date_stub(period_match.group(1))
            p_end = self._parse_date_stub(period_match.group(2))
            if p_start:
                res.fields.append(ExtractedField(name="period_start", value=p_start, confidence=0.95, source_text_ref=period_match.group(1)))
            if p_end:
                res.fields.append(ExtractedField(name="period_end", value=p_end, confidence=0.95, source_text_ref=period_match.group(2)))

        row_index = 0
        for page in ext.pages:
            if page.tables:
                for table in page.tables:
                    header_idx = -1
                    date_col, desc_col, debit_col, credit_col, bal_col = -1, -1, -1, -1, -1
                    
                    for r_idx, row in enumerate(table):
                        cleaned_row = [c.lower() for c in row]
                        if any(kw in cleaned_row for kw in ["date", "description", "particulars", "debit", "credit", "amount"]):
                            header_idx = r_idx
                            for c_idx, cell in enumerate(cleaned_row):
                                if "date" in cell:
                                    date_col = c_idx
                                elif "desc" in cell or "particulars" in cell or "narration" in cell:
                                    desc_col = c_idx
                                elif "debit" in cell or "withdrawal" in cell:
                                    debit_col = c_idx
                                elif "credit" in cell or "deposit" in cell:
                                    credit_col = c_idx
                                elif "balance" in cell:
                                    bal_col = c_idx
                            break
                    
                    start_row = header_idx + 1 if header_idx != -1 else 0
                    for r_idx in range(start_row, len(table)):
                        row = table[r_idx]
                        if len(row) < 2:
                            continue
                        
                        d_col = date_col if date_col != -1 else 0
                        ds_col = desc_col if desc_col != -1 else (1 if len(row) > 1 else 0)
                        deb_col = debit_col if debit_col != -1 else (2 if len(row) > 2 else -1)
                        cred_col = credit_col if credit_col != -1 else (3 if len(row) > 3 else -1)
                        b_col = bal_col if bal_col != -1 else (4 if len(row) > 4 else -1)

                        t_date = row[d_col]
                        t_desc = row[ds_col]
                        
                        if not self._date_pattern.search(t_date):
                            continue

                        t_debit = row[deb_col] if deb_col != -1 and deb_col < len(row) else None
                        t_credit = row[cred_col] if cred_col != -1 and cred_col < len(row) else None
                        t_balance = row[b_col] if b_col != -1 and b_col < len(row) else None

                        res.transactions.append(
                            TransactionCandidate(
                                date=t_date,
                                description=t_desc,
                                debit=t_debit,
                                credit=t_credit,
                                balance=t_balance,
                                source_page=page.page_number,
                                source_row=row_index,
                                confidence=0.98
                            )
                        )
                        row_index += 1
            else:
                lines = page.text.split("\n")
                for line in lines:
                    line = line.strip()
                    date_match = self._date_pattern.search(line)
                    if date_match:
                        t_date = date_match.group(1)
                        remaining = line.replace(t_date, "").strip()
                        amounts = self._amount_pattern.findall(remaining)
                        if amounts:
                            t_desc = remaining
                            for amt in amounts:
                                t_desc = t_desc.replace(amt, "")
                            t_desc = re.sub(r"rs\.?|inr|usd|[\$₹]", "", t_desc, flags=re.IGNORECASE).strip()
                            t_desc = re.sub(r"\s+", " ", t_desc)

                            amount_val = amounts[0]
                            is_credit = any(kw in remaining.lower() for kw in ["credit", "deposit", "salary", "refund", "interest received"])
                            
                            res.transactions.append(
                                TransactionCandidate(
                                    date=t_date,
                                    description=t_desc or "Transaction",
                                    debit=None if is_credit else amount_val,
                                    credit=amount_val if is_credit else None,
                                    balance=amounts[1] if len(amounts) > 1 else None,
                                    source_page=page.page_number,
                                    source_row=row_index,
                                    confidence=0.85
                                )
                            )
                            row_index += 1

    def _extract_loan_statement(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        loan_ac = re.search(r"loan\s*(?:account|ac)\s*(?:no\.?|number)?\s*[:\-]?\s*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
        if loan_ac:
            raw_ac = loan_ac.group(1)
            masked = f"XXXXXX{raw_ac[-4:]}" if len(raw_ac) >= 4 else raw_ac
            res.fields.append(ExtractedField(name="loan_account_number", value=masked, confidence=0.9, source_text_ref=loan_ac.group(0).strip()))

        pr_amt = re.search(r"(?:principal|loan\s*amount|disbursed\s*amount)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if pr_amt:
            res.fields.append(ExtractedField(name="principal_amount", value=self._parse_decimal_stub(pr_amt.group(1)), confidence=0.95, source_text_ref=pr_amt.group(0).strip()))

        emi_match = re.search(r"(?:emi|monthly\s*installment|installment\s*amount)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if emi_match:
            res.fields.append(ExtractedField(name="emi", value=self._parse_decimal_stub(emi_match.group(1)), confidence=0.95, source_text_ref=emi_match.group(0).strip()))

        rate_match = re.search(r"(?:interest\s*rate|rate\s*of\s*interest|roi)\s*[:\-]?\s*([\d\.]+)%", text, re.IGNORECASE)
        if rate_match:
            res.fields.append(ExtractedField(name="interest_rate", value=self._parse_decimal_stub(rate_match.group(1)), confidence=0.9, source_text_ref=rate_match.group(0).strip()))

        bal_match = re.search(r"(?:outstanding\s*balance|outstanding\s*principal|amount\s*outstanding)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if bal_match:
            res.fields.append(ExtractedField(name="outstanding_balance", value=self._parse_decimal_stub(bal_match.group(1)), confidence=0.95, source_text_ref=bal_match.group(0).strip()))

    def _extract_investment_statement(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        folio_match = re.search(r"folio\s*(?:no\.?|number)\s*[:\-]?\s*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
        if folio_match:
            res.fields.append(ExtractedField(name="folio_number", value=folio_match.group(1).strip(), confidence=0.95, source_text_ref=folio_match.group(0).strip()))

        inv_match = re.search(r"(?:invested\s*amount|cost\s*of\s*investment|amount\s*invested)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if inv_match:
            res.fields.append(ExtractedField(name="invested_amount", value=self._parse_decimal_stub(inv_match.group(1)), confidence=0.95, source_text_ref=inv_match.group(0).strip()))

        val_match = re.search(r"(?:current\s*value|portfolio\s*value|valuation)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if val_match:
            res.fields.append(ExtractedField(name="current_value", value=self._parse_decimal_stub(val_match.group(1)), confidence=0.95, source_text_ref=val_match.group(0).strip()))

        scheme_match = re.search(r"(?:scheme\s*name|fund\s*name)\s*[:\-]?\s*([a-zA-Z0-9\s,\-\(\)]+)", text, re.IGNORECASE)
        if scheme_match:
            res.fields.append(ExtractedField(name="scheme_name", value=scheme_match.group(1).strip(), confidence=0.85, source_text_ref=scheme_match.group(0).strip()))

    def _extract_insurance_document(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        pol_match = re.search(r"policy\s*(?:no\.?|number)\s*[:\-]?\s*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
        if pol_match:
            raw_pol = pol_match.group(1)
            masked = f"XXXXXX{raw_pol[-4:]}" if len(raw_pol) >= 4 else raw_pol
            res.fields.append(ExtractedField(name="policy_number", value=masked, confidence=0.94, source_text_ref=pol_match.group(0).strip()))

        prem_match = re.search(r"(?:premium|premium\s*amount)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if prem_match:
            res.fields.append(ExtractedField(name="premium", value=self._parse_decimal_stub(prem_match.group(1)), confidence=0.95, source_text_ref=prem_match.group(0).strip()))

        sum_match = re.search(r"(?:sum\s*assured|coverage\s*amount)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if sum_match:
            res.fields.append(ExtractedField(name="sum_assured", value=self._parse_decimal_stub(sum_match.group(1)), confidence=0.92, source_text_ref=sum_match.group(0).strip()))

    def _extract_business_document(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        rev_match = re.search(r"(?:revenue|total\s*revenue|sales|turnover)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if rev_match:
            res.fields.append(ExtractedField(name="revenue", value=self._parse_decimal_stub(rev_match.group(1)), confidence=0.92, source_text_ref=rev_match.group(0).strip()))

        exp_match = re.search(r"(?:operating\s*expenses|total\s*expenses|expenses)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if exp_match:
            res.fields.append(ExtractedField(name="total_amount", value=self._parse_decimal_stub(exp_match.group(1)), confidence=0.90, source_text_ref=exp_match.group(0).strip()))

    def _extract_generic(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        """
        Generic extraction for UNKNOWN documents.
        CRITICAL RULE: NEVER extract an un-labeled numeric value as an 'amount' or 'income'.
        Only extract explicit document_date if formatted cleanly as a date.
        """
        text = ext.raw_text
        date_matches = self._date_pattern.findall(text)
        if date_matches:
            d_val = self._parse_date_stub(date_matches[0])
            if d_val:
                res.fields.append(ExtractedField(name="document_date", value=d_val, confidence=0.7, source_text_ref=date_matches[0].strip()))

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_decimal_stub(self, val_str: str) -> Decimal:
        cleaned = val_str.replace(",", "").strip()
        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return Decimal("0.00")

    def _parse_date_stub(self, date_str: str) -> Optional[date]:
        cleaned = date_str.replace("-", "/").replace(".", "/").strip()
        parts = cleaned.split("/")
        if len(parts) == 3:
            try:
                if len(parts[0]) == 4:
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
                else:
                    y = int(parts[2])
                    if y < 100:
                        y += 2000
                    return date(y, int(parts[1]), int(parts[0]))
            except ValueError:
                return None
        return None

