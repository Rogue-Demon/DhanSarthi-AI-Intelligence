import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function ProfessionalAssetsWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const goalsList = dashboardData?.goals?.goals || []

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Long-term savings goals and payment events')}
      onRefresh={() => console.log('Assets/goals refresh')}
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
        {/* COLUMN 1: GOALS & PROGRESS */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Long-term Financial Goals
            </span>
          </div>

          {/* Goal progress cards */}
          <div className="flex flex-col gap-3">
            {goalsList.length > 0 ? (
              goalsList.map((goal) => {
                const pct = Math.min(100, Math.round(parseFloat(goal.completion_percentage || 0)))
                const current = parseFloat(goal.current_amount || 0)
                const target = parseFloat(goal.target_amount || 0)

                return (
                  <div
                    key={goal.id}
                    className="clay-surface bg-card border border-border/80 p-3.5 flex flex-col gap-2.5 shadow-card"
                  >
                    <div className="flex items-center justify-between text-xs font-bold text-text-primary">
                      <span className="truncate max-w-[150px] sm:max-w-xs">{goal.name}</span>
                      <span className="text-[10px] font-black text-text-muted">{pct}%</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-muted h-2.5 rounded-full overflow-hidden border border-white/60 shadow-inner relative">
                        <div
                          className="h-full rounded-full bg-primary transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>

                    <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase tracking-wider">
                      <span>Saved: ₹{current.toLocaleString()}</span>
                      <span>Target: ₹{target.toLocaleString()}</span>
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="text-xs text-text-muted text-center py-4 font-medium">
                No financial goals created yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default ProfessionalAssetsWidget
