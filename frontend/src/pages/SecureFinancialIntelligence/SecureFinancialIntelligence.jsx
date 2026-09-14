import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { apiClient, ENDPOINTS } from '@/services/api'
import PinAuthScreen from './components/PinAuthScreen'
import ProfileHeader from './components/ProfileHeader'
import DataQualityBanner from './components/DataQualityBanner'
import FinancialSnapshot from './components/FinancialSnapshot'
import RiskAreas from './components/RiskAreas'
import Opportunities from './components/Opportunities'
import AIAdvice from './components/AIAdvice'
import './SecureFinancialIntelligence.css'

export default function SecureFinancialIntelligence() {
  const { token } = useParams()
  const [authState, setAuthState] = useState(() => (token ? 'validating' : 'error')) // validating | auth_required | loading_data | authenticated | error
  const [errorMessage, setErrorMessage] = useState(() => (token ? '' : 'Invalid access link.'))
  const [pinError, setPinError] = useState('')
  const [pinLoading, setPinLoading] = useState(false)
  const [data, setData] = useState(null)

  // Step 1: Validate token on mount
  useEffect(() => {
    if (!token) return

    let isMounted = true

    const validateToken = async () => {
      try {
        const res = await apiClient.post(ENDPOINTS.secureIntelligence.validate, { token })
        if (!isMounted) return
        if (res.valid) {
          setAuthState('auth_required')
        } else {
          setAuthState('error')
          setErrorMessage(res.message || 'Secure access link is invalid or expired.')
        }
      } catch (err) {
        if (!isMounted) return
        setAuthState('error')
        setErrorMessage(err.message || 'Failed to validate secure access link.')
      }
    }

    validateToken()

    return () => {
      isMounted = false
    }
  }, [token])

  // Step 2: Handle PIN submission
  const handlePinSubmit = async (pin) => {
    setPinLoading(true)
    setPinError('')
    try {
      const res = await apiClient.post(ENDPOINTS.secureIntelligence.authenticate, {
        token,
        pin,
      })
      if (res.authenticated && res.session_token) {
        fetchIntelligenceData(res.session_token)
      } else {
        setPinError(res.message || 'Incorrect PIN. Please try again.')
        setPinLoading(false)
      }
    } catch (err) {
      setPinError(err.message || 'Incorrect PIN. Please try again.')
      setPinLoading(false)
    }
  }

  // Step 3: Fetch intelligence data with session token
  const fetchIntelligenceData = async (sessToken) => {
    setAuthState('loading_data')
    try {
      const res = await apiClient.get(ENDPOINTS.secureIntelligence.intelligence, {
        headers: {
          'X-Secure-Session': sessToken,
        },
      })
      setData(res)
      setAuthState('authenticated')
    } catch (err) {
      setAuthState('error')
      setErrorMessage(err.message || 'Failed to load financial intelligence.')
    } finally {
      setPinLoading(false)
    }
  }

  // Render: Loading token validation
  if (authState === 'validating') {
    return (
      <div className="secure-fi-loading">
        <div className="secure-fi-loading__spinner" />
      </div>
    )
  }

  // Render: Error screen
  if (authState === 'error') {
    return (
      <div className="secure-fi-error-page">
        <div>
          <div className="secure-fi-error-page__icon">🔒</div>
          <h1 className="secure-fi-error-page__title">Access Restricted</h1>
          <p className="secure-fi-error-page__message">{errorMessage}</p>
        </div>
      </div>
    )
  }

  // Render: PIN Auth Screen
  if (authState === 'auth_required') {
    return <PinAuthScreen onSubmit={handlePinSubmit} error={pinError} loading={pinLoading} />
  }

  // Render: Loading Intelligence Data
  if (authState === 'loading_data') {
    return (
      <div className="secure-fi-loading">
        <div className="secure-fi-loading__spinner" />
      </div>
    )
  }

  // Render: Full Intelligence Page
  if (authState === 'authenticated' && data) {
    return (
      <div className="secure-fi">
        <div className="secure-fi-page">
          <ProfileHeader profile={data.profile} dataAsOf={data.data_as_of} />

          <DataQualityBanner quality={data.data_quality} dataAsOf={data.data_as_of} />

          <FinancialSnapshot snapshot={data.financial_snapshot} />

          <RiskAreas risks={data.risks} />

          <Opportunities opportunities={data.opportunities} />

          <AIAdvice advice={data.ai_advice} />

          <footer className="secure-fi-footer">
            DhanSarthi Secure Financial Intelligence · Confidential & Read-Only · Generated at{' '}
            {new Date(data.data_as_of).toLocaleTimeString()}
          </footer>
        </div>
      </div>
    )
  }

  return null
}
