const QUALITY_CONFIG = {
  COMPLETE: {
    icon: '✅',
    label: 'Complete Financial Profile',
    text: 'All financial data streams are active and up to date.',
    className: 'secure-fi-dq-banner--complete',
  },
  GOOD: {
    icon: 'ℹ️',
    label: 'Good Data Freshness',
    text: 'Most financial areas are covered with accurate data.',
    className: 'secure-fi-dq-banner--good',
  },
  PARTIAL: {
    icon: '⚠️',
    label: 'Partial Data Profile',
    text: 'Some financial streams (e.g. investments or budgets) are missing or incomplete.',
    className: 'secure-fi-dq-banner--partial',
  },
  LIMITED: {
    icon: '🚨',
    label: 'Limited Data Available',
    text: 'Data quality is limited. Adding income, expense, or asset details will improve intelligence accuracy.',
    className: 'secure-fi-dq-banner--limited',
  },
}

/**
 * DataQualityBanner — Displays financial data completeness indicator.
 */
export default function DataQualityBanner({ quality, dataAsOf }) {
  const config = QUALITY_CONFIG[quality] || QUALITY_CONFIG.LIMITED
  const formattedDate = dataAsOf
    ? new Date(dataAsOf).toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : ''

  return (
    <div className={`secure-fi-dq-banner ${config.className}`}>
      <span>{config.icon}</span>
      <div>
        <strong>{config.label}:</strong> {config.text}{' '}
        {formattedDate && <span style={{ opacity: 0.8 }}>(As of {formattedDate})</span>}
      </div>
    </div>
  )
}
