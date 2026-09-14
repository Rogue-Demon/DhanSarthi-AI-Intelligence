import { STORAGE_KEYS } from '@/constants'

export const requestInterceptor = (options) => {
  const token = localStorage.getItem(STORAGE_KEYS.AUTH)
  const headers = { ...options.headers }

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    let parsedToken
    try {
      parsedToken = JSON.parse(token)
    } catch {
      parsedToken = token
    }
    headers['Authorization'] = `Bearer ${parsedToken}`
  }

  return {
    ...options,
    headers,
  }
}

export const responseInterceptor = async (response) => {
  if (response.status === 401) {
    localStorage.removeItem(STORAGE_KEYS.AUTH)
    console.warn('Unauthorized request! Session expired.')
  }
  return response
}

export default {
  request: requestInterceptor,
  response: responseInterceptor,
}
