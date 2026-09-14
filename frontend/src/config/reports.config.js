import { PROFILES } from '@/constants'

/**
 * Reusable Reports & Analytics Configuration
 *
 * Centralizes design tokens and helper functions for rendering
 * real user metrics dynamically fetched from PostgreSQL.
 */

// Colors matching Claymorphism Design Tokens
export const Colors = {
  primary: '#7C3AED',
  secondary: '#8B5CF6',
  accent: '#EC4899',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#3B82F6',
  muted: '#94A3B8',
}

// Default empty datasets structure for Recharts
export const mockDatasets = {
  incomeVsExpenses: [],
  expenseCategories: [],
  dailySpending: [],
  weeklyPerformance: [],
  annualGrowth: [],
  assetAllocation: [],
  investmentGrowth: [],
  goalsAnalytics: [],
}

export const getReportsConfig = (profileName, dashboardData = null) => {
  const summary = dashboardData?.summary || {
    total_income: 0,
    total_expenses: 0,
    savings: 0,
    net_worth: 0,
    total_assets: 0,
    total_liabilities: 0,
  }

  const formatVal = (v) => '₹' + parseFloat(v || 0).toLocaleString('en-IN')

  const focusMetrics = [
    {
      title: 'Gross Income',
      value: formatVal(summary.total_income),
      change: summary.total_income > 0 ? 'Recorded' : 'No Data',
      status: 'Inflow',
      icon: 'Briefcase',
    },
    {
      title: 'Total Expenses',
      value: formatVal(summary.total_expenses),
      change: summary.total_expenses > 0 ? 'Recorded' : 'No Data',
      status: 'Outflow',
      icon: 'CreditCard',
    },
    {
      title: 'Net Savings',
      value: formatVal(summary.savings),
      change: summary.savings >= 0 ? 'Surplus' : 'Deficit',
      status: 'Savings',
      icon: 'PiggyBank',
    },
    {
      title: 'Net Worth',
      value: formatVal(summary.net_worth),
      change: summary.net_worth !== 0 ? 'Active' : 'No Data',
      status: 'Balance',
      icon: 'Gem',
    },
  ]

  const highlights = []
  if (summary.total_income > 0) {
    highlights.push({
      text: `Total income recorded: ${formatVal(summary.total_income)}`,
      type: 'positive',
    })
  }
  if (summary.total_expenses > 0) {
    highlights.push({
      text: `Total expenses recorded: ${formatVal(summary.total_expenses)}`,
      type: 'neutral',
    })
  }
  if (highlights.length === 0) {
    highlights.push({
      text: 'No transaction data entered yet. Add income & expenses to view AI insights.',
      type: 'neutral',
    })
  }

  return { focusMetrics, highlights }
}

export default getReportsConfig
