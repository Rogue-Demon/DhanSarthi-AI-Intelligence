import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function ProfessionalInvestmentsWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const totalInvested = parseFloat(dashboardData?.investments?.total_invested || 0)
  const currentValue = parseFloat(dashboardData?.investments?.current_value || totalInvested)
  const allocation = dashboardData?.investments?.allocation_by_type || {}
  const allocationEntries = Object.entries(allocation)

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Investment portfolio allocation and tax liabilities')}
      onRefresh={() => console.log('Investments refresh')}
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
      <div className="flex flex-col lg:flex-row gap-6 w-full select-none text-left font-sans">
        {/* COLUMN 1: PORTFOLIO ALLOCATION */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Portfolio Assets Valuation
            </span>
            <div className="flex items-baseline gap-2.5 mt-1.5">
              <span className="text-2xl font-extrabold text-text-primary tracking-tight">
                ₹{currentValue.toLocaleString('en-IN')}
              </span>
              <Badge
                variant="secondary"
                className="text-[10px] font-bold bg-primary/10 border-primary/20 text-primary py-0.5 px-2 rounded"
              >
                {currentValue > 0 ? 'Active Portfolio' : 'No Investments'}
              </Badge>
            </div>
          </div>

          {/* Allocation details list */}
          <div className="flex flex-col gap-2.5">
            <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Asset Allocation Mappings
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {allocationEntries.length > 0 ? (
                allocationEntries.map(([type, val]) => (
                  <div
                    key={type}
                    className="flex items-center justify-between p-2 rounded-lg bg-muted/40 border border-border/80 text-xs font-semibold text-text-secondary"
                  >
                    <span className="truncate capitalize">
                      {type.replace(/_/g, ' ').toLowerCase()}
                    </span>
                    <span className="font-extrabold text-text-primary">
                      ₹{parseFloat(val).toLocaleString('en-IN')}
                    </span>
                  </div>
                ))
              ) : (
                <div className="col-span-2 text-xs text-text-muted py-3 text-center font-medium">
                  No investments recorded yet.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default ProfessionalInvestmentsWidget
