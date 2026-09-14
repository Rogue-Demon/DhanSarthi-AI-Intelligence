import { useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { Sparkles, Sliders, ShieldCheck, RefreshCw } from 'lucide-react'
import InvestmentTree from './InvestmentTree'

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899']

export default function PersonalizedPlanner({ onGeneratePlan, planResult, isGenerating }) {
  const [amount, setAmount] = useState('100000')
  const [monthlySip, setMonthlySip] = useState('10000')
  const [riskProfile, setRiskProfile] = useState('moderate')
  const [horizon, setHorizon] = useState('3-5')
  const [financialGoal, setFinancialGoal] = useState('Wealth Accumulation')
  const [emergencyStatus, setEmergencyStatus] = useState('adequate')
  const [preferredAssets, setPreferredAssets] = useState([])

  const ALL_PREFERRED_ASSETS = [
    'Stocks',
    'Mutual Funds',
    'ETFs',
    'Gold',
    'Silver',
    'Bonds',
    'T-Bills',
    'FD',
    'RD',
    'PPF',
    'NPS',
    'Crypto',
  ]

  const togglePreferredAsset = (asset) => {
    if (preferredAssets.includes(asset)) {
      setPreferredAssets(preferredAssets.filter((a) => a !== asset))
    } else {
      setPreferredAssets([...preferredAssets, asset])
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onGeneratePlan({
      amount: Number(amount) || 100000,
      monthly_sip: Number(monthlySip) || 0,
      risk_profile: riskProfile,
      horizon: horizon,
      financial_goal: financialGoal,
      emergency_reserve_status: emergencyStatus,
      preferred_assets: preferredAssets,
    })
  }

  const pieData = planResult?.allocation_breakdown
    ? Object.entries(planResult.allocation_breakdown).map(([name, value]) => ({
        name,
        value: Number(value),
      }))
    : []

  return (
    <div className="w-full bg-card border border-border/80 rounded-2xl p-5 md:p-6 shadow-sm flex flex-col gap-6">
      {/* Header */}
      <div className="border-b border-border/60 pb-4">
        <h3 className="text-lg font-bold text-foreground tracking-tight flex items-center gap-2">
          ✨ Personalized Investment Planner
        </h3>
        <p className="text-xs text-text-muted">
          Generate an intelligent asset allocation and dynamic strategy tree tailored to your
          financial goals
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Column */}
        <form
          onSubmit={handleSubmit}
          className="lg:col-span-5 bg-background border border-border/80 rounded-2xl p-5 flex flex-col gap-4"
        >
          <div className="flex items-center justify-between pb-2 border-b border-border/50">
            <span className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="h-4 w-4 text-primary" /> Strategy Parameters
            </span>
          </div>

          {/* Amount */}
          <div>
            <label className="text-xs font-semibold text-text-muted block mb-1">
              Lump Sum Capital (₹)
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-muted/40 border border-border/60 rounded-xl text-xs text-foreground font-mono focus:outline-none focus:border-primary"
              placeholder="e.g. 100000"
              required
            />
          </div>

          {/* Monthly SIP */}
          <div>
            <label className="text-xs font-semibold text-text-muted block mb-1">
              Monthly SIP Target (₹)
            </label>
            <input
              type="number"
              value={monthlySip}
              onChange={(e) => setMonthlySip(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-muted/40 border border-border/60 rounded-xl text-xs text-foreground font-mono focus:outline-none focus:border-primary"
              placeholder="e.g. 10000"
            />
          </div>

          {/* Risk Profile */}
          <div>
            <label className="text-xs font-semibold text-text-muted block mb-1">Risk Profile</label>
            <div className="grid grid-cols-3 gap-2">
              {['conservative', 'moderate', 'aggressive'].map((r) => (
                <button
                  type="button"
                  key={r}
                  onClick={() => setRiskProfile(r)}
                  className={`py-2 rounded-xl text-xs font-bold capitalize border transition-all ${
                    riskProfile === r
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-muted/40 text-text-muted border-border/60 hover:bg-muted'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Financial Goal */}
          <div>
            <label className="text-xs font-semibold text-text-muted block mb-1">
              Financial Target Goal
            </label>
            <select
              value={financialGoal}
              onChange={(e) => setFinancialGoal(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-muted/40 border border-border/60 rounded-xl text-xs text-foreground focus:outline-none focus:border-primary"
            >
              <option value="Wealth Accumulation">Wealth Accumulation</option>
              <option value="Retirement Fund">Retirement Corpus</option>
              <option value="Home Purchase">Home Purchase / Real Estate</option>
              <option value="Higher Education">Higher Education Fund</option>
              <option value="Tax Saving & Yield">Tax Saving & Sovereign Yield</option>
            </select>
          </div>

          {/* Investment Horizon */}
          <div>
            <label className="text-xs font-semibold text-text-muted block mb-1">
              Investment Horizon
            </label>
            <select
              value={horizon}
              onChange={(e) => setHorizon(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-muted/40 border border-border/60 rounded-xl text-xs text-foreground focus:outline-none focus:border-primary"
            >
              <option value="<1">&lt; 1 Year (Short Duration)</option>
              <option value="1-3">1 – 3 Years (Medium Duration)</option>
              <option value="3-5">3 – 5 Years (Balanced Accumulation)</option>
              <option value="5+">5+ Years (Long Term Growth)</option>
            </select>
          </div>

          {/* Emergency Reserve */}
          <div>
            <label className="text-xs font-semibold text-text-muted block mb-1">
              Emergency Fund Status
            </label>
            <select
              value={emergencyStatus}
              onChange={(e) => setEmergencyStatus(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-muted/40 border border-border/60 rounded-xl text-xs text-foreground focus:outline-none focus:border-primary"
            >
              <option value="adequate">Adequate (6+ Months Covered)</option>
              <option value="partial">Partial (3-5 Months Covered)</option>
              <option value="none">None (Build Buffer First)</option>
            </select>
          </div>

          {/* Preferred Assets (Optional) */}
          <div>
            <label className="text-xs font-semibold text-text-muted block mb-1">
              Preferred Asset Focus (Optional)
            </label>
            <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
              {ALL_PREFERRED_ASSETS.map((asset) => {
                const isSelected = preferredAssets.includes(asset)
                return (
                  <button
                    type="button"
                    key={asset}
                    onClick={() => togglePreferredAsset(asset)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border transition-all ${
                      isSelected
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-muted/40 text-text-muted border-border/60 hover:text-foreground hover:bg-muted'
                    }`}
                  >
                    {isSelected ? `✓ ${asset}` : `+ ${asset}`}
                  </button>
                )
              })}
            </div>
          </div>

          <button
            type="submit"
            disabled={isGenerating}
            className="mt-2 w-full py-3 bg-primary text-primary-foreground font-black text-xs uppercase tracking-wider rounded-xl hover:opacity-90 transition-all flex items-center justify-center gap-2 shadow-md"
          >
            {isGenerating ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {isGenerating ? 'Computing Strategy...' : 'Generate Personalized Plan'}
          </button>
        </form>

        {/* Results Column */}
        <div className="lg:col-span-7 flex flex-col gap-5">
          {planResult ? (
            <>
              {/* Allocation Chart Card */}
              <div className="bg-background border border-border/80 rounded-2xl p-5 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm">
                <div className="w-full md:w-1/2 h-52">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(val) => [`${val}%`, 'Allocation']}
                        contentStyle={{
                          backgroundColor: '#18181b',
                          borderColor: '#27272a',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="w-full md:w-1/2 flex flex-col gap-2 text-xs">
                  <h4 className="font-bold text-foreground mb-1 border-b border-border/60 pb-1">
                    Recommended Asset Mix ({planResult.risk_profile})
                  </h4>
                  {pieData.map((item, idx) => (
                    <div key={item.name} className="flex items-center justify-between font-medium">
                      <span className="flex items-center gap-2 text-text-muted">
                        <span
                          className="h-2.5 w-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                        />
                        {item.name}
                      </span>
                      <span className="font-bold font-mono text-foreground">{item.value}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Dynamic Investment Tree Component */}
              <InvestmentTree treeData={planResult.tree_data} />
            </>
          ) : (
            <div className="h-full min-h-[300px] bg-background/50 border border-dashed border-border/80 rounded-2xl p-8 flex flex-col items-center justify-center text-center gap-3">
              <div className="p-4 rounded-full bg-primary/10 text-primary">
                <Sparkles className="h-8 w-8" />
              </div>
              <h4 className="font-bold text-foreground">Ready to Build Your Strategy</h4>
              <p className="text-xs text-text-muted max-w-sm">
                Fill in your capital, risk tolerance, and horizon to generate a data-backed asset
                allocation tree.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Safety Notice Banner */}
      <div className="p-3 bg-muted/40 rounded-xl text-[11px] text-text-muted flex items-center gap-2 border border-border/40">
        <ShieldCheck className="h-4 w-4 text-primary shrink-0" />
        <span>
          <strong>Financial Safety Notice:</strong> All investment allocations are calculated via
          quantitative optimization. Past market performance does not guarantee future results.
        </span>
      </div>
    </div>
  )
}
