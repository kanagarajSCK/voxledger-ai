export interface ApiErrorDetail {
  code: string
  message: string
  details?: unknown
}

export interface ApiErrorResponse {
  success: false
  error: ApiErrorDetail
  timestamp: string
}
