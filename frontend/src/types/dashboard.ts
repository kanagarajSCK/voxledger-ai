import { Transaction } from './transaction'

export interface DashboardSummary {
  total_customers: number
  total_outstanding_credit: string
  today_credit: string
  today_payments: string
  recent_transactions: Transaction[]
}
