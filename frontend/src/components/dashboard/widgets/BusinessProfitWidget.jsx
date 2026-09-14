import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function BusinessProfitWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const totalIncome = parseFloat(dashboardData?.summary?.total_income || 0)
  const totalExpenses = parseFloat(dashboardData?.summary?.total_expenses || 0)
  const netProfit = totalIncome - totalExpenses
  const marginPct = totalIncome > 0 ? Math.round((netProfit / totalIncome) * 100) : 0

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Operating margins and business health status')}
      onRefresh={() => console.log('Profit refresh')}
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
        {/* Core Metric & Margin Info */}
        <div className="flex justify-between items-start">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Net Profit Margin (Surplus)
            </span>
            <span className="text-3xl font-extrabold text-text-primary tracking-tight mt-1.5">
              ₹{netProfit.toLocaleString('en-IN')}
            </span>
            <span className="text-xs text-text-secondary mt-1 font-medium">
              {totalIncome > 0 ? `${marginPct}% net profit ratio` : 'No revenue recorded yet'}
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-primary/10 border-primary/20 text-primary py-0.5 px-2 rounded"
          >
            {netProfit >= 0 ? 'Surplus' : 'Deficit'}
          </Badge>
        </div>

        {/* Business Health Summary */}
        <div className="flex items-center gap-4 bg-muted/30 border border-border/80 p-3.5 rounded-xl">
          <div className="flex flex-col text-left">
            <span className="text-xs font-extrabold text-text-primary leading-none">
              Net Financial Position
            </span>
            <span className="text-[10px] font-bold text-text-muted mt-1 leading-tight">
              {totalIncome > 0 || totalExpenses > 0
                ? `Income: ₹${totalIncome.toLocaleString('en-IN')} | Expenses: ₹${totalExpenses.toLocaleString('en-IN')}`
                : 'No financial transactions logged yet.'}
            </span>
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default BusinessProfitWidget
