"""
Rule-based Document Classifier for DhanSarthi.

Determines the likely DocumentType of a document based on text keywords/signals
and returns classification confidence.
"""

from __future__ import annotations

import math
from typing import List
from pydantic import BaseModel
from app.models.enums import DocumentType
from app.core.config import settings


class ClassificationResult(BaseModel):
    """Structure returned by the document classifier."""

    document_type: DocumentType
    confidence: float
    signals: List[str]


class DocumentClassifier:
    """Classifies raw text using keyword frequency and weights."""

    def __init__(self) -> None:
        # Define keyword sets with weights for all 10 document types
        self._rules = {
            DocumentType.BANK_STATEMENT: {
                "high_priority": ["bank statement", "statement of account", "passbook", "opening balance", "closing balance"],
                "keywords": [
                    "account number", "statement of account", "transaction date",
                    "debit", "credit", "opening balance", "closing balance",
                    "withdrawal", "deposit", "cheque", "ledger balance", "rtgs", "neft",
                    "ifsc", "bank statement", "passbook", "ac no", "account no"
                ],
                "weight": 1.0
            },
            DocumentType.SALARY_SLIP: {
                "high_priority": ["salary slip", "pay slip", "payslip", "pay-slip", "salary statement"],
                "keywords": [
                    "payslip", "pay slip", "salary slip", "basic salary", "basic pay",
                    "provident fund", "epf", "net pay", "gross earnings", "deductions",
                    "allowance", "house rent allowance", "hra", "lta", "gratuity",
                    "employee id", "employee name", "net salary", "gross salary", "take home",
                    "company", "employer", "salary", "pay period", "designation", "department",
                    "esi", "tds", "pay date", "earnings"
                ],
                "weight": 1.2
            },
            DocumentType.LOAN_STATEMENT: {
                "high_priority": ["loan statement", "loan account", "emi schedule", "sanction letter"],
                "keywords": [
                    "loan account", "outstanding principal", "emi", "tenure",
                    "rate of interest", "principal amount", "outstanding balance",
                    "disbursement", "interest rate", "repayment schedule", "lender", "foreclosure",
                    "borrower", "sanction letter", "loan amount", "borrower name"
                ],
                "weight": 1.0
            },
            DocumentType.INVESTMENT_STATEMENT: {
                "high_priority": ["mutual fund statement", "folio number", "holding statement", "demat statement"],
                "keywords": [
                    "folio number", "mutual fund", "nav", "portfolio value",
                    "transaction units", "sip", "dividend", "mutual fund statement",
                    "demat", "holding statement", "units balance", "scheme name", "isin",
                    "current value", "purchase value", "returns"
                ],
                "weight": 1.0
            },
            DocumentType.TAX_DOCUMENT: {
                "high_priority": ["form 16", "form 26as", "income tax return", "itr-v", "tax deduction certificate"],
                "keywords": [
                    "form 16", "income tax", "section 80c", "tax deduction", "tds",
                    "assessment year", "pan card", "itr", "tax return", "financial year",
                    "form 26as", "taxable income", "tax paid", "taxpayer"
                ],
                "weight": 1.0
            },
            DocumentType.BILL: {
                "high_priority": ["electricity bill", "utility bill", "water bill", "gas bill", "telecom bill"],
                "keywords": [
                    "utility bill", "bill number", "bill date", "electricity bill", "water bill",
                    "gas bill", "consumer number", "due date", "amount due", "total payable",
                    "billing period", "biller name", "units consumed"
                ],
                "weight": 1.0
            },
            DocumentType.INVOICE: {
                "high_priority": ["tax invoice", "commercial invoice", "invoice number"],
                "keywords": [
                    "invoice", "tax invoice", "invoice number", "invoice date", "seller",
                    "buyer", "vendor", "gstin", "subtotal", "tax amount", "payment status",
                    "bill to", "ship to", "unit price", "po number"
                ],
                "weight": 1.0
            },
            DocumentType.INSURANCE_DOCUMENT: {
                "high_priority": ["insurance policy", "policy schedule", "insurance certificate"],
                "keywords": [
                    "insurance policy", "policy number", "sum assured", "premium",
                    "policyholder", "insured", "expiry date", "insurance company",
                    "coverage", "policy period", "claim"
                ],
                "weight": 1.0
            },
            DocumentType.EXPENSE_RECEIPT: {
                "high_priority": ["cash receipt", "payment receipt", "pos receipt", "store receipt"],
                "keywords": [
                    "receipt", "payment receipt", "merchant", "cash receipt", "pos receipt",
                    "total paid", "card payment", "change", "store", "counter"
                ],
                "weight": 1.0
            },
            DocumentType.BUSINESS_FINANCIAL_DOCUMENT: {
                "high_priority": ["balance sheet", "profit and loss statement", "cash flow statement", "trial balance"],
                "keywords": [
                    "balance sheet", "profit and loss", "p&l", "revenue", "operating expense",
                    "cash flow statement", "trial balance", "gross profit", "ebitda",
                    "company registration", "auditor report"
                ],
                "weight": 1.0
            }
        }

    def classify(self, text: str) -> ClassificationResult:
        """
        Scan text to count matching keywords for each category.

        Returns:
            ClassificationResult containing the classified DocumentType and confidence.
        """
        if not text or not text.strip():
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                signals=[]
            )

        lower_text = text.lower()
        scores = {}
        signals_map = {}
        high_priority_hits = {}

        for doc_type, rule in self._rules.items():
            matched = []
            score = 0.0
            has_hp = False
            
            # Check high priority phrases first
            for hp in rule.get("high_priority", []):
                if hp in lower_text:
                    score += 3.0 * rule["weight"]
                    matched.append(hp)
                    has_hp = True

            for kw in rule["keywords"]:
                if kw in matched:
                    continue
                count = lower_text.count(kw)
                if count > 0:
                    matched.append(kw)
                    score += rule["weight"] * (1.0 + math.log(count))
            
            scores[doc_type] = score
            signals_map[doc_type] = matched
            high_priority_hits[doc_type] = has_hp

        if not scores:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                signals=[]
            )

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        if best_score == 0.0:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                signals=[]
            )

        # Calculate confidence normalized by score magnitude and relative margin over second best
        sorted_scores = sorted(scores.values(), reverse=True)
        second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0

        # Base confidence from raw score and separation margin
        score_factor = min(1.0, best_score / 4.0)
        margin_factor = 1.0 if second_score == 0 else min(1.0, (best_score - second_score) / best_score)
        
        confidence = (0.6 * score_factor) + (0.4 * margin_factor)
        if high_priority_hits[best_type]:
            confidence = max(confidence, 0.85)

        signals = signals_map[best_type]
        threshold = settings.document_classification_threshold

        if confidence < threshold and not high_priority_hits[best_type]:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                signals=[]
            )

        return ClassificationResult(
            document_type=best_type,
            confidence=round(confidence, 2),
            signals=signals
        )

