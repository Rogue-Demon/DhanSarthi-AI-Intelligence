import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function BusinessCashFlowWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const totalIncome = parseFloat(dashboardData?.summary?.total_income || 0)
  const totalExpenses = parseFloat(dashboardData?.summary?.total_expenses || 0)
  const netFlow = parseFloat(dashboardData?.cash_flow?.net_cash_flow || totalIncome - totalExpenses)

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Corporate liquidity cash flow details')}
      onRefresh={() => console.log('Cash flow refresh')}
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
      <div className="flex flex-col lg:flex-row gap-8 w-full select-none text-left font-sans">
        {/* COLUMN 1: STATEMENT METRICS */}
        <div className="flex-1 lg:flex-[1.2] flex flex-col gap-4">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Net cash flow statement
            </span>
            <div className="flex items-baseline gap-2 mt-1.5">
              <span className="text-2xl font-extrabold text-text-primary tracking-tight">
                {netFlow >= 0 ? '+' : ''}₹{netFlow.toLocaleString('en-IN')}
              </span>
              <Badge
                variant="secondary"
                className={`text-[8px] font-bold py-0.5 px-1.5 rounded ml-2 ${netFlow >= 0 ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}
              >
                {netFlow >= 0 ? 'Positive flow' : 'Deficit flow'}
              </Badge>
            </div>
          </div>

          <div className="flex flex-col gap-2.5 bg-muted/40 border border-border p-3.5 rounded-xl text-xs font-semibold text-text-secondary">
            <div className="flex justify-between">
              <span>Money In (Inflow)</span>
              <span className="font-extrabold text-success">
                ₹{totalIncome.toLocaleString('en-IN')}
              </span>
            </div>
            <div className="flex justify-between border-t border-border/40 pt-2.5">
              <span>Money Out (Outflow)</span>
              <span className="font-extrabold text-danger">
                ₹{totalExpenses.toLocaleString('en-IN')}
              </span>
            </div>
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default BusinessCashFlowWidget
