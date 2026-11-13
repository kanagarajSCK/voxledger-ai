export interface CustomerSummary {
  id: string
  name: string
  phone: string | null
  address: string | null
  outstanding_balance: string
  total_credit: string
  total_payment: string
  transaction_count: number
  created_at: string
  updated_at: string
}

export interface CustomerCreate {
  name: string
  phone?: string
  address?: string
}

export interface CustomerUpdate {
  name?: string
  phone?: string
  address?: string
}

export interface CustomerListResponse {
  total: number
  items: CustomerSummary[]
  limit: number
  offset: number
}

export interface CustomerDetailResponse extends CustomerSummary {}
