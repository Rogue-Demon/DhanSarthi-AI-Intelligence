"""
Mock model providers for unit testing and offline development.
"""

from __future__ import annotations

from typing import Any
from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.ai.schemas.advisor import AIContext


class MockLLMProvider(LLMProvider):
    """Generates deterministic mock responses without external network access."""

    def __init__(self, response_text: str = "Mock financial guidance response.") -> None:
        self.response_text = response_text
        self.last_prompt = ""
        self.last_context = None

    def _synthesize_dynamic_response(self, context: AIContext, prompt: str) -> str:
        # If custom non-default response_text was set (e.g., in unit tests), return it
        if self.response_text != "Mock financial guidance response.":
            return self.response_text

        q = (context.question or prompt or "").lower()
        fc = context.user_financial_context

        from decimal import Decimal

        nw_obj = getattr(fc, "net_worth", 0.0) if fc else 0.0
        if hasattr(nw_obj, "net_worth"):
            net_worth = float(getattr(nw_obj, "net_worth") or 0.0)
        elif isinstance(nw_obj, (int, float, Decimal)):
            net_worth = float(nw_obj)
        else:
            net_worth = 0.0

        inc_obj = getattr(fc, "monthly_income", 0.0) if fc else 0.0
        if hasattr(inc_obj, "total_income"):
            income = float(getattr(inc_obj, "total_income") or 0.0)
        elif isinstance(inc_obj, (int, float, Decimal)):
            income = float(inc_obj)
        else:
            income = 0.0

        exp_obj = getattr(fc, "monthly_expenses", 0.0) if fc else 0.0
        if hasattr(exp_obj, "total_expenses"):
            expenses = float(getattr(exp_obj, "total_expenses") or 0.0)
        elif isinstance(exp_obj, (int, float, Decimal)):
            expenses = float(exp_obj)
        else:
            expenses = 0.0
        surplus = max(0.0, income - expenses)
        savings_rate = (surplus / income * 100) if income > 0 else 0.0

        has_data = fc and (net_worth != 0 or income != 0 or expenses != 0)

        # 1. Net worth / overview query
        if any(w in q for w in ["net worth", "summary", "overview", "status", "profile", "wealth", "balance"]):
            if has_data:
                return (
                    f"Here is your personalized financial summary based on your connected records:\n\n"
                    f"• **Net Worth**: ₹{net_worth:,.2f}\n"
                    f"• **Monthly Income**: ₹{income:,.2f}\n"
                    f"• **Monthly Expenses**: ₹{expenses:,.2f}\n"
                    f"• **Monthly Surplus**: ₹{surplus:,.2f} ({savings_rate:.1f}% savings rate)\n\n"
                    f"**Guidance**: Your net cash flow is positive. To accelerate wealth creation, "
                    f"aim to automate allocations of your monthly surplus into diversified investments "
                    f"and build a liquid emergency reserve of at least ₹{expenses * 6:,.2f}."
                )
            else:
                return (
                    "Your financial portfolio is currently clear and ready for setup.\n\n"
                    "• **Net Worth**: ₹0.00\n"
                    "• **Monthly Income**: ₹0.00\n"
                    "• **Monthly Expenses**: ₹0.00\n\n"
                    "To receive personalized AI guidance, start by adding your income sources, recurring expenses, "
                    "or assets in the DhanSarthi dashboard."
                )

        # 2. Investment / SIP / Mutual funds / Stocks query
        if any(w in q for w in ["invest", "sip", "mutual fund", "stock", "equity", "return", "portfolio", "growth"]):
            if has_data and surplus > 0:
                rec_sip = surplus * 0.7
                return (
                    f"Based on your monthly net surplus of ₹{surplus:,.2f}, here is a recommended investment approach:\n\n"
                    f"1. **Systematic Investment Plan (SIP)**: Allocate ~₹{rec_sip:,.2f}/month into low-cost index funds or broad-market equity mutual funds for long-term growth.\n"
                    f"2. **Emergency Buffer**: Ensure you maintain ₹{expenses * 6:,.2f} (6 months of expenses) in liquid fixed deposits or savings accounts.\n"
                    f"3. **Diversification**: Split investments between equity for growth and debt instruments for stability based on your risk tolerance."
                )
            return (
                "Here is a disciplined framework for starting your investment journey:\n\n"
                "1. **Emergency Reserve**: Build 3–6 months of essential monthly living expenses in liquid funds.\n"
                "2. **SIP Allocation**: Start small with monthly Systematic Investment Plans (SIPs) in broad market index funds.\n"
                "3. **Debt Priority**: High-interest debts (like credit cards) should be cleared before making major investments."
            )

        # 3. Budget / Expense / Savings query
        if any(w in q for w in ["budget", "save", "saving", "expense", "spend", "cost", "cut"]):
            if has_data:
                return (
                    f"Analysis of your monthly cash flow:\n\n"
                    f"• **Income**: ₹{income:,.2f}\n"
                    f"• **Expenses**: ₹{expenses:,.2f}\n"
                    f"• **Savings Rate**: {savings_rate:.1f}%\n\n"
                    f"**Recommendations**:\n"
                    f"1. **50/30/20 Rule**: Aim for 50% needs, 30% wants, and 20% savings.\n"
                    f"2. **Expense Tracking**: Review recurring subscriptions and non-essential spending.\n"
                    f"3. **Target Savings**: Your current monthly net savings of ₹{surplus:,.2f} provides a strong foundation."
                )
            return (
                "To optimize your budget and increase savings:\n\n"
                "1. **Track Monthly Cashflow**: Log all income streams and recurring expenses.\n"
                "2. **Follow the 50/30/20 Rule**: 50% for needs, 30% for wants, and 20% committed to savings/investments.\n"
                "3. **Emergency Reserve**: Build a liquid safety buffer of 3-6 months' living expenses."
            )

        # 4. Fallback / General Financial Guidance
        if has_data:
            return (
                f"Regarding your inquiry about: *'{context.question}'*\n\n"
                f"Based on your profile (Net Worth: ₹{net_worth:,.2f}, Monthly Income: ₹{income:,.2f}, Expenses: ₹{expenses:,.2f}):\n\n"
                f"• Maintain disciplined monthly savings (currently ₹{surplus:,.2f}/month).\n"
                f"• Ensure emergency fund coverage of ₹{expenses * 6:,.2f}.\n"
                f"• Focus on long-term wealth building through automated investments and asset allocation.\n\n"
                f"Feel free to ask specific questions about budgeting, investments, tax planning, or loan management!"
            )

        return (
            f"Thank you for asking: *'{context.question}'*\n\n"
            f"As your DhanSarthi AI Financial Advisor, here are core financial principles to follow:\n\n"
            f"1. **Budgeting**: Always maintain positive monthly net cash flow.\n"
            f"2. **Emergency Fund**: Keep 3-6 months of expenses liquid.\n"
            f"3. **Investing**: Start early with systematic investments in index funds.\n"
            f"4. **Protection**: Secure essential health and life insurance.\n\n"
            f"Add your financial details in the dashboard to unlock personalized recommendations!"
        )

    async def generate(self, context: AIContext, prompt: str, **kwargs: Any) -> str:
        self.last_prompt = prompt
        self.last_context = context
        tracker = kwargs.get("tracker")
        routing_decision = kwargs.get("routing_decision")
        selected_model = kwargs.get("model") or kwargs.get("model_name") or (routing_decision.model if routing_decision else "mock-llama-3-8b")
        
        response_text = self._synthesize_dynamic_response(context, prompt)
        
        if tracker:
            tracker.record_str("provider_name", "mock")
            tracker.record_str("selected_model", selected_model)
            if routing_decision:
                tracker.record_str("model_routing_reason", routing_decision.reason)

            config = kwargs.get("config") or kwargs.get("inference_config")
            max_tokens = config.max_tokens if config else kwargs.get("max_tokens", 512)
            tracker.record_count("max_tokens_budget", max_tokens)
            tracker.record_count("effective_max_tokens", max_tokens)

            from app.ai.inference.tokenizer import get_tokenizer
            tokenizer = get_tokenizer()
            p_tok = tokenizer.count_tokens(prompt)
            g_tok = tokenizer.count_tokens(response_text)
            tracker.record_count("prompt_tokens", p_tok)
            tracker.record_count("generated_tokens", g_tok)
            tracker.record("generation_ms", 10.0)
            tracker.record("total_llm_ms", 10.0)
            tracker.record("tokens_per_second", 150.0)
            tracker.record_str("request_status", "SUCCESS")
        return response_text

    async def generate_stream(
        self,
        context: AIContext,
        prompt: str,
        tracker: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ):
        self.last_prompt = prompt
        self.last_context = context
        routing_decision = kwargs.get("routing_decision")
        selected_model = kwargs.get("model") or kwargs.get("model_name") or (routing_decision.model if routing_decision else "mock-llama-3-8b")
        if tracker:
            tracker.record_str("provider_name", "mock")
            tracker.record_str("selected_model", selected_model)
            tracker.record_flag("streaming_used", True)
            tracker.record("ttft_ms", 1.5)
            tracker.record("time_to_first_token_ms", 1.5)
            tracker.record("time_to_first_byte_ms", 1.5)
            if routing_decision:
                tracker.record_str("model_routing_reason", routing_decision.reason)

            config = kwargs.get("config") or kwargs.get("inference_config")
            eff_max = config.max_tokens if config else (max_tokens or 512)
            tracker.record_count("max_tokens_budget", eff_max)
            tracker.record_count("effective_max_tokens", eff_max)

            from app.ai.inference.tokenizer import get_tokenizer
            tokenizer = get_tokenizer()
            p_tok = tokenizer.count_tokens(prompt)
            g_tok = tokenizer.count_tokens(self.response_text)
            tracker.record_count("prompt_tokens", p_tok)
            tracker.record_count("generated_tokens", g_tok)
            tracker.record("generation_ms", 12.0)
            tracker.record("total_llm_ms", 13.5)
            tracker.record("tokens_per_second", 120.0)
            tracker.record_str("request_status", "SUCCESS")

        words = self.response_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


class MockEmbeddingProvider(EmbeddingProvider):
    """Generates dummy vector floats without external network access."""

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    async def embed(self, text: str) -> list[float]:
        # Return a deterministic mock vector matching the requested dimension
        # Use a simple hashing or pattern so different texts produce slightly different vectors
        base = [0.1 * ((i % 10) + 1) for i in range(self.dim)]
        if text:
            mod = (sum(ord(c) for c in text) % 10) * 0.01
            base = [x + mod for x in base]
        return base
