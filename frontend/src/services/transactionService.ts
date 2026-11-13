import { apiClient } from '../lib/api'
import {
  Transaction,
  TransactionCreate,
  TransactionListResponse,
  TransactionType,
} from '../types/transaction'

export async function fetchTransactions(
  type?: TransactionType,
  limit = 50,
  offset = 0
): Promise<TransactionListResponse> {
  const params = new URLSearchParams()
  if (type) params.append('type', type)
  params.append('limit', limit.toString())
  params.append('offset', offset.toString())

  return apiClient<TransactionListResponse>(`/api/v1/transactions?${params.toString()}`)
}

export async function fetchCustomerTransactions(
  customerId: string,
  limit = 50,
  offset = 0
): Promise<TransactionListResponse> {
  const params = new URLSearchParams()
  params.append('limit', limit.toString())
  params.append('offset', offset.toString())

  return apiClient<TransactionListResponse>(
    `/api/v1/customers/${customerId}/transactions?${params.toString()}`
  )
}

export async function createTransaction(data: TransactionCreate): Promise<Transaction> {
  return apiClient<Transaction>('/api/v1/transactions', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
