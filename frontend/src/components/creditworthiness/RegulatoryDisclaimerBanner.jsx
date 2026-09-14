import React from 'react'
import { ShieldCheck, Info } from 'lucide-react'

export function RegulatoryDisclaimerBanner() {
  return (
    <div className="bg-slate-900/80 backdrop-blur-md border border-amber-500/30 rounded-xl p-4 shadow-lg text-slate-300 text-sm">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg shrink-0 mt-0.5">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <div className="flex items-center gap-2 font-semibold text-amber-300">
            <span>Product & Regulatory Transparency</span>
            <span className="text-xs bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full border border-amber-500/40">
              DhanSarthi Internal Assessment
            </span>
          </div>
          <p className="text-xs leading-relaxed text-slate-300">
            The <strong>DhanSarthi Creditworthiness Score (DCS)</strong> is an internal, explainable
            assessment of financial health calculated deterministically from your verified financial
            data inside DhanSarthi. It is{' '}
            <strong>
              NOT an official credit bureau score (such as CIBIL, Experian, or Equifax)
            </strong>{' '}
            and does not guarantee loan approval.
          </p>
        </div>
      </div>
    </div>
  )
}

export default RegulatoryDisclaimerBanner
