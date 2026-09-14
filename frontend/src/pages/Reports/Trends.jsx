import React from 'react'
import { useAssets, useInvestments } from '@/hooks'
import { Colors } from '@/config'
import { motion, useReducedMotion } from 'framer-motion'
import { DashboardGrid } from '@/components/dashboard'
import { RadarChartCard, AreaChartCard } from '@/components/charts'
import * as LucideIcons from 'lucide-react'

export function Trends() {
  const shouldReduceMotion = useReducedMotion()
  const { data: assetsResp } = useAssets()
  const { data: investmentsResp } = useInvestments()

  const assetsData = assetsResp?.data || assetsResp?.items || assetsResp || []
  const investmentsData = investmentsResp?.data || investmentsResp?.items || investmentsResp || []

  const assetsArray = Array.isArray(assetsData) ? assetsData : []
  const investmentsArray = Array.isArray(investmentsData) ? investmentsData : []

  const hasInvestments = investmentsArray.length > 0 || assetsArray.length > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Trend & Risk Analytics
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Multi-dimensional asset allocation radar and investment growth benchmarking.
        </p>
      </div>

      <DashboardGrid>
        {/* Radar Allocation Dimension */}
        <div className="lg:col-span-6 md:col-span-2 col-span-1">
          {assetsArray.length > 0 ? (
            <RadarChartCard
              title="Portfolio Asset Distribution Radar"
              subtitle="Evaluating asset weights across logged asset classes"
              data={assetsArray.map((a) => ({
                subject: a.name || a.asset_type || 'Asset',
                A: a.value || a.amount || 0,
              }))}
              dataKey="A"
              subjectKey="subject"
              color={Colors.primary}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.Compass className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Asset Allocation Radar</h4>
              <p className="text-xs text-text-muted mt-1 max-w-xs">
                Log your assets to see risk distribution.
              </p>
            </div>
          )}
        </div>

        {/* Investment Growth vs Benchmark */}
        <div className="lg:col-span-6 md:col-span-2 col-span-1">
          {investmentsArray.length > 0 ? (
            <AreaChartCard
              title="Portfolio Progression"
              subtitle="Logged investments value tracking"
              data={investmentsArray.map((inv, idx) => ({
                period: inv.name || `Inv #${idx + 1}`,
                portfolio: inv.current_value || inv.amount || 0,
                benchmark: (inv.current_value || inv.amount || 0) * 0.9,
              }))}
              xAxisKey="period"
              dataKeys={[
                { key: 'portfolio', color: Colors.success, name: 'Portfolio Value' },
                { key: 'benchmark', color: Colors.muted, name: 'Estimated Benchmark' },
              ]}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.TrendingUp className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Investment Analytics</h4>
              <p className="text-xs text-text-muted mt-1 max-w-xs">
                No active investments recorded yet.
              </p>
            </div>
          )}
        </div>
      </DashboardGrid>
    </motion.div>
  )
}

export default Trends
