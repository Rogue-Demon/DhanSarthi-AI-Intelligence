import { apiClient, ENDPOINTS } from '@/services/api'

export const investmentGuideApi = {
  getMarketOverview: async () => {
    return await apiClient.get(ENDPOINTS.investmentGuide.marketOverview)
  },

  getOpportunities: async (params = {}) => {
    return await apiClient.get(ENDPOINTS.investmentGuide.opportunities, { params })
  },

  getOpportunityDetails: async (symbol) => {
    return await apiClient.get(ENDPOINTS.investmentGuide.opportunityDetails(symbol))
  },

  getTopOpportunities: async (limit = 6) => {
    return await apiClient.get(ENDPOINTS.investmentGuide.topOpportunities, { params: { limit } })
  },

  getAssetsUniverse: async () => {
    return await apiClient.get(ENDPOINTS.investmentGuide.assets)
  },

  getIndicators: async (symbol) => {
    return await apiClient.get(ENDPOINTS.investmentGuide.indicators(symbol))
  },

  generatePlan: async (planPayload) => {
    return await apiClient.post(ENDPOINTS.investmentGuide.plan, planPayload)
  },

  getPortfolioAnalysis: async () => {
    return await apiClient.get(ENDPOINTS.investmentGuide.portfolioAnalysis)
  },

  getMarketStatus: async () => {
    return await apiClient.get(ENDPOINTS.investmentGuide.marketStatus)
  },
}

export default investmentGuideApi
