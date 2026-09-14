import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function BusinessPayrollWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const totalExp = parseFloat(dashboardData?.summary?.total_expenses || 0)
  const expenseCategories = dashboardData?.cash_flow?.expense_by_category || {}
  const salaryExp = parseFloat(
    expenseCategories['SALARY'] || expenseCategories['PAYROLL'] || totalExp || 0
  )

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Corporate payroll and historical activity events')}
      onRefresh={() => console.log('Payroll refresh')}
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
              Active Monthly Payroll & OPEX
            </span>
            <span className="text-3xl font-extrabold text-text-primary tracking-tight mt-1.5">
              ₹{salaryExp.toLocaleString('en-IN')}
            </span>
            <span className="text-xs text-text-secondary mt-1 font-medium">
              {salaryExp > 0 ? 'Recorded expense outflows' : 'No payroll expenses recorded'}
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-primary/10 border-primary/15 text-primary py-0.5 px-2 rounded"
          >
            {salaryExp > 0 ? 'Active' : 'No Data'}
          </Badge>
        </div>

        {/* Corporate Activity Breakdown */}
        <div className="flex flex-col gap-3">
          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Expenses Breakdown
          </span>

          <div className="flex flex-col gap-2">
            {Object.keys(expenseCategories).length > 0 ? (
              Object.entries(expenseCategories).map(([cat, val]) => (
                <div
                  key={cat}
                  className="flex justify-between items-center text-xs p-2 bg-muted/20 rounded-lg border border-border/50"
                >
                  <span className="font-semibold text-text-secondary capitalize">
                    {cat.replace(/_/g, ' ').toLowerCase()}
                  </span>
                  <span className="font-bold text-text-primary">
                    ₹{parseFloat(val).toLocaleString('en-IN')}
                  </span>
                </div>
              ))
            ) : (
              <span className="text-xs font-medium text-text-muted text-center py-4">
                No corporate expenses logged yet.
              </span>
            )}
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default BusinessPayrollWidget
