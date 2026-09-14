/**
 * AIAdvice — Personalized AI advice summary and action priorities.
 */
export default function AIAdvice({ advice }) {
  if (!advice) return null

  return (
    <section className="secure-fi-advice">
      <div className="secure-fi-section-title">
        <span className="secure-fi-section-title__icon">✨</span>
        AI Financial Advice
      </div>
      <div className="secure-fi-advice__card">
        {!advice.generated && (
          <div className="secure-fi-advice__fallback-badge">ℹ️ Rule-Based Advice Summary</div>
        )}
        <div className="secure-fi-advice__summary">{advice.summary}</div>

        {advice.priorities && advice.priorities.length > 0 && (
          <>
            <div className="secure-fi-advice__priorities-title">Recommended Priorities</div>
            <ul className="secure-fi-advice__priorities">
              {advice.priorities.map((item, idx) => (
                <li key={idx} className="secure-fi-advice__priority">
                  {item}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </section>
  )
}
