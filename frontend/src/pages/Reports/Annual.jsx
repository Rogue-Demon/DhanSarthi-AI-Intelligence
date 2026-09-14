import React from 'react'
import { useCashFlow, useDashboardData } from '@/hooks'
import { Colors } from '@/config'
import { motion, useReducedMotion } from 'framer-motion'
import { DashboardGrid } from '@/components/dashboard'
import { AreaChartCard } from '@/components/charts'
import * as LucideIcons from 'lucide-react'

export function Annual() {
  const shouldReduceMotion = useReducedMotion()
  const { data: cashFlowResp } = useCashFlow()
  const { data: dashboardResp } = useDashboardData()

  const cashFlowData = cashFlowResp?.data || cashFlowResp || []
  const dashboardData = dashboardResp?.data || dashboardResp || {}

  const totalIncome = dashboardData?.summary?.totalIncome ?? 0
  const totalSavings = dashboardData?.summary?.totalSavings ?? dashboardData?.summary?.netWorth ?? 0

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Annual Performance & Growth
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Multi-year revenue, net worth growth trajectories, and financial milestone
          accomplishments.
        </p>
      </div>

      <DashboardGrid>
        {/* 5-Year Net Worth Area Chart */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          {cashFlowData.length > 0 ? (
            <AreaChartCard
              title="Net Worth Progression"
              subtitle="Historical performance based on database records"
              data={cashFlowData}
              xAxisKey="month"
              dataKeys={[
                { key: 'netWorth', color: Colors.primary, name: 'Net Worth Value' },
                { key: 'income', color: Colors.success, name: 'Annual Income' },
              ]}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.TrendingUp className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Multi-Year History</h4>
              <p className="text-xs text-text-muted mt-1 max-w-sm">
                No historical financial records accumulated yet.
              </p>
            </div>
          )}
        </div>

        {/* Milestones Card */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left h-full">
            <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
              Annual Milestones
            </h4>

            <div className="flex flex-col gap-3">
              {totalIncome > 0 || totalSavings > 0 ? (
                <div className="p-3 rounded-xl bg-muted/30 border border-border/60 flex items-start gap-3">
                  <div className="p-2 rounded-lg text-white shrink-0 bg-emerald-500">
                    <LucideIcons.Trophy className="h-4 w-4" />
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[10px] font-black text-text-muted">CURRENT YEAR</span>
                    <span className="text-xs font-bold text-text-primary">
                      Total Savings: ₹{totalSavings.toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center text-center p-6 text-text-muted">
                  <LucideIcons.Award className="h-8 w-8 mb-2 opacity-40" />
                  <span className="text-xs font-semibold">No Milestones Recorded</span>
                  <span className="text-[11px] opacity-75 mt-0.5">
                    Save your first milestone to view progress.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </DashboardGrid>
    </motion.div>
  )
}

export default Annual
