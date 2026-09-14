import React from 'react'
import { useProfile, useDashboardData, useCashFlow } from '@/hooks'
import { getReportsConfig, Colors } from '@/config'
import { motion, useReducedMotion } from 'framer-motion'
import { DashboardGrid } from '@/components/dashboard'
import { AreaChartCard, DonutChartCard, BarChartCard, MiniTrendChart } from '@/components/charts'
import * as LucideIcons from 'lucide-react'
import { Badge } from '@/components/ui'

export function Overview() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()
  const { data: dashboardResp } = useDashboardData()
  const { data: cashFlowResp } = useCashFlow()

  const dashboardData = dashboardResp?.data || dashboardResp || {}
  const cashFlowData = cashFlowResp?.data || cashFlowResp || []
  const reportsData = getReportsConfig(profile)

  const totalIncome = dashboardData?.summary?.totalIncome ?? 0
  const totalExpenses = dashboardData?.summary?.totalExpenses ?? 0
  const netSurplus = dashboardData?.summary?.netSurplus ?? totalIncome - totalExpenses
  const totalSavings = dashboardData?.summary?.totalSavings ?? dashboardData?.summary?.netWorth ?? 0

  const focusMetrics = [
    {
      title: 'Total Income',
      value: `₹${totalIncome.toLocaleString('en-IN')}`,
      status: totalIncome > 0 ? 'Active' : 'No entries',
      icon: 'TrendingUp',
      change: totalIncome > 0 ? 'Live' : '₹0',
    },
    {
      title: 'Total Expenses',
      value: `₹${totalExpenses.toLocaleString('en-IN')}`,
      status: totalExpenses > 0 ? 'Active' : 'No entries',
      icon: 'ShoppingBag',
      change: totalExpenses > 0 ? 'Live' : '₹0',
    },
    {
      title: 'Net Surplus',
      value: `₹${netSurplus.toLocaleString('en-IN')}`,
      status: netSurplus !== 0 ? 'Active' : 'Balanced',
      icon: 'PiggyBank',
      change: netSurplus >= 0 ? '+Surplus' : '-Deficit',
    },
    {
      title: 'Total Net Worth',
      value: `₹${totalSavings.toLocaleString('en-IN')}`,
      status: totalSavings > 0 ? 'Growth' : 'Initial',
      icon: 'ShieldCheck',
      change: 'Current',
    },
  ]

  // Dynamic expense categories from breakdown or empty
  const expenseCategoriesData = dashboardData?.breakdown?.expensesByCategory
    ? Object.entries(dashboardData.breakdown.expensesByCategory).map(([name, value]) => ({
        name,
        value,
      }))
    : []

  const hasData = totalIncome > 0 || totalExpenses > 0 || cashFlowData.length > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left"
    >
      {/* Executive KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {focusMetrics.map((metric, idx) => {
          const Icon = LucideIcons[metric.icon] || LucideIcons.Activity

          return (
            <motion.div
              key={metric.title}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="clay-surface bg-card p-4 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-3 select-none text-left"
            >
              <div className="flex flex-col gap-1">
                <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                  {metric.title}
                </span>
                <span className="text-xl font-black text-text-primary tracking-tight">
                  {metric.value}
                </span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Badge
                    variant="secondary"
                    className="text-[8px] font-bold py-0.5 px-1 bg-success/10 text-success border-success/15 rounded"
                  >
                    {metric.change}
                  </Badge>
                  <span className="text-[9px] font-bold text-text-muted">{metric.status}</span>
                </div>
              </div>

              <div className="flex flex-col items-end gap-2">
                <div className="p-2 rounded-xl bg-primary/10 text-primary shrink-0">
                  <Icon className="h-4 w-4" />
                </div>
                {/* Mini Sparkline Chart */}
                <MiniTrendChart
                  data={hasData ? [0, totalIncome, totalExpenses, netSurplus] : [0, 0, 0, 0]}
                  color={Colors.primary}
                  width={60}
                  height={24}
                />
              </div>
            </motion.div>
          )
        })}
      </div>

      <DashboardGrid>
        {/* Main Income vs Expense Area Chart */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          {cashFlowData.length > 0 ? (
            <AreaChartCard
              title="Income vs Expenses Trends"
              subtitle="Monthly inbound credits vs outbound expenditures"
              data={cashFlowData}
              xAxisKey="month"
              dataKeys={[
                { key: 'income', color: Colors.primary, name: 'Income' },
                { key: 'expenses', color: Colors.accent, name: 'Expenses' },
              ]}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.BarChart3 className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Cash Flow Data</h4>
              <p className="text-xs text-text-muted mt-1 max-w-sm">
                Add your income and expense transactions to see live historical trends here.
              </p>
            </div>
          )}
        </div>

        {/* Expense Category Donut Chart */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1">
          {expenseCategoriesData.length > 0 ? (
            <DonutChartCard
              title="Expense Allocations"
              subtitle="Breakdown by operational category"
              data={expenseCategoriesData}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.PieChart className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Expense Allocations</h4>
              <p className="text-xs text-text-muted mt-1 max-w-xs">
                No expense categories logged yet.
              </p>
            </div>
          )}
        </div>

        {/* AI Highlights Panel */}
        <div className="lg:col-span-12 col-span-1 flex flex-col gap-4">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left h-full">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
                AI Executive Highlights
              </h4>
              <LucideIcons.Sparkles className="h-4 w-4 text-accent" />
            </div>

            <div className="flex flex-col gap-3">
              {hasData ? (
                <div className="p-3 rounded-xl bg-primary/5 border border-primary/10 flex items-start gap-3">
                  <LucideIcons.CheckCircle2 className="h-4 w-4 text-success shrink-0 mt-0.5" />
                  <p className="text-xs font-semibold text-text-secondary leading-relaxed">
                    Total recorded income is ₹{totalIncome.toLocaleString('en-IN')} with total
                    expenses of ₹{totalExpenses.toLocaleString('en-IN')}. Net surplus is ₹
                    {netSurplus.toLocaleString('en-IN')}.
                  </p>
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-muted/20 border border-border/60 flex items-start gap-3">
                  <LucideIcons.Info className="h-4 w-4 text-text-muted shrink-0 mt-0.5" />
                  <p className="text-xs font-semibold text-text-secondary leading-relaxed">
                    Welcome! Your financial profile is completely fresh. Add your first income,
                    expense, or savings goal to generate personalized AI executive insights.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </DashboardGrid>
    </motion.div>
  )
}

export default Overview
