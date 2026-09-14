import React from 'react'
import { useTransactions, useDashboardData } from '@/hooks'
import { Colors } from '@/config'
import { motion, useReducedMotion } from 'framer-motion'
import { DashboardGrid } from '@/components/dashboard'
import { BarChartCard } from '@/components/charts'
import * as LucideIcons from 'lucide-react'

export function Daily() {
  const shouldReduceMotion = useReducedMotion()
  const { data: txResp } = useTransactions({ page_size: 10 })
  const { data: dashboardResp } = useDashboardData()

  const transactionsData = txResp?.data || txResp?.items || txResp || []
  const dashboardData = dashboardResp?.data || dashboardResp || {}

  const totalIncome = dashboardData?.summary?.totalIncome ?? 0
  const totalExpenses = dashboardData?.summary?.totalExpenses ?? 0
  const netSurplus = totalIncome - totalExpenses

  const transactionList = Array.isArray(transactionsData) ? transactionsData : []

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Daily Transactions & Spending
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Analyze day-to-day inbound income credits and outbound spending debits.
        </p>
      </div>

      <DashboardGrid>
        {/* Daily Spending Bar Chart */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          {transactionList.length > 0 ? (
            <BarChartCard
              title="Expenditure Log"
              subtitle="Daily debits vs credits"
              data={transactionList.map((t) => ({
                day: t.date
                  ? new Date(t.date).toLocaleDateString('en-IN', { weekday: 'short' })
                  : 'Today',
                expense:
                  t.type === 'expense' || t.transaction_type === 'expense' ? Math.abs(t.amount) : 0,
                income:
                  t.type === 'income' || t.transaction_type === 'income' ? Math.abs(t.amount) : 0,
              }))}
              xAxisKey="day"
              dataKeys={[
                { key: 'expense', color: Colors.danger, name: 'Daily Expense' },
                { key: 'income', color: Colors.success, name: 'Daily Income' },
              ]}
              height={280}
            />
          ) : (
            <div className="clay-surface bg-card p-6 border border-border/60 rounded-2xl flex flex-col items-center justify-center text-center h-[280px]">
              <LucideIcons.BarChart2 className="h-10 w-10 text-text-muted mb-2 opacity-40" />
              <h4 className="text-sm font-bold text-text-primary">No Expenditure Activity</h4>
              <p className="text-xs text-text-muted mt-1 max-w-sm">
                No daily spending recorded yet for this period.
              </p>
            </div>
          )}
        </div>

        {/* Daily Summary Card */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1 flex flex-col gap-4">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left h-full">
            <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
              Recorded Totals
            </h4>

            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center text-xs font-semibold p-3 rounded-xl bg-muted/30 border border-border/60">
                <span className="text-text-secondary">Total Income</span>
                <span className="font-extrabold text-success">
                  +₹{totalIncome.toLocaleString('en-IN')}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs font-semibold p-3 rounded-xl bg-muted/30 border border-border/60">
                <span className="text-text-secondary">Total Expense</span>
                <span className="font-extrabold text-danger">
                  -₹{totalExpenses.toLocaleString('en-IN')}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs font-semibold p-3 rounded-xl bg-primary/10 border border-primary/20">
                <span className="text-primary font-black">Net Surplus</span>
                <span className="font-extrabold text-primary">
                  ₹{netSurplus.toLocaleString('en-IN')}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Daily Transactions Table */}
        <div className="lg:col-span-12 col-span-1">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left">
            <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
              Recent Transactions Log
            </h4>

            {transactionList.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-border/60 text-text-muted uppercase text-[9px] font-black tracking-wider">
                      <th className="pb-3 px-2">Description</th>
                      <th className="pb-3 px-2">Category</th>
                      <th className="pb-3 px-2">Date</th>
                      <th className="pb-3 px-2 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40 font-semibold">
                    {transactionList.map((t, idx) => {
                      const isIncome = t.type === 'income' || t.transaction_type === 'income'
                      return (
                        <tr key={t.id || idx} className="hover:bg-muted/30 transition-colors">
                          <td className="py-3 px-2 text-text-primary font-bold">
                            {t.description || t.title || 'Transaction'}
                          </td>
                          <td className="py-3 px-2 text-text-muted">{t.category || 'General'}</td>
                          <td className="py-3 px-2 text-text-muted">
                            {t.date ? new Date(t.date).toLocaleDateString('en-IN') : 'N/A'}
                          </td>
                          <td
                            className={`py-3 px-2 text-right font-black ${isIncome ? 'text-success' : 'text-danger'}`}
                          >
                            {isIncome ? '+' : '-'}₹{Math.abs(t.amount).toLocaleString('en-IN')}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-center p-8 text-text-muted">
                <LucideIcons.Receipt className="h-10 w-10 mb-2 opacity-30" />
                <span className="text-xs font-bold text-text-secondary">
                  No Recent Transactions Logged
                </span>
                <span className="text-[11px] opacity-75 mt-1">
                  Your transaction history will appear here once you log incomes or expenses.
                </span>
              </div>
            )}
          </div>
        </div>
      </DashboardGrid>
    </motion.div>
  )
}

export default Daily
