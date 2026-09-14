"""
Financial Domain Scope Guard for DhanSarthi AI Advisor.

Provides layered, deterministic classification of user query intent against DhanSarthi's financial scope:
  - Layer 1: Fast deterministic keyword & regex pattern matching for explicit financial vs non-financial queries.
  - Layer 2: Conversation history inspection for contextual short follow-ups (e.g. "What should I do with it?").
  - Layer 3: Categorized polite refusal generator (positive, helpful redirect to financial topics).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GuardResult:
    """Result of Financial Domain Guard inspection."""

    is_financial: bool
    refusal_message: Optional[str] = None
    category: str = "FINANCIAL"  # FINANCIAL, NON_FINANCIAL_POLITICS, NON_FINANCIAL_TRIVIA, NON_FINANCIAL_CODING, etc.
    is_mixed: bool = False
    confidence: float = 1.0
    reason: str = ""


class FinancialDomainGuard:
    """Layered Financial Domain Scope Guard."""

    # ---------------------------------------------------------------------------
    # Explicit Financial Intent Patterns & Keywords
    # ---------------------------------------------------------------------------

    FINANCIAL_KEYWORDS = [
        "money", "finance", "financial", "budget", "budgeting", "expense", "expenses",
        "spending", "spent", "spend", "income", "salary", "earning", "earnings",
        "save", "savings", "saver", "invest", "investment", "investing", "investments",
        "portfolio", "mutual fund", "mutual funds", "sip", "lump sum", "lumpsum",
        "stock", "stocks", "share", "shares", "equity", "nifty", "sensex", "market",
        "debt", "loan", "loans", "emi", "borrow", "borrowing", "interest rate", "repo rate",
        "cibil", "credit score", "creditworthiness", "dcs", "loan readiness", "repayment",
        "repayment behaviour", "credit card", "tax", "taxes", "taxation", "80c", "gst",
        "capital gains", "insurance", "premium", "policy", "claim", "asset", "assets",
        "liability", "liabilities", "net worth", "networth", "wealth", "cash flow",
        "cashflow", "retirement", "pension", "epf", "ppf", "nps", "fd", "fixed deposit",
        "rd", "recurring deposit", "gold price", "silver price", "dividend", "yield",
        "inflation", "compound interest", "compounding", "financial health", "emergency fund",
        "working capital", "profit margin", "revenue", "payroll", "balance sheet",
        "bank statement", "salary slip", "invoice", "itr", "tax return", "crypto",
        "bitcoin", "etf", "bond", "bonds", "reit", "real estate", "mortgage", "home loan",
        "car loan", "personal loan", "education loan", "term plan", "health insurance",
    ]

    FINANCIAL_PATTERNS = [
        # Creditworthiness & DCS
        r"\b(dcs|creditworthiness|credit score|loan readiness)\b",
        r"\b(why is my score (low|high|changing|different))\b",
        r"\b(why did my (score|dcs) change)\b",
        r"\b(am i ready for a loan|loan readiness)\b",
        r"\b(how (can|to) (improve|increase|build) my (score|creditworthiness|dcs))\b",
        r"\b(what is affecting my (score|creditworthiness|dcs))\b",
        # Affordability & Decisions
        r"\bcan i afford\b",
        r"\bshould i buy\b",
        r"\bshould i invest\b",
        r"\bhow much should i (save|invest|spend|keep|put)\b",
        r"\bwhat should i do with (my money|my salary|my savings|my income|₹|\$|\d+)\b",
        r"\bcan i retire\b",
        r"\bhow to (reduce|cut|manage|track) (my )?(expenses?|spending|debt|taxes?|cost)\b",
        r"\bhow to (increase|grow|build) (my )?(savings?|wealth|net worth|income)\b",
        r"\bis (it|this) a good time to (invest|buy|sell)\b",
        r"\bwhere should i (invest|put|keep) my\b",
        r"\bhow much (emergency fund|money) (do i|should i)\b",
        # Financial Concepts & Definitions
        r"\bwhat is (a |an )?(sip|mutual fund|ppf|nps|epf|emi|gst|cibil|dcs|creditworthiness|cagr|xirr|nav|fd|rd|index fund|stock|bond|etf|reit|inflation|compound interest|net worth|dti|debt to income|cash flow|capital gain|tax saver|emergency fund|working capital|profit margin|balance sheet)\b",
        r"\bexplain (compound interest|sip|mutual funds?|inflation|cagr|xirr|taxes?|80c|asset allocation|dollar cost averaging|rupee cost averaging|dcs|creditworthiness)\b",
        r"\bdifference between (sip|lump sum|mutual fund|stocks?|direct|regular|ppf|nps|term insurance|endowment|cibil|dcs)\b",
        # Calculations & Metrics
        r"\bcalculate (emi|sip|returns?|interest|tax|capital gains?|loan|mortgage)\b",
        r"\bwhat is my (savings rate|net worth|spending|total expense|dti|debt ratio|creditworthiness|dcs|score)\b",
        # Business Finance
        r"\b(business|startup|company) (cash flow|revenue|profit|working capital|expenses?|payroll|loan|margin)\b",
        # Document & Statement Analysis
        r"\b(analyze|summarize|review|explain) (this|my) (bank statement|tax document|invoice|salary slip|loan statement|financial statement|document)\b",
        # Financial News / Policy Impact
        r"\bhow (will|could|does|might) (the )?(rbi|union budget|budget|tax policy|interest rate|inflation|fed) (affect|impact) (my )?(loan|emi|investments?|taxes?|savings?)\b",
        r"\b(rbi|rate hike|rate cut|budget|tax slab) (impact|effect) on\b",
    ]

    # Short follow-up phrases that inherit financial scope from conversation context
    CONTEXTUAL_FOLLOWUP_PATTERNS = [
        r"^how much should i (save|invest|put|keep)\??$",
        r"^what about the loan\??$",
        r"^how much do i need\??$",
        r"^what should i do with it\??$",
        r"^is it safe\??$",
        r"^should i do it\??$",
        r"^can i afford it\??$",
        r"^what is the emi\??$",
        r"^how long will it take\??$",
        r"^which one is better\??$",
        r"^what are the tax implications\??$",
    ]

    # ---------------------------------------------------------------------------
    # Explicit Non-Financial Intent Patterns (REJECT)
    # ---------------------------------------------------------------------------

    NON_FINANCIAL_PATTERNS = {
        "POLITICS": [
            r"\b(who is|who was|current|latest)?\s*([\w'\s]+\s+)?(prime minister|president|chief minister|governor|chancellor|king|queen|emperor)\b",
            r"\b(who won|winner of) (the )?(election|polls|voting|presidential election)\b",
            r"\b(political|parliament|congress|bjp|democrats|republicans|senate) (party|leader|news|debate)\b",
            r"\bwho is (narendra modi|biden|trump|putin|xi jinping|sunak|rahul gandhi|kejriwal)\b",
        ],
        "GENERAL_TRIVIA": [
            r"\bwhat is the capital of\b",
            r"\bwho (discovered|invented|founded|wrote|painted|directed|built) (the |a )?(moon|gravity|america|light bulb|iphone|facebook|python|java|relativity|taj mahal|mona lisa)\b",
            r"\bhow far is (the moon|mars|sun|jupiter)\b",
            r"\bwhat is the (boiling point|speed of light|formula for|atomic number)\b",
            r"\bexplain (quantum physics|black hole|string theory|photosynthesis|theory of relativity|plate tectonics)\b",
        ],
        "SPORTS_ENTERTAINMENT": [
            r"\bwho won (the )?(cricket|football|world cup|ipl|match|game|super bowl|nba)\b",
            r"\b(score|result) of (the )?(match|game|ipl)\b",
            r"\bwhat movie (should i|to) watch\b",
            r"\bwho is (virat kohli|rohit sharma|messi|ronaldo|dhoni|actor|actress|singer)\b",
            r"\b(movie|film|song|music|actor) review\b",
        ],
        "CREATIVE_WRITING": [
            r"^\s*(write|compose|tell) (me )?(a )?(poem|joke|story|song|riddle|fairy tale)\b",
            r"^\s*(tell|make) me a joke\b",
        ],
        "PROGRAMMING": [
            r"\b(write|create|generate) (a |an )?(python|javascript|typescript|c\+\+|java|html|css|sql|bash) (program|script|code|function|class|app)\b",
            r"\bhow to (fix|debug|resolve) (a |an )?(nullpointerexception|syntaxerror|typeerror|segmentation fault|memory leak|recursion error)\b",
            r"\bexplain (react hooks|async await|closure in js|dependency injection|binary tree|linked list|quick sort)\b",
        ],
        "WEATHER_DAILY_LIFE": [
            r"\bwhat is the weather\b",
            r"\bis it going to rain\b",
            r"\bwhat should i (eat|wear|cook) (for dinner|today|tonight)\b",
            r"\bhow to (make|cook|prepare) (coffee|tea|pizza|pasta|biryani)\b",
        ],
        "GENERAL_SHOPPING": [
            r"^\s*what is the price of (the )?(latest )?(iphone|macbook|car|tesla|ferrari|shoe|watch|laptop)\??\s*$",
            r"^\s*how much does a (ferrari|lamborghini|rolex|bugatti) cost\??\s*$",
        ],
        "GENERAL_PEOPLE": [
            r"^\s*tell me about (elon musk|jeff bezos|steve jobs|bill gates|mark zuckerberg)\??\s*$",
            r"^\s*who is (elon musk|jeff bezos|steve jobs|bill gates|mark zuckerberg)\??\s*$",
        ],
    }

    # Standard positive polite refusal messages by category
    REFUSAL_MESSAGES = {
        "POLITICS": (
            "I’m DhanSarthi AI, your financial advisor, so I’m focused on helping with money and financial decisions. "
            "I can’t help with general political or non-financial questions, but I’d be happy to help with budgeting, "
            "savings, investments, loans, taxes, or your financial goals."
        ),
        "PROGRAMMING": (
            "I’m focused on financial assistance, so I can’t help with general programming questions. "
            "I’d be happy to help you analyze or plan something related to your personal finances, budgeting, or investments."
        ),
        "GENERAL": (
            "I’m DhanSarthi AI, focused specifically on financial guidance. "
            "I can’t assist with general non-financial questions, but I can help with your budgeting, savings, "
            "investments, loans, taxes, or financial goals. What financial topic would you like to explore?"
        ),
    }

    def check_query(
        self,
        query: str,
        history: Optional[List] = None,
    ) -> GuardResult:
        """
        Inspect query and evaluate whether it falls within DhanSarthi's financial domain.

        Args:
            query: Raw user message string.
            history: Optional conversation message history.

        Returns:
            GuardResult indicating whether the query is financial, refusal message if non-financial, etc.
        """
        if not getattr(settings, "financial_domain_guard_enabled", True):
            return GuardResult(is_financial=True, category="FINANCIAL", confidence=1.0)

        if not query or not query.strip():
            return GuardResult(is_financial=True, category="CASUAL", confidence=1.0)

        q_clean = query.strip()
        q_lower = q_clean.lower()

        # ---------------------------------------------------------------------------
        # 0. Casual Greetings & Meta Capabilities
        # ---------------------------------------------------------------------------
        if self._is_casual(q_lower):
            return GuardResult(is_financial=True, category="CASUAL", confidence=1.0)

        # ---------------------------------------------------------------------------
        # 1. Layer 1: Check Explicit Non-Financial Patterns (High Priority Rejection)
        # ---------------------------------------------------------------------------
        non_fin_category = self._match_non_financial(q_lower)
        if non_fin_category:
            # Check if this query has an explicit financial implication attached (MIXED QUERY)
            if self._has_explicit_financial_context(q_lower):
                logger.info(f"[DomainGuard] Query contains non-financial topic '{non_fin_category}' but includes financial intent: '{q_clean}'")
                return GuardResult(
                    is_financial=True,
                    category="MIXED_FINANCIAL",
                    is_mixed=True,
                    confidence=0.9,
                    reason="Contains financial implications alongside general topic",
                )
            
            # Pure non-financial match -> REJECT
            refusal_key = "POLITICS" if non_fin_category == "POLITICS" else ("PROGRAMMING" if non_fin_category == "PROGRAMMING" else "GENERAL")
            refusal_text = self.REFUSAL_MESSAGES.get(refusal_key, self.REFUSAL_MESSAGES["GENERAL"])
            logger.info(f"[DomainGuard] Non-financial query rejected ({non_fin_category}): '{q_clean}'")
            return GuardResult(
                is_financial=False,
                refusal_message=refusal_text,
                category=non_fin_category,
                confidence=0.98,
                reason=f"Matched non-financial pattern category: {non_fin_category}",
            )

        # ---------------------------------------------------------------------------
        # 2. Layer 1: Check Explicit Financial Indicators (High Priority Acceptance)
        # ---------------------------------------------------------------------------
        if self._has_explicit_financial_context(q_lower):
            return GuardResult(is_financial=True, category="FINANCIAL", confidence=1.0)

        # ---------------------------------------------------------------------------
        # 3. Layer 2: Check Conversation Context for Short/Ambiguous Queries
        # ---------------------------------------------------------------------------
        if self._is_contextual_followup(q_lower):
            if history and self._history_has_financial_context(history):
                logger.info(f"[DomainGuard] Contextual short query passed via conversation history: '{q_clean}'")
                return GuardResult(
                    is_financial=True,
                    category="FINANCIAL_CONTEXTUAL",
                    confidence=0.95,
                    reason="Inherited financial intent from conversation history",
                )

        # Also if the history clearly shows an ongoing financial discussion and query is not explicitly non-financial
        if history and len(history) >= 2 and self._history_has_financial_context(history):
            if not self._is_severely_non_financial(q_lower):
                logger.info(f"[DomainGuard] Query allowed under active financial conversation history: '{q_clean}'")
                return GuardResult(
                    is_financial=True,
                    category="FINANCIAL_HISTORY_ACTIVE",
                    confidence=0.9,
                    reason="Active financial conversation thread",
                )

        # ---------------------------------------------------------------------------
        # 4. Fallback Default Evaluation: If no financial keywords or context found
        # ---------------------------------------------------------------------------
        if self._is_devoid_of_financial_intent(q_lower):
            logger.info(f"[DomainGuard] Query rejected due to absence of financial intent: '{q_clean}'")
            return GuardResult(
                is_financial=False,
                refusal_message=self.REFUSAL_MESSAGES["GENERAL"],
                category="NON_FINANCIAL_GENERAL",
                confidence=0.95,
                reason="No financial intent detected in query",
            )

        # Default pass for borderline financial queries
        return GuardResult(is_financial=True, category="FINANCIAL", confidence=0.8)

    def _is_casual(self, q_lower: str) -> bool:
        """Check if query is a casual greeting, thank you, or meta capability question."""
        casual_phrases = [
            "hi", "hello", "hey", "greetings", "namaste", "good morning", "good afternoon", "good evening",
            "thanks", "thank you", "thx", "how are you", "what can you do", "who are you", "help",
            "what are your capabilities", "how can you help me", "tell me about yourself",
        ]
        q_strip = re.sub(r"[^\w\s]", "", q_lower).strip()
        if q_strip in casual_phrases:
            return True
        for phrase in ["what can you do", "who are you", "how can you help", "tell me about yourself"]:
            if phrase in q_lower:
                return True
        return False

    def _has_explicit_financial_context(self, q_lower: str) -> bool:
        """Check if query contains explicit financial keywords or financial regex patterns."""
        for pattern in self.FINANCIAL_PATTERNS:
            if re.search(pattern, q_lower, re.IGNORECASE):
                return True

        for kw in self.FINANCIAL_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", q_lower, re.IGNORECASE):
                return True

        if re.search(r"(₹|\$|rs\.?|inr|lakh|crore|k)\s*\d+|\d+\s*(lakh|crore|k|rupees|dollars)", q_lower):
            return True

        return False

    def _match_non_financial(self, q_lower: str) -> Optional[str]:
        """Match query against non-financial category patterns."""
        for category, patterns in self.NON_FINANCIAL_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, q_lower, re.IGNORECASE):
                    return category
        return None

    def _is_contextual_followup(self, q_lower: str) -> bool:
        """Check if query is a short follow-up question."""
        for pat in self.CONTEXTUAL_FOLLOWUP_PATTERNS:
            if re.search(pat, q_lower, re.IGNORECASE):
                return True
        if len(q_lower.split()) <= 6 and any(w in q_lower for w in ["how much", "should i", "can i", "what about", "which one", "is it"]):
            return True
        return False

    def _history_has_financial_context(self, history: List) -> bool:
        """Check if recent conversation messages contain financial keywords/intent."""
        if not history:
            return False
        recent = history[-4:]
        for msg in recent:
            content = getattr(msg, "content", "") if hasattr(msg, "content") else str(msg)
            if self._has_explicit_financial_context(content.lower()):
                return True
        return False

    def _is_severely_non_financial(self, q_lower: str) -> bool:
        """Check if query is an obvious non-financial request even in ongoing conversation."""
        severely_non_financial_words = [
            "prime minister", "president of usa", "capital of france", "cricket match",
            "write a poem", "tell me a joke", "quantum physics", "weather today", "python code",
        ]
        return any(w in q_lower for w in severely_non_financial_words)

    def _is_devoid_of_financial_intent(self, q_lower: str) -> bool:
        """Evaluate if a non-casual query lacks any financial, money, or economic intent."""
        non_fin_indicators = [
            "who is", "who was", "where is", "what is the capital", "tell me about",
            "write a", "compose a", "how to cook", "how to make", "what movie",
            "who won", "play a", "sing a", "explain physics", "explain chemistry",
            "how does a", "how does", "how do",
        ]
        has_non_fin = any(ind in q_lower for ind in non_fin_indicators)
        has_fin = self._has_explicit_financial_context(q_lower)

        if has_non_fin and not has_fin:
            return True

        return False
