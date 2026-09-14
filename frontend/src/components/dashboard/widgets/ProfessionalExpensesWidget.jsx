import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import { useTransactions } from '@/hooks'
import { cn } from '@/utils'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function ProfessionalExpensesWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()
  const totalExpenses = parseFloat(dashboardData?.summary?.total_expenses || 0)
  const totalBudget = parseFloat(dashboardData?.budgets?.total_budget || 0)
  const percentSpent = totalBudget > 0 ? Math.round((totalExpenses / totalBudget) * 100) : 0

  const expenseCategories = dashboardData?.cash_flow?.expense_by_category || {}
  const categoriesList = Object.entries(expenseCategories)

  // Fetch the single most recent transaction dynamically
  const { data: txData } = useTransactions({ page: 1, page_size: 1 })
  const recentTx = txData?.items?.[0]

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Expense details and monthly bill cycles')}
      onRefresh={() => console.log('Expenses refresh')}
    />
  )

  return (
    <WidgetContainer
      title={widget.title}
      icon={widget.icon}
      color={widget.color}
      sizeClass={sizeClass}
      toolbar={toolbar}
    >
      <div className="flex flex-col gap-5 h-full select-none text-left font-sans">
        {/* Core Metric */}
        <div className="flex justify-between items-start">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Accumulated Monthly Expenses
            </span>
            <span className="text-3xl font-extrabold text-text-primary tracking-tight mt-1.5">
              ₹{totalExpenses.toLocaleString('en-IN')}
            </span>
            <span className="text-xs text-text-secondary mt-1 font-medium">
              {totalBudget > 0
                ? `${percentSpent}% of total monthly budget spent`
                : 'No budget target set'}
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-danger/10 border-danger/15 text-danger py-0.5 px-2 rounded"
          >
            {totalExpenses > 0 ? 'Active Outflows' : 'No Outflows'}
          </Badge>
        </div>

        {/* Expense Categories Breakdown */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Expenses by Category
          </span>

          <div className="flex flex-col gap-2">
            {categoriesList.length > 0 ? (
              categoriesList.map(([cat, val], idx) => (
                <div
                  key={cat}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40 border border-border/80 text-xs font-semibold text-text-secondary"
                >
                  <span className="font-extrabold text-text-primary capitalize">
                    {cat.replace(/_/g, ' ').toLowerCase()}
                  </span>
                  <span className="font-extrabold text-text-primary">
                    ₹{parseFloat(val).toLocaleString('en-IN')}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-xs font-medium text-text-muted py-3 text-center">
                No monthly expenses recorded yet.
              </div>
            )}
          </div>
        </div>

        {/* Recent Transactions List */}
        <div className="flex flex-col gap-2 mt-auto border-t border-border/40 pt-4">
          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Recent Activity Log
          </span>
          {recentTx ? (
            <div className="flex justify-between items-center text-xs">
              <div className="flex items-center gap-2">
                <div className="p-1 rounded bg-muted text-text-muted">
                  <LucideIcons.ArrowDownLeft className="h-3.5 w-3.5 text-danger" />
                </div>
                <span className="font-bold text-text-secondary truncate max-w-[150px]">
                  {recentTx.description || recentTx.category}
                </span>
              </div>
              <span
                className={cn(
                  'font-extrabold',
                  recentTx.transaction_type === 'INCOME' ? 'text-success' : 'text-text-primary'
                )}
              >
                {recentTx.transaction_type === 'INCOME' ? '+' : '-'}₹
                {parseFloat(recentTx.amount).toLocaleString('en-IN')}
              </span>
            </div>
          ) : (
            <span className="text-xs font-bold text-text-muted">
              No recent transactions recorded.
            </span>
          )}
        </div>
      </div>
    </WidgetContainer>
  )
}

export default ProfessionalExpensesWidget
