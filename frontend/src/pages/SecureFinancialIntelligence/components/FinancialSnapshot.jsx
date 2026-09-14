const METRICS = [
  { key: 'monthly_income', label: 'Monthly Income', prefix: true },
  { key: 'monthly_expenses', label: 'Monthly Expenses', prefix: true },
  { key: 'net_cash_flow', label: 'Net Cash Flow', prefix: true, signed: true },
  { key: 'savings_rate_percent', label: 'Savings Rate', suffix: '%' },
  { key: 'investment_value', label: 'Investment Value', prefix: true },
  { key: 'outstanding_debt', label: 'Outstanding Debt', prefix: true },
  { key: 'net_worth', label: 'Net Worth', prefix: true, signed: true },
  { key: 'emergency_fund_months', label: 'Emergency Fund', suffix: ' months' },
]

const CURRENCY_SYMBOLS = {
  INR: '₹',
  USD: '$',
  EUR: '€',
  GBP: '£',
}

function formatValue(value, metric, currency) {
  if (value === null || value === undefined) {
    return { text: 'N/A', className: 'secure-fi-metric-card__value--na' }
  }

  const num = parseFloat(value)
  const symbol = CURRENCY_SYMBOLS[currency] || currency + ' '

  let text
  if (metric.prefix) {
    const formattedNum = `${symbol}${Math.abs(num).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
    if (metric.signed && num < 0) text = `-${formattedNum}`
    else if (metric.signed && num > 0) text = `+${formattedNum}`
    else text = formattedNum
  } else if (metric.suffix) {
    text = `${num.toLocaleString('en-IN', { maximumFractionDigits: 1 })}${metric.suffix}`
  } else {
    text = num.toLocaleString('en-IN', { maximumFractionDigits: 1 })
  }

  let className = ''
  if (metric.signed) {
    className =
      num >= 0 ? 'secure-fi-metric-card__value--positive' : 'secure-fi-metric-card__value--negative'
  }

  return { text, className }
}

/**
 * FinancialSnapshot — Grid of key financial metric cards.
 */
export default function FinancialSnapshot({ snapshot }) {
  return (
    <section className="secure-fi-snapshot">
      <div className="secure-fi-section-title">
        <span className="secure-fi-section-title__icon">📊</span>
        Financial Snapshot
      </div>
      <div className="secure-fi-snapshot__grid">
        {METRICS.map((metric) => {
          const { text, className } = formatValue(snapshot[metric.key], metric, snapshot.currency)
          return (
            <div key={metric.key} className="secure-fi-metric-card">
              <div className="secure-fi-metric-card__label">{metric.label}</div>
              <div className={`secure-fi-metric-card__value ${className}`}>{text}</div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
