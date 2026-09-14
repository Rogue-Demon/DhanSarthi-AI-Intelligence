import React from 'react'
import { useCashFlow } from '@/hooks'
import { Colors } from '@/config'
import { motion, useReducedMotion } from 'framer-motion'
import { DashboardGrid } from '@/components/dashboard'
import { LineChartCard, AreaChartCard } from '@/components/charts'
import * as LucideIcons from 'lucide-react'

export function Monthly() {
  const shouldReduceMotion = useReducedMotion()
  const { data: cashFlowResp } = useCashFlow()

  const cashFlowData = cashFlowResp?.data || cashFlowResp || []

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Monthly Financial Statement
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Comprehensive monthly performance analysis, savings accumulation, and budget compliance.
        </p>
      </div>

      <DashboardGrid>
        {/* Monthly Line Trend */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          {cashFlowData.length > 0 ? (
            <LineChartCard
              title="Monthly Cash Inflow vs Outflow"
              subtitle="Income vs expense progression"
              data={cashFlowData}
              xAxisKey="month"
              dataKeys={[
                { key: 'income', color: Colors.primary, name: 'Monthly Income' },
                { key: 'expenses', color: Colors.accent, name: 'Monthly Expenses' },
              ]}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.Calendar className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Monthly Statement Data</h4>
              <p className="text-xs text-text-muted mt-1 max-w-sm">
                No monthly transaction data available yet.
              </p>
            </div>
          )}
        </div>

        {/* Monthly Savings Growth Area */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1">
          {cashFlowData.length > 0 ? (
            <AreaChartCard
              title="Monthly Savings Growth"
              subtitle="Net surplus saved per month"
              data={cashFlowData}
              xAxisKey="month"
              dataKeys={[{ key: 'savings', color: Colors.success, name: 'Net Savings' }]}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.PiggyBank className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Savings Growth</h4>
              <p className="text-xs text-text-muted mt-1 max-w-xs">
                Start saving to track monthly growth.
              </p>
            </div>
          )}
        </div>
      </DashboardGrid>
    </motion.div>
  )
}

export default Monthly
