const isBrowserProduction =
  typeof window !== 'undefined' &&
  window.location.hostname !== 'localhost' &&
  window.location.hostname !== '127.0.0.1'

const customApiUrl = import.meta.env.VITE_API_BASE_URL

const getApiBaseUrl = () => {
  if (isBrowserProduction) {
    if (
      customApiUrl &&
      !customApiUrl.includes('localhost') &&
      !customApiUrl.includes('127.0.0.1')
    ) {
      return customApiUrl
    }
    return 'https://dhansarthi-remastered.onrender.com/api/v1'
  }
  return customApiUrl || 'http://localhost:8000/api/v1'
}

export const envConfig = {
  apiBaseUrl: getApiBaseUrl(),
  mode: import.meta.env.MODE || 'development',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD || isBrowserProduction,
}

export default envConfig
