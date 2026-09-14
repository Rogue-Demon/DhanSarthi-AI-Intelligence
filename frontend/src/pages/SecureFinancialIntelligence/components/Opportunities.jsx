/**
 * Opportunities — Cards displaying identified financial opportunities.
 */
export default function Opportunities({ opportunities }) {
  if (!opportunities || opportunities.length === 0) {
    return null
  }

  return (
    <section className="secure-fi-opps">
      <div className="secure-fi-section-title">
        <span className="secure-fi-section-title__icon">🚀</span>
        Opportunities ({opportunities.length})
      </div>
      <div className="secure-fi-opps__grid">
        {opportunities.map((opp, i) => (
          <div key={`opp-${i}`} className="secure-fi-opp-card">
            <div className="secure-fi-opp-card__header">
              <span className="secure-fi-opp-card__icon">💡</span>
              <span className="secure-fi-opp-card__title">{opp.title}</span>
            </div>
            <div className="secure-fi-opp-card__explanation">{opp.explanation}</div>
            <div className="secure-fi-opp-card__benefit">
              <strong>Potential Benefit:</strong> {opp.potential_benefit}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
