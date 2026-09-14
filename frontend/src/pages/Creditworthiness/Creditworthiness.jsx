import React from 'react'
import { ShieldCheck, RefreshCw } from 'lucide-react'
import useCreditworthiness from '../../hooks/useCreditworthiness'
import RegulatoryDisclaimerBanner from '../../components/creditworthiness/RegulatoryDisclaimerBanner'
import CreditScoreGauge from '../../components/creditworthiness/CreditScoreGauge'
import DimensionBreakdownCard from '../../components/creditworthiness/DimensionBreakdownCard'
import FactorInsightsCard from '../../components/creditworthiness/FactorInsightsCard'
import LoanReadinessCard from '../../components/creditworthiness/LoanReadinessCard'
import CreditHistoryChart from '../../components/creditworthiness/CreditHistoryChart'

export function Creditworthiness() {
  const {
    creditData,
    isLoading,
    isError,
    error,
    historyData,
    recalculate,
    isRecalculating,
    recordShareConsent,
    isSharing,
  } = useCreditworthiness()

  if (isLoading) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="h-40 bg-slate-900/60 rounded-2xl animate-pulse" />
        <div className="h-64 bg-slate-900/60 rounded-2xl animate-pulse" />
        <div className="h-64 bg-slate-900/60 rounded-2xl animate-pulse" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-8 max-w-7xl mx-auto text-center space-y-4">
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-6 rounded-2xl">
          <h3 className="text-lg font-bold">Failed to Load Creditworthiness Profile</h3>
          <p className="text-xs mt-1 text-slate-400">
            {error?.message || 'Server error occurred while evaluating profile.'}
          </p>
        </div>
      </div>
    )
  }

  const {
    creditworthiness_score,
    status,
    risk_band,
    loan_readiness,
    confidence_label,
    data_coverage,
    dti_ratio,
    positive_factors,
    risk_factors,
    dimension_scores,
  } = creditData || {}

  const historyList = historyData?.history || []

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6 text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Creditworthiness Profile
            </h1>
            <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-0.5 rounded-full font-medium">
              DhanSarthi DCS
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Explainable internal assessment of financial health & loan readiness based on genuine
            DhanSarthi records.
          </p>
        </div>
      </div>

      {/* Mandatory Regulatory Transparency Disclaimer */}
      <RegulatoryDisclaimerBanner />

      {/* Radial Score Gauge */}
      <CreditScoreGauge
        score={creditworthiness_score}
        status={status}
        riskBand={risk_band}
        confidenceLabel={confidence_label}
        dataCoverage={data_coverage}
        onRecalculate={recalculate}
        isRecalculating={isRecalculating}
      />

      {/* 6 Dimension Breakdown */}
      <DimensionBreakdownCard dimensionScores={dimension_scores} />

      {/* Positive & Negative Factors */}
      <FactorInsightsCard positiveFactors={positive_factors} riskFactors={risk_factors} />

      {/* Loan Readiness & Lender Sharing Consent */}
      <LoanReadinessCard
        loanReadiness={loan_readiness}
        dtiRatio={dti_ratio}
        onShareConsent={recordShareConsent}
        isSharing={isSharing}
      />

      {/* Historical Score Progression */}
      <CreditHistoryChart history={historyList} />
    </div>
  )
}

export default Creditworthiness
