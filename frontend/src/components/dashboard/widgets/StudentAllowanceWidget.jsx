import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function StudentAllowanceWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const totalIncome = parseFloat(dashboardData?.summary?.total_income || 0)

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Allowance Tracking')}
      onRefresh={() => console.log('Allowance refresh')}
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
        {/* Metrics Row */}
        <div className="flex justify-between items-center bg-primary/5 border border-primary/10 p-4 rounded-2xl relative overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center border border-white/40 dark:border-white/5 shadow-xs">
              <LucideIcons.Wallet className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                Allowance Account
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight">
                ₹{totalIncome.toLocaleString('en-IN')}
              </span>
            </div>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-black bg-primary/10 border-primary/20 text-primary rounded-full py-0.5 px-2"
          >
            {totalIncome > 0 ? 'Active' : 'No Inflows'}
          </Badge>
        </div>

        {/* Activity Status */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <LucideIcons.History className="h-4 w-4 text-text-muted" />
            <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
              Allowance Status
            </h4>
          </div>

          <div className="text-xs font-semibold text-text-secondary bg-muted/30 p-3 rounded-xl border border-border/50">
            {totalIncome > 0
              ? `Total monthly allowance / stipend logged: ₹${totalIncome.toLocaleString('en-IN')}`
              : 'No allowance or stipend logged for this period.'}
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default StudentAllowanceWidget
