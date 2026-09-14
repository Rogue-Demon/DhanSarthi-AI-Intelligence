import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function StudentBudgetWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const totalIncome = parseFloat(dashboardData?.summary?.total_income || 0)
  const totalExpenses = parseFloat(dashboardData?.summary?.total_expenses || 0)
  const remaining = totalIncome - totalExpenses
  const percentSpent =
    totalIncome > 0 ? Math.min(100, Math.round((totalExpenses / totalIncome) * 100)) : 0

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Budget Planning')}
      onRefresh={() => console.log('Budget refresh')}
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
        {/* Metrics Row: Allowance vs Spent vs Remaining */}
        <div className="grid grid-cols-3 gap-4 bg-muted/30 border border-border p-4.5 rounded-2xl">
          <div className="flex flex-col text-left">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider leading-none">
              Allowance
            </span>
            <span className="text-lg font-black text-text-primary mt-1.5">
              ₹{totalIncome.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex flex-col text-left border-x border-border/80 px-4">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider leading-none">
              Spent
            </span>
            <span className="text-lg font-black text-primary mt-1.5">
              ₹{totalExpenses.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex flex-col text-left pl-2">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider leading-none">
              Remaining
            </span>
            <span className="text-lg font-black text-success mt-1.5">
              ₹{remaining.toLocaleString('en-IN')}
            </span>
          </div>
        </div>

        {/* Progress visualizer strip */}
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between items-center text-[10px] font-black text-text-muted uppercase tracking-wider">
            <span>Monthly Budget Spending</span>
            <span className="text-primary font-black">{percentSpent}% spent</span>
          </div>
          <div className="w-full bg-muted h-3 rounded-full overflow-hidden border border-white/60 shadow-inner relative">
            <div
              className="bg-gradient-primary h-full rounded-full transition-all duration-500 shadow-button"
              style={{ width: `${percentSpent}%` }}
            />
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default StudentBudgetWidget
