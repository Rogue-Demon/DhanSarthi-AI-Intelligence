import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function StudentGoalsWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const goalsList = dashboardData?.goals?.goals || []

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Goal tracking')}
      onRefresh={() => console.log('Goals refresh')}
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
      <div className="flex flex-col gap-6 w-full select-none text-left">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <LucideIcons.Target className="h-4.5 w-4.5 text-primary" />
            <h4 className="text-sm font-extrabold text-text-primary uppercase tracking-wider">
              Active Goals
            </h4>
          </div>

          <div className="flex flex-col gap-3">
            {goalsList.length > 0 ? (
              goalsList.map((goal) => {
                const progressPct = Math.min(
                  100,
                  Math.round(parseFloat(goal.completion_percentage || 0))
                )
                const current = parseFloat(goal.current_amount || 0)
                const target = parseFloat(goal.target_amount || 0)
                const remaining = Math.max(0, target - current)

                return (
                  <div
                    key={goal.id}
                    className="clay-surface bg-card border border-white/60 dark:border-white/5 p-4 flex flex-col gap-2 shadow-card"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-black text-text-primary">{goal.name}</span>
                      <span className="text-[10px] font-black text-text-muted">{progressPct}%</span>
                    </div>

                    <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden mt-1">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${progressPct}%` }}
                      />
                    </div>

                    <div className="flex justify-between items-center text-[10px] font-bold text-text-muted mt-1">
                      <span>
                        Saved: ₹{current.toLocaleString()} / Target: ₹{target.toLocaleString()}
                      </span>
                      <span>Remaining: ₹{remaining.toLocaleString()}</span>
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="text-xs text-text-muted py-4 text-center font-medium">
                No active savings goals recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default StudentGoalsWidget
