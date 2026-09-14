import React from 'react'
import { useBudgets, useExpenses } from '@/hooks'
import { Colors } from '@/config'
import { motion, useReducedMotion } from 'framer-motion'
import { DashboardGrid } from '@/components/dashboard'
import { ComposedChartCard, DonutChartCard } from '@/components/charts'
import * as LucideIcons from 'lucide-react'

export function Weekly() {
  const shouldReduceMotion = useReducedMotion()
  const { data: budgetsResp } = useBudgets()
  const { data: expensesResp } = useExpenses()

  const budgetsData = budgetsResp?.data || budgetsResp?.items || budgetsResp || []
  const expensesData = expensesResp?.data || expensesResp?.items || expensesResp || []

  const budgetsArray = Array.isArray(budgetsData) ? budgetsData : []
  const expensesArray = Array.isArray(expensesData) ? expensesData : []

  const hasWeeklyData = budgetsArray.length > 0 || expensesArray.length > 0

  // Compute expense categories dynamically
  const expenseCategoryMap = {}
  expensesArray.forEach((e) => {
    const cat = e.category || 'General'
    expenseCategoryMap[cat] = (expenseCategoryMap[cat] || 0) + Math.abs(e.amount || 0)
  })
  const categoryData = Object.entries(expenseCategoryMap).map(([name, value]) => ({ name, value }))

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Weekly Performance Reports
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Compare week-over-week spending efficiency, savings margins, and budget limits.
        </p>
      </div>

      <DashboardGrid>
        {/* Composed Chart: Budget vs Spent vs Savings */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          {hasWeeklyData ? (
            <ComposedChartCard
              title="Weekly Budget vs Actual Expenditure"
              subtitle="Comparing budget caps against actual logged debits"
              data={budgetsArray.map((b, idx) => ({
                week: b.category || `Budget #${idx + 1}`,
                spent: b.spent_amount || 0,
                saved: Math.max((b.amount || 0) - (b.spent_amount || 0), 0),
                budget: b.amount || 0,
              }))}
              xAxisKey="week"
              barKeys={[
                { key: 'spent', color: Colors.primary, name: 'Spent' },
                { key: 'saved', color: Colors.success, name: 'Saved' },
              ]}
              lineKeys={[{ key: 'budget', color: Colors.accent, name: 'Budget Cap' }]}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.BarChart3 className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Weekly Performance Data</h4>
              <p className="text-xs text-text-muted mt-1 max-w-sm">
                No budget targets or expenses logged for weekly comparison.
              </p>
            </div>
          )}
        </div>

        {/* Weekly Category Breakdown */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1">
          {categoryData.length > 0 ? (
            <DonutChartCard
              title="Weekly Category Breakdown"
              subtitle="Distribution of weekly debits"
              data={categoryData}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.PieChart className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Category Breakdown</h4>
              <p className="text-xs text-text-muted mt-1 max-w-xs">
                No expense categories available.
              </p>
            </div>
          )}
        </div>
      </DashboardGrid>
    </motion.div>
  )
}

export default Weekly
