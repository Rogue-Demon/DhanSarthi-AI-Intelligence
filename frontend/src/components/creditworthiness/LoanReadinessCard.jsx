import React, { useState } from 'react'
import { ShieldAlert, CheckCircle, Clock, AlertOctagon, Share2, FileText } from 'lucide-react'

export function LoanReadinessCard({ loanReadiness, dtiRatio, onShareConsent, isSharing }) {
  const [recipient, setRecipient] = useState('')
  const [shareSuccessMsg, setShareSuccessMsg] = useState('')

  const getReadinessConfig = (state) => {
    switch (state) {
      case 'READY':
        return {
          title: 'Loan Ready',
          badge: 'High Financial Readiness',
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10 border-emerald-500/30',
          icon: CheckCircle,
          desc: 'Your cash flow surplus, income stability, and low DTI ratio indicate strong credit readiness for supplementary loan applications.',
        }
      case 'NEARLY_READY':
        return {
          title: 'Nearly Loan Ready',
          badge: 'Favourable Health',
          color: 'text-teal-400',
          bg: 'bg-teal-500/10 border-teal-500/30',
          icon: Clock,
          desc: 'Favourable financial health indicators. Minor debt optimization or building an additional month of savings will strengthen your profile.',
        }
      case 'BUILD_HISTORY':
        return {
          title: 'Build History Needed',
          badge: 'Data History Building',
          color: 'text-amber-400',
          bg: 'bg-amber-500/10 border-amber-500/30',
          icon: Clock,
          desc: 'Your financial parameters are sound, but additional months of active tracking inside DhanSarthi are needed before sharing.',
        }
      case 'HIGH_RISK':
        return {
          title: 'High Financial Risk',
          badge: 'Leverage Warning',
          color: 'text-rose-400',
          bg: 'bg-rose-500/10 border-rose-500/30',
          icon: AlertOctagon,
          desc: 'Elevated debt-to-income ratio or tight cash flow. Reducing existing monthly EMI commitments is recommended.',
        }
      default:
        return {
          title: 'Insufficient Data',
          badge: 'History Pending',
          color: 'text-slate-400',
          bg: 'bg-slate-500/10 border-slate-500/30',
          icon: ShieldAlert,
          desc: 'Add more income, expense, or asset records inside DhanSarthi to unlock your loan readiness assessment.',
        }
    }
  }

  const config = getReadinessConfig(loanReadiness)
  const IconComponent = config.icon

  const handleShareSubmit = async (e) => {
    e.preventDefault()
    if (!recipient.trim()) return

    try {
      const res = await onShareConsent(recipient.trim())
      setShareSuccessMsg(res.message || `Consent recorded for ${recipient}.`)
      setRecipient('')
    } catch (err) {
      console.error('Failed to record consent:', err)
    }
  }

  return (
    <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl border ${config.bg} ${config.color}`}>
            <IconComponent className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">
              Loan Readiness Indicator
            </h3>
            <p className="text-xs text-slate-400">
              Internal supplementary credit readiness assessment
            </p>
          </div>
        </div>
        <span
          className={`text-xs font-semibold px-3 py-1 rounded-full border ${config.bg} ${config.color}`}
        >
          {config.badge}
        </span>
      </div>

      <div className="space-y-4">
        <p className="text-sm text-slate-300 leading-relaxed">{config.desc}</p>

        {dtiRatio !== null && dtiRatio !== undefined && (
          <div className="bg-slate-950/60 border border-slate-800 p-3.5 rounded-xl flex items-center justify-between text-xs">
            <span className="text-slate-400">Debt-to-Income (DTI) Obligation:</span>
            <span className="font-bold text-slate-200">{(dtiRatio * 100).toFixed(1)}%</span>
          </div>
        )}
      </div>

      {/* Sharing Consent Section */}
      <div className="border-t border-slate-800/80 pt-4 space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
          <Share2 className="w-4 h-4 text-emerald-400" />
          <span>Prepare Shareable Financial Credit Profile</span>
        </div>
        <p className="text-xs text-slate-400">
          Generate a user-consented, secure summary report to share with prospective lenders as
          supplementary financial proof.
        </p>

        {shareSuccessMsg ? (
          <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs p-3 rounded-xl flex items-center justify-between">
            <span>{shareSuccessMsg}</span>
            <button
              onClick={() => setShareSuccessMsg('')}
              className="text-xs underline text-emerald-400 ml-2"
            >
              Close
            </button>
          </div>
        ) : (
          <form onSubmit={handleShareSubmit} className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. HDFC Bank / SBI Lender"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              disabled={isSharing || !recipient.trim()}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shrink-0"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Grant Consent</span>
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

export default LoanReadinessCard
