export type TransactionType = 'CREDIT' | 'PAYMENT'
export type TransactionStatus = 'COMPLETED' | 'REVERSED'

export interface Transaction {
  id: string
  customer_id: string
  customer_name?: string
  amount: string
  type: TransactionType
  status: TransactionStatus
  description: string | null
  voice_raw_text: string | null
  idempotency_key: string | null
  created_at: string
  updated_at: string
}

export interface TransactionCreate {
  customer_id: string
  amount: number | string
  type: TransactionType
  description?: string
  voice_raw_text?: string
  idempotency_key?: string
}

export interface TransactionListResponse {
  total: number
  items: Transaction[]
  limit: number
  offset: number
}
