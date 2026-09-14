const SEVERITY_ICONS = {
  HIGH: '🔴',
  MEDIUM: '🟠',
  LOW: '🔵',
}

/**
 * RiskAreas — Cards displaying identified financial risk areas with severity.
 */
export default function RiskAreas({ risks }) {
  if (!risks || risks.length === 0) {
    return (
      <section className="secure-fi-risks">
        <div className="secure-fi-section-title">
          <span className="secure-fi-section-title__icon">⚠️</span>
          Risk Areas
        </div>
        <div className="secure-fi-empty">
          ✅ No significant financial risk areas identified. Great job!
        </div>
      </section>
    )
  }

  // Sort: HIGH first, then MEDIUM, then LOW
  const sortOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 }
  const sorted = [...risks].sort(
    (a, b) => (sortOrder[a.severity] ?? 3) - (sortOrder[b.severity] ?? 3)
  )

  return (
    <section className="secure-fi-risks">
      <div className="secure-fi-section-title">
        <span className="secure-fi-section-title__icon">⚠️</span>
        Risk Areas ({risks.length})
      </div>
      <div className="secure-fi-risks__grid">
        {sorted.map((risk, i) => (
          <div
            key={`risk-${i}`}
            className={`secure-fi-risk-card secure-fi-risk-card--${risk.severity}`}
          >
            <div className="secure-fi-risk-card__header">
              <span
                className={`secure-fi-risk-card__severity secure-fi-risk-card__severity--${risk.severity}`}
              >
                {SEVERITY_ICONS[risk.severity] || '⚪'} {risk.severity}
              </span>
              <span className="secure-fi-risk-card__title">{risk.title}</span>
            </div>
            <div className="secure-fi-risk-card__explanation">{risk.explanation}</div>
            <div className="secure-fi-risk-card__why">
              <strong>Why it matters:</strong> {risk.why_it_matters}
            </div>
            {risk.metric_value && (
              <div className="secure-fi-risk-card__metric">📏 {risk.metric_value}</div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
