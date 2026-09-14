import { useState, useRef, useEffect } from 'react'

/**
 * PinAuthScreen — 4-digit PIN entry for secure access authentication.
 *
 * Features:
 * - Auto-focus and auto-advance between digit inputs
 * - Backspace navigation
 * - Paste support (4-digit)
 * - Error shake animation
 * - Loading state during verification
 */
export default function PinAuthScreen({ onSubmit, error, loading }) {
  const [digits, setDigits] = useState(['', '', '', ''])
  const inputRef0 = useRef(null)
  const inputRef1 = useRef(null)
  const inputRef2 = useRef(null)
  const inputRef3 = useRef(null)
  const inputRefs = [inputRef0, inputRef1, inputRef2, inputRef3]

  useEffect(() => {
    inputRef0.current?.focus()
  }, [])

  const handleChange = (index, value) => {
    // Accept only single digit
    const digit = value.replace(/\D/g, '').slice(-1)
    const newDigits = [...digits]
    newDigits[index] = digit
    setDigits(newDigits)

    // Auto-advance to next input
    if (digit && index < 3) {
      inputRefs[index + 1].current?.focus()
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs[index - 1].current?.focus()
    }
    if (e.key === 'Enter') {
      handleSubmit()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 4)
    if (pasted.length === 4) {
      const newDigits = pasted.split('')
      setDigits(newDigits)
      inputRefs[3].current?.focus()
    }
  }

  const handleSubmit = () => {
    const pin = digits.join('')
    if (pin.length === 4 && !loading) {
      onSubmit(pin)
    }
  }

  const isComplete = digits.every((d) => d !== '')

  return (
    <div className="secure-fi-auth">
      <div className="secure-fi-auth__card">
        <div className="secure-fi-auth__shield">🛡️</div>
        <h1 className="secure-fi-auth__title">Secure Access</h1>
        <p className="secure-fi-auth__subtitle">
          Enter your 4-digit PIN to view financial intelligence
        </p>

        <div className="secure-fi-auth__pin-group" onPaste={handlePaste}>
          {digits.map((digit, i) => (
            <input
              key={i}
              ref={inputRefs[i]}
              id={`secure-fi-pin-${i}`}
              type="password"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              className={[
                'secure-fi-auth__pin-digit',
                digit ? 'secure-fi-auth__pin-digit--filled' : '',
                error ? 'secure-fi-auth__pin-digit--error' : '',
              ]
                .filter(Boolean)
                .join(' ')}
              autoComplete="off"
              aria-label={`PIN digit ${i + 1}`}
              disabled={loading}
            />
          ))}
        </div>

        <button
          id="secure-fi-submit-pin"
          className="secure-fi-auth__submit"
          onClick={handleSubmit}
          disabled={!isComplete || loading}
        >
          {loading && <span className="secure-fi-spinner" />}
          {loading ? 'Verifying…' : 'Unlock'}
        </button>

        {error && <div className="secure-fi-auth__error">{error}</div>}

        <div className="secure-fi-auth__branding">DhanSarthi · Secure Financial Intelligence</div>
      </div>
    </div>
  )
}
