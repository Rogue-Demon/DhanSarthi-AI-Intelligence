import apiClient from './client'
import ENDPOINTS from './endpoints'

export const creditworthinessApi = {
  getCreditworthiness: async () => {
    const response = await apiClient.get(ENDPOINTS.creditworthiness.get)
    return response.data
  },

  getCreditSummary: async () => {
    const response = await apiClient.get(ENDPOINTS.creditworthiness.summary)
    return response.data
  },

  getScoreComparison: async () => {
    const response = await apiClient.get(ENDPOINTS.creditworthiness.comparison)
    return response.data
  },

  getCreditReport: async () => {
    const response = await apiClient.get(ENDPOINTS.creditworthiness.report)
    return response.data
  },

  recalculateCreditworthiness: async () => {
    const response = await apiClient.post(ENDPOINTS.creditworthiness.recalculate)
    return response.data
  },

  getCreditHistory: async () => {
    const response = await apiClient.get(ENDPOINTS.creditworthiness.history)
    return response.data
  },

  recordShareConsent: async (recipientName) => {
    const response = await apiClient.post(ENDPOINTS.creditworthiness.shareConsent, {
      recipient_name: recipientName,
    })
    return response.data
  },
}

export default creditworthinessApi
