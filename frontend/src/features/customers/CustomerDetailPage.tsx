import React, { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchCustomer, deleteCustomer } from '../../services/customerService'
import { fetchCustomerTransactions } from '../../services/transactionService'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { ErrorAlert } from '../../components/ui/ErrorAlert'
import { EmptyState } from '../../components/ui/EmptyState'
import { TransactionModal } from '../transactions/TransactionModal'
import { TransactionType } from '../../types/transaction'
import { ApiError } from '../../lib/api'
import {
  ArrowLeft,
  Phone,
  MapPin,
  Calendar,
  ArrowUpRight,
  ArrowDownLeft,
  Receipt,
  Trash2,
  TrendingUp,
  TrendingDown,
} from 'lucide-react'

export const CustomerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [txModal, setTxModal] = useState<{
    isOpen: boolean
    type: TransactionType
  }>({ isOpen: false, type: 'CREDIT' })
  const [deleteError, setDeleteError] = useState<string | null>(null)

  // 1. Fetch customer details
  const {
    data: customer,
    isLoading: isCustomerLoading,
    isError: isCustomerError,
    error: customerError,
    refetch: refetchCustomer,
  } = useQuery({
    queryKey: ['customer', id],
    queryFn: () => fetchCustomer(id!),
    enabled: !!id,
  })

  // 2. Fetch customer transaction history
  const {
    data: transactionsData,
    isLoading: isTxLoading,
  } = useQuery({
    queryKey: ['customer-transactions', id],
    queryFn: () => fetchCustomerTransactions(id!),
    enabled: !!id,
  })

  // 3. Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => deleteCustomer(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      navigate('/customers')
    },
    onError: (err: ApiError) => {
      setDeleteError(err.message || 'Cannot delete customer.')
    },
  })

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete customer '${customer?.name}'?`)) {
      setDeleteError(null)
      deleteMutation.mutate()
    }
  }

  if (isCustomerLoading) {
    return <LoadingSpinner size="lg" label="Loading customer ledger account..." />
  }

  if (isCustomerError || !customer) {
    return (
      <div className="space-y-4">
        <Link to="/customers">
          <Button variant="ghost" size="sm" className="gap-1.5">
            <ArrowLeft className="w-4 h-4" />
            Back to Customers
          </Button>
        </Link>
        <ErrorAlert
          title="Customer Not Found"
          message={customerError?.message || 'Could not find customer profile.'}
          onRetry={() => refetchCustomer()}
        />
      </div>
    )
  }

  const balance = parseFloat(customer.outstanding_balance)
  const isOwing = balance > 0

  return (
    <div className="space-y-6">
      {/* Back button and page actions */}
      <div className="flex items-center justify-between">
        <Link to="/customers">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
            <ArrowLeft className="w-4 h-4" />
            Back to Customer Directory
          </Button>
        </Link>

        <Button
          variant="outline"
          size="sm"
          onClick={handleDelete}
          isLoading={deleteMutation.isPending}
          className="text-xs text-red-600 hover:bg-red-50 border-red-200 gap-1.5"
        >
          <Trash2 className="w-3.5 h-3.5" />
          Delete Customer
        </Button>
      </div>

      {deleteError && (
        <ErrorAlert
          title="Cannot Delete Customer"
          message={deleteError}
        />
      )}

      {/* Customer Header Banner */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {customer.name}
            </h1>
            <Badge variant={isOwing ? 'danger' : 'success'}>
              {isOwing ? 'Payment Due' : 'Account Settled'}
            </Badge>
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-500">
            {customer.phone && (
              <span className="flex items-center gap-1 font-mono">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                {customer.phone}
              </span>
            )}
            {customer.address && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                {customer.address}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              Customer since {new Date(customer.created_at).toLocaleDateString([], { month: 'short', year: 'numeric' })}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <Button
            variant="danger"
            onClick={() => setTxModal({ isOpen: true, type: 'CREDIT' })}
            className="flex-1 md:flex-initial gap-1.5"
          >
            <ArrowUpRight className="w-4 h-4" />
            + Give Credit (उधार)
          </Button>
          <Button
            variant="primary"
            onClick={() => setTxModal({ isOpen: true, type: 'PAYMENT' })}
            className="flex-1 md:flex-initial gap-1.5"
          >
            <ArrowDownLeft className="w-4 h-4" />
            - Record Payment (जमा)
          </Button>
        </div>
      </div>

      {/* 3 Ledger Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Outstanding Balance */}
        <Card className={`border-l-4 shadow-sm ${isOwing ? 'border-l-red-500 bg-red-50/20' : 'border-l-emerald-500 bg-emerald-50/20'}`}>
          <CardContent className="p-5">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Current Outstanding Balance (बाकी)
            </span>
            <div className="mt-2">
              <span className={`text-3xl font-extrabold ${isOwing ? 'text-red-600' : 'text-emerald-600'}`}>
                ₹{balance.toFixed(2)}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              {isOwing ? 'Money owed to shopkeeper' : 'All credit settled'}
            </p>
          </CardContent>
        </Card>

        {/* Total Credit Given */}
        <Card className="shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Total Credit Given (कुल उधार)
              </span>
              <div className="w-7 h-7 rounded-md bg-amber-50 text-amber-600 flex items-center justify-center">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2">
              <span className="text-2xl font-bold text-slate-900">
                ₹{parseFloat(customer.total_credit).toFixed(2)}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              Cumulative purchases on credit
            </p>
          </CardContent>
        </Card>

        {/* Total Payment Received */}
        <Card className="shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Total Payments Received (कुल जमा)
              </span>
              <div className="w-7 h-7 rounded-md bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <TrendingDown className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2">
              <span className="text-2xl font-bold text-emerald-600">
                ₹{parseFloat(customer.total_payment).toFixed(2)}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">
              Cumulative debt settlements
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Full Transaction History Ledger */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="text-base sm:text-lg">Ledger Timeline</CardTitle>
            <p className="text-xs text-slate-500">Chronological list of all credits and payments</p>
          </div>
          {transactionsData && (
            <Badge variant="neutral">
              {transactionsData.total} Transactions
            </Badge>
          )}
        </CardHeader>
        <CardContent className="p-0">
          {isTxLoading ? (
            <LoadingSpinner size="md" label="Loading transaction history..." />
          ) : !transactionsData || transactionsData.items.length === 0 ? (
            <div className="p-6">
              <EmptyState
                icon={Receipt}
                title="No Transactions for This Customer"
                description="Use the buttons above to give goods on credit or record a cash/UPI payment."
                actionLabel="Give Credit"
                onAction={() => setTxModal({ isOpen: true, type: 'CREDIT' })}
              />
            </div>
          ) : (
            <div className="divide-y divide-slate-100 overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead className="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Description / Note</th>
                    <th className="px-4 py-3">Date & Time</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transactionsData.items.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-4 py-3">
                        <Badge
                          variant={tx.type === 'CREDIT' ? 'danger' : 'success'}
                          className="text-[10px]"
                        >
                          {tx.type === 'CREDIT' ? 'CREDIT (+ Udhar)' : 'PAYMENT (- Jama)'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-700">
                        {tx.description || <span className="text-slate-400 italic">No description</span>}
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs font-mono">
                        {new Date(tx.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })},{' '}
                        {new Date(tx.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="neutral" className="text-[10px]">
                          {tx.status}
                        </Badge>
                      </td>
                      <td
                        className={`px-4 py-3 text-right font-extrabold text-sm ${
                          tx.type === 'CREDIT' ? 'text-red-600' : 'text-emerald-600'
                        }`}
                      >
                        {tx.type === 'CREDIT' ? '+' : '-'}₹{parseFloat(tx.amount).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Transaction Modal */}
      <TransactionModal
        isOpen={txModal.isOpen}
        onClose={() => setTxModal({ ...txModal, isOpen: false })}
        customerId={customer.id}
        customerName={customer.name}
        currentBalance={customer.outstanding_balance}
        initialType={txModal.type}
      />
    </div>
  )
}
