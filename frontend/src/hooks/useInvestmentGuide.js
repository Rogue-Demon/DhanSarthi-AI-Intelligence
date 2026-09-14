import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { investmentGuideApi } from '@/services/investmentGuideApi'

export const useMarketOverview = () => {
  return useQuery({
    queryKey: ['investment-guide', 'market-overview'],
    queryFn: () => investmentGuideApi.getMarketOverview(),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 120 * 1000,
  })
}

export const useInvestmentOpportunities = (filters = {}) => {
  return useQuery({
    queryKey: ['investment-guide', 'opportunities', filters],
    queryFn: () => investmentGuideApi.getOpportunities(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useTopOpportunities = (limit = 6) => {
  return useQuery({
    queryKey: ['investment-guide', 'top-opportunities', limit],
    queryFn: () => investmentGuideApi.getTopOpportunities(limit),
    staleTime: 5 * 60 * 1000,
  })
}

export const useOpportunityDetails = (symbol) => {
  return useQuery({
    queryKey: ['investment-guide', 'opportunity', symbol],
    queryFn: () => investmentGuideApi.getOpportunityDetails(symbol),
    enabled: Boolean(symbol),
  })
}

export const useAssetAnalysis = (symbol) => {
  return useQuery({
    queryKey: ['investment-guide', 'indicators', symbol],
    queryFn: () => investmentGuideApi.getIndicators(symbol),
    enabled: Boolean(symbol),
  })
}

export const useGenerateInvestmentPlan = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (planPayload) => investmentGuideApi.generatePlan(planPayload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investment-guide', 'portfolio-analysis'] })
    },
  })
}

export const usePortfolioGuideAnalysis = () => {
  return useQuery({
    queryKey: ['investment-guide', 'portfolio-analysis'],
    queryFn: () => investmentGuideApi.getPortfolioAnalysis(),
    staleTime: 2 * 60 * 1000,
  })
}

export const useMarketStatus = () => {
  return useQuery({
    queryKey: ['investment-guide', 'market-status'],
    queryFn: () => investmentGuideApi.getMarketStatus(),
    staleTime: 5 * 60 * 1000,
  })
}
