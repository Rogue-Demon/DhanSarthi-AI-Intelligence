const customApiUrl = import.meta.env.VITE_API_BASE_URL

const getApiBaseUrl = () => {
  return customApiUrl || 'http://127.0.0.1:8000/api/v1'
}

export const envConfig = {
  apiBaseUrl: getApiBaseUrl(),
  mode: import.meta.env.MODE || 'development',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
}

export default envConfig
