import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function StudentSavingsWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const totalSavings = dashboardData?.summary?.totalSavings ?? dashboardData?.summary?.netWorth ?? 0
  const savingRate =
    dashboardData?.summary?.totalIncome > 0
      ? Math.round((totalSavings / dashboardData.summary.totalIncome) * 100)
      : 0

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Savings Goals')}
      onRefresh={() => console.log('Savings refresh')}
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
        <div className="flex justify-between items-center bg-accent/5 border border-accent/10 p-4 rounded-2xl relative overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-accent/10 text-accent flex items-center justify-center border border-white/40 dark:border-white/5 shadow-xs">
              <LucideIcons.PiggyBank className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                Total Savings
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight">
                ₹{totalSavings.toLocaleString('en-IN')}
              </span>
            </div>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-black bg-accent/10 border-accent/25 text-accent rounded-full py-0.5 px-2"
          >
            {savingRate > 0 ? `+${savingRate}% saving rate` : '0% saving rate'}
          </Badge>
        </div>

        {/* Savings Streak Widget Section */}
        <div className="clay-surface bg-muted/20 border border-border p-4 rounded-2xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-warning/15 flex items-center justify-center text-warning shadow-sm border border-white/50 relative">
              <LucideIcons.Flame className="h-6 w-6 stroke-[2.2] animate-pulse" />
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[8px] font-black text-white">
                🔥
              </span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-black text-text-primary leading-none">
                  {totalSavings > 0 ? 'Active Saver' : '0-Day Streak'}
                </span>
                <Badge
                  variant="secondary"
                  className="text-[8px] font-black uppercase tracking-wider py-0 px-1 bg-warning/10 text-warning border-warning/15"
                >
                  Saver Streak
                </Badge>
              </div>
              <span className="text-[11px] font-bold text-text-secondary mt-1">
                {totalSavings > 0
                  ? 'Keep up your savings habit!'
                  : 'Start adding savings to build your streak.'}
              </span>
            </div>
          </div>

          {/* Streak Stats */}
          <div className="flex flex-col text-right shrink-0">
            <span className="text-[9px] font-black text-text-muted uppercase tracking-wider leading-none">
              Longest
            </span>
            <span className="text-sm font-black text-text-secondary">
              {totalSavings > 0 ? '1 Day' : '0 Days'}
            </span>
          </div>
        </div>

        {/* Savings Growth History */}
        <div className="flex flex-col gap-2.5 border-t border-border/50 pt-4 mt-auto">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
              Savings Growth History
            </h4>
            <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">
              Current Status
            </span>
          </div>

          <div className="h-20 w-full rounded-2xl bg-card border border-border/70 relative flex items-center justify-center px-4 py-2 overflow-hidden">
            {totalSavings > 0 ? (
              <div className="flex items-center gap-2 text-xs font-bold text-emerald-600 dark:text-emerald-400">
                <LucideIcons.TrendingUp className="h-4 w-4" />
                <span>Savings accumulated: ₹{totalSavings.toLocaleString('en-IN')}</span>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-center">
                <LucideIcons.PiggyBank className="h-5 w-5 text-text-muted mb-1 opacity-50" />
                <span className="text-[11px] text-text-muted">No savings history recorded yet</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default StudentSavingsWidget
