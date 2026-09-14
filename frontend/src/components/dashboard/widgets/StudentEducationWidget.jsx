import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function StudentEducationWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const expenseCategories = dashboardData?.cash_flow?.expense_by_category || {}
  const eduSpend = parseFloat(expenseCategories['EDUCATION'] || 0)
  const totalExp = parseFloat(dashboardData?.summary?.total_expenses || 0)

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Education Expenses')}
      onRefresh={() => console.log('Education refresh')}
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
      <div className="flex flex-col gap-6 h-full select-none text-left">
        {/* Metrics Header */}
        <div className="flex justify-between items-center bg-info/5 border border-info/10 p-4 rounded-2xl relative overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-info/10 text-info flex items-center justify-center border border-white/40 dark:border-white/5 shadow-xs">
              <LucideIcons.GraduationCap className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                Education Spend
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight">
                ₹{eduSpend.toLocaleString('en-IN')}
              </span>
            </div>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-black bg-info/10 border-info/25 text-info rounded-full py-0.5 px-2"
          >
            {eduSpend > 0 ? 'Recorded' : 'No Data'}
          </Badge>
        </div>

        <div className="flex flex-col gap-2.5">
          <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
            Total Operational Outflows
          </h4>
          <div className="p-3 rounded-xl bg-muted/40 border border-border/80 text-xs font-semibold text-text-secondary">
            ₹{totalExp.toLocaleString('en-IN')} logged in expenses for this period.
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default StudentEducationWidget
