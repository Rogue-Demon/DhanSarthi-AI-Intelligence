import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  useMarketOverview,
  useInvestmentOpportunities,
  useGenerateInvestmentPlan,
  usePortfolioGuideAnalysis,
} from '@/hooks'

import MarketOverviewBanner from './components/MarketOverviewBanner'
import OpportunityScanner from './components/OpportunityScanner'
import PersonalizedPlanner from './components/PersonalizedPlanner'
import CompareInvestments from './components/CompareInvestments'
import PortfolioHealthCard from './components/PortfolioHealthCard'

export function InvestmentGuide() {
  const [selectedCompareAssets, setSelectedCompareAssets] = useState([])
  const [activeTab, setActiveTab] = useState('scanner') // 'scanner' | 'planner' | 'compare' | 'portfolio'

  // React Query Hooks
  const {
    data: overview,
    isLoading: isOverviewLoading,
    isError: isOverviewError,
  } = useMarketOverview()
  const { data: opportunities, isLoading: isOppLoading } = useInvestmentOpportunities()
  const { data: portfolioAnalysis, isLoading: isPortfolioLoading } = usePortfolioGuideAnalysis()
  const planMutation = useGenerateInvestmentPlan()

  const handleSelectForCompare = (asset) => {
    if (selectedCompareAssets.some((a) => a.id === asset.id)) {
      setSelectedCompareAssets(selectedCompareAssets.filter((a) => a.id !== asset.id))
    } else {
      if (selectedCompareAssets.length < 5) {
        setSelectedCompareAssets([...selectedCompareAssets, asset])
      }
    }
  }

  const handleRemoveCompareAsset = (id) => {
    setSelectedCompareAssets(selectedCompareAssets.filter((a) => a.id !== id))
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full flex flex-col gap-6"
    >
      {/* Top Banner: Market Overview */}
      <MarketOverviewBanner
        overview={overview}
        isLoading={isOverviewLoading}
        isError={isOverviewError}
      />

      {/* Main Section Navigation Bar */}
      <div className="flex items-center gap-2 border-b border-border/60 pb-3 overflow-x-auto scrollbar-none">
        <button
          onClick={() => setActiveTab('scanner')}
          className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all shrink-0 ${
            activeTab === 'scanner'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'bg-card text-text-muted hover:text-foreground hover:bg-muted'
          }`}
        >
          🎯 Opportunity Scanner
        </button>
        <button
          onClick={() => setActiveTab('planner')}
          className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all shrink-0 ${
            activeTab === 'planner'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'bg-card text-text-muted hover:text-foreground hover:bg-muted'
          }`}
        >
          ✨ Personalized Planner & Tree
        </button>
        <button
          onClick={() => setActiveTab('compare')}
          className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all shrink-0 ${
            activeTab === 'compare'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'bg-card text-text-muted hover:text-foreground hover:bg-muted'
          }`}
        >
          ⚖️ Compare ({selectedCompareAssets.length})
        </button>
        <button
          onClick={() => setActiveTab('portfolio')}
          className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all shrink-0 ${
            activeTab === 'portfolio'
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'bg-card text-text-muted hover:text-foreground hover:bg-muted'
          }`}
        >
          💓 Portfolio Health
        </button>
      </div>

      {/* Active Tab Content */}
      {activeTab === 'scanner' && (
        <OpportunityScanner
          opportunities={opportunities}
          isLoading={isOppLoading}
          onSelectForCompare={handleSelectForCompare}
          selectedCompareIds={selectedCompareAssets.map((a) => a.id)}
        />
      )}

      {activeTab === 'planner' && (
        <PersonalizedPlanner
          onGeneratePlan={(payload) => planMutation.mutate(payload)}
          planResult={planMutation.data}
          isGenerating={planMutation.isPending}
        />
      )}

      {activeTab === 'compare' && (
        <CompareInvestments
          selectedAssets={selectedCompareAssets}
          onRemoveAsset={handleRemoveCompareAsset}
          allAssets={opportunities}
        />
      )}

      {activeTab === 'portfolio' && (
        <PortfolioHealthCard analysis={portfolioAnalysis} isLoading={isPortfolioLoading} />
      )}
    </motion.div>
  )
}

export default InvestmentGuide
