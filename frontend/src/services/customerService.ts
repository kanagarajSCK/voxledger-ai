import { apiClient } from '../lib/api'
import {
  CustomerCreate,
  CustomerDetailResponse,
  CustomerListResponse,
  CustomerSummary,
  CustomerUpdate,
} from '../types/customer'

export async function fetchCustomers(
  search?: string,
  limit = 50,
  offset = 0
): Promise<CustomerListResponse> {
  const params = new URLSearchParams()
  if (search && search.trim()) params.append('search', search.trim())
  params.append('limit', limit.toString())
  params.append('offset', offset.toString())

  return apiClient<CustomerListResponse>(`/api/v1/customers?${params.toString()}`)
}

export async function fetchCustomer(id: string): Promise<CustomerDetailResponse> {
  return apiClient<CustomerDetailResponse>(`/api/v1/customers/${id}`)
}

export async function createCustomer(data: CustomerCreate): Promise<CustomerSummary> {
  return apiClient<CustomerSummary>('/api/v1/customers', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateCustomer(
  id: string,
  data: CustomerUpdate
): Promise<CustomerSummary> {
  return apiClient<CustomerSummary>(`/api/v1/customers/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function deleteCustomer(id: string): Promise<void> {
  return apiClient<void>(`/api/v1/customers/${id}`, {
    method: 'DELETE',
  })
}
