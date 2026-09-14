import React from 'react'
import { Badge, Button } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function BusinessInventoryWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const totalAssetVal = parseFloat(dashboardData?.summary?.total_assets || 0)
  const goalsList = dashboardData?.goals?.goals || []

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Corporate inventory assets and expansion goals')}
      onRefresh={() => console.log('Inventory refresh')}
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
        {/* COLUMN 1: INVENTORY & STOCK VALUATION (50% width) */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Warehouse Stock Valuation
            </span>
            <Badge
              variant="secondary"
              className="text-[8px] font-bold py-0.5 px-1.5 bg-success/10 border-success/20 text-success rounded"
            >
              {totalAssetVal > 0 ? 'Active Assets' : 'No Assets'}
            </Badge>
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs font-semibold text-text-secondary bg-muted/30 p-2.5 rounded-lg border border-border/50">
              <span>Total Inventory Asset Value</span>
              <span className="font-extrabold text-text-primary">
                ₹{totalAssetVal.toLocaleString('en-IN')}
              </span>
            </div>
            <div className="flex justify-between items-center text-xs font-semibold text-text-secondary bg-muted/30 p-2.5 rounded-lg border border-border/50">
              <span>Inventory Status</span>
              <span className="font-extrabold text-text-primary">
                {totalAssetVal > 0 ? 'Recorded' : '0 recorded'}
              </span>
            </div>
          </div>
        </div>

        {/* COLUMN 2: CORPORATE GOALS & TARGETS (50% width) */}
        <div className="flex-1 border-t lg:border-t-0 lg:border-l border-border/60 pt-4 lg:pt-0 lg:pl-6 flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Corporate Goals & Targets
            </span>
          </div>

          {/* Goal progress cards list */}
          <div className="flex flex-col gap-3">
            {goalsList.length > 0 ? (
              goalsList.map((goal) => {
                const pct = Math.min(100, Math.round(parseFloat(goal.completion_percentage || 0)))
                return (
                  <div key={goal.id} className="flex flex-col gap-1 text-xs">
                    <div className="flex justify-between font-bold text-text-primary">
                      <span className="truncate max-w-[140px]">{goal.name}</span>
                      <span className="text-[10px] font-black text-text-muted">{pct}%</span>
                    </div>
                    <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden border border-white/60 shadow-inner">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="text-xs text-text-muted py-3 text-center font-medium">
                No corporate goals recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default BusinessInventoryWidget
