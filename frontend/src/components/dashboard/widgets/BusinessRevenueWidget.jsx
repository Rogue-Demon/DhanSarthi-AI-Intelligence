import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function BusinessRevenueWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const totalIncome = parseFloat(dashboardData?.summary?.total_income || 0)
  const incomeCategories = dashboardData?.cash_flow?.income_by_category || {}

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Gross revenue pipeline overview')}
      onRefresh={() => console.log('Revenue refresh')}
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
        {/* Core metrics row */}
        <div className="flex justify-between items-start bg-muted/40 border border-border p-4 rounded-xl">
          <div className="flex flex-col text-left">
            <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Total Inflow Revenue
            </span>
            <span className="text-2xl font-extrabold text-text-primary mt-1.5">
              ₹{totalIncome.toLocaleString('en-IN')}
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-primary/10 border-primary/15 text-primary rounded py-0.5 px-2"
          >
            {totalIncome > 0 ? 'Active' : 'No Inflows'}
          </Badge>
        </div>

        {/* Revenue Categories */}
        <div className="flex flex-col gap-2">
          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Revenue Categories
          </span>
          {Object.keys(incomeCategories).length > 0 ? (
            Object.entries(incomeCategories).map(([cat, val]) => (
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
              No revenue categories recorded yet.
            </span>
          )}
        </div>
      </div>
    </WidgetContainer>
  )
}

export default BusinessRevenueWidget
