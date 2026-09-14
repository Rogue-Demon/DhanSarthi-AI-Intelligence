import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import creditworthinessApi from '../services/api/creditworthinessApi'

export const CREDITWORTHINESS_QUERY_KEY = ['creditworthiness']
export const CREDIT_SUMMARY_QUERY_KEY = ['creditworthiness', 'summary']
export const CREDIT_COMPARISON_QUERY_KEY = ['creditworthiness', 'comparison']
export const CREDIT_HISTORY_QUERY_KEY = ['creditworthiness', 'history']

export function useCreditworthiness() {
  const queryClient = useQueryClient()

  const creditworthinessQuery = useQuery({
    queryKey: CREDITWORTHINESS_QUERY_KEY,
    queryFn: creditworthinessApi.getCreditworthiness,
    staleTime: 5 * 60 * 1000,
  })

  const summaryQuery = useQuery({
    queryKey: CREDIT_SUMMARY_QUERY_KEY,
    queryFn: creditworthinessApi.getCreditSummary,
    staleTime: 5 * 60 * 1000,
  })

  const comparisonQuery = useQuery({
    queryKey: CREDIT_COMPARISON_QUERY_KEY,
    queryFn: creditworthinessApi.getScoreComparison,
    staleTime: 5 * 60 * 1000,
  })

  const historyQuery = useQuery({
    queryKey: CREDIT_HISTORY_QUERY_KEY,
    queryFn: creditworthinessApi.getCreditHistory,
    staleTime: 10 * 60 * 1000,
  })

  const recalculateMutation = useMutation({
    mutationFn: creditworthinessApi.recalculateCreditworthiness,
    onSuccess: (data) => {
      queryClient.setQueryData(CREDITWORTHINESS_QUERY_KEY, data)
      queryClient.invalidateQueries({ queryKey: CREDIT_SUMMARY_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: CREDIT_COMPARISON_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: CREDIT_HISTORY_QUERY_KEY })
    },
  })

  const shareConsentMutation = useMutation({
    mutationFn: (recipientName) => creditworthinessApi.recordShareConsent(recipientName),
  })

  return {
    creditData: creditworthinessQuery.data,
    isLoading: creditworthinessQuery.isLoading,
    isError: creditworthinessQuery.isError,
    error: creditworthinessQuery.error,
    refetch: creditworthinessQuery.refetch,

    summaryData: summaryQuery.data,
    isSummaryLoading: summaryQuery.isLoading,

    comparisonData: comparisonQuery.data,
    isComparisonLoading: comparisonQuery.isLoading,

    historyData: historyQuery.data,
    isHistoryLoading: historyQuery.isLoading,

    recalculate: recalculateMutation.mutateAsync,
    isRecalculating: recalculateMutation.isPending,

    recordShareConsent: shareConsentMutation.mutateAsync,
    isSharing: shareConsentMutation.isPending,
  }
}

export default useCreditworthiness
