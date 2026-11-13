import { ApiErrorResponse } from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ApiError extends Error {
  code: string
  details?: unknown
  status: number

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('http')
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`

  const headers = new Headers(options.headers || {})
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json')
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorData: ApiErrorResponse | null = null
    try {
      errorData = await response.json()
    } catch {
      // response wasn't JSON
    }

    if (errorData?.error) {
      throw new ApiError(
        response.status,
        errorData.error.code,
        errorData.error.message,
        errorData.error.details
      )
    }

    throw new ApiError(
      response.status,
      'HTTP_ERROR',
      `Request failed with status ${response.status}: ${response.statusText}`
    )
  }

  return response.json() as Promise<T>
}

export { API_BASE_URL }
