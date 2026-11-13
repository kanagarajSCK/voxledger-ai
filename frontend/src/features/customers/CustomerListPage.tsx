import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchCustomers } from '../../services/customerService'
import { CustomerSummary } from '../../types/customer'
import { Card, CardContent } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { ErrorAlert } from '../../components/ui/ErrorAlert'
import { EmptyState } from '../../components/ui/EmptyState'
import { AddCustomerModal } from './AddCustomerModal'
import { TransactionModal } from '../transactions/TransactionModal'
import {
  Users,
  Search,
  UserPlus,
  ArrowUpRight,
  ArrowDownLeft,
  ChevronRight,
  Phone,
  MapPin,
} from 'lucide-react'

export const CustomerListPage: React.FC = () => {
  const [search, setSearch] = useState('')
  const [isAddCustomerOpen, setIsAddCustomerOpen] = useState(false)
  const [txModalCustomer, setTxModalCustomer] = useState<{
    customer: CustomerSummary
    type: 'CREDIT' | 'PAYMENT'
  } | null>(null)

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['customers', search],
    queryFn: () => fetchCustomers(search),
    staleTime: 3000,
  })

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Customer Accounts (ग्राहक सूची)
            </h1>
            {data && (
              <Badge variant="neutral" className="font-mono">
                {data.total}
              </Badge>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Manage kirana customer credit ledgers, balances and transaction histories.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsAddCustomerOpen(true)}
          className="gap-2 w-full sm:w-auto"
        >
          <UserPlus className="w-4 h-4" />
          Add Customer
        </Button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search customers by name or phone number..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full h-11 pl-10 pr-4 rounded-xl border border-slate-300 bg-white text-sm text-slate-900 shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
        />
      </div>

      {isLoading && (
        <LoadingSpinner size="lg" label="Loading customer ledger directory..." />
      )}

      {isError && (
        <ErrorAlert
          title="Could Not Load Customer List"
          message={error?.message || 'Failed to fetch customers.'}
          onRetry={() => refetch()}
        />
      )}

      {data && (
        <>
          {data.items.length === 0 ? (
            <EmptyState
              icon={Users}
              title={search ? 'No Matching Customers Found' : 'No Customers Yet'}
              description={
                search
                  ? `No customer matches '${search}'. Check spelling or register as a new customer.`
                  : 'Start by adding your first customer to track their credit and payments.'
              }
              actionLabel="Add Customer"
              onAction={() => setIsAddCustomerOpen(true)}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.items.map((cust) => {
                const balance = parseFloat(cust.outstanding_balance)
                const isOwing = balance > 0

                return (
                  <Card key={cust.id} className="hover:border-slate-300 transition-all flex flex-col justify-between">
                    <CardContent className="p-4 sm:p-5 space-y-3">
                      {/* Name & Phone */}
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <Link
                            to={`/customers/${cust.id}`}
                            className="text-base font-bold text-slate-900 hover:text-emerald-600 transition-colors flex items-center gap-1.5"
                          >
                            {cust.name}
                            <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" />
                          </Link>
                          {cust.phone ? (
                            <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5 font-mono">
                              <Phone className="w-3 h-3 text-slate-400" />
                              {cust.phone}
                            </p>
                          ) : (
                            <p className="text-xs text-slate-400 italic mt-0.5">No phone number</p>
                          )}
                        </div>

                        {/* Balance Badge */}
                        <div className="text-right">
                          <span
                            className={`text-lg font-extrabold ${
                              isOwing ? 'text-red-600' : 'text-emerald-600'
                            }`}
                          >
                            ₹{balance.toFixed(2)}
                          </span>
                          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                            {isOwing ? 'Due (उधार)' : 'Settled (चुका दिया)'}
                          </p>
                        </div>
                      </div>

                      {cust.address && (
                        <p className="text-xs text-slate-500 flex items-center gap-1 truncate">
                          <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                          {cust.address}
                        </p>
                      )}

                      {/* Transaction Count & Breakdown */}
                      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                        <span>Total Udhar: ₹{parseFloat(cust.total_credit).toFixed(2)}</span>
                        <span>Paid: ₹{parseFloat(cust.total_payment).toFixed(2)}</span>
                        <span>{cust.transaction_count} txns</span>
                      </div>
                    </CardContent>

                    {/* Quick Action Footer */}
                    <div className="p-3 bg-slate-50/80 border-t border-slate-100 grid grid-cols-2 gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          setTxModalCustomer({ customer: cust, type: 'CREDIT' })
                        }
                        className="text-xs text-red-700 hover:bg-red-50 border-red-200"
                      >
                        <ArrowUpRight className="w-3.5 h-3.5 mr-1" />
                        + Credit (उधार)
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          setTxModalCustomer({ customer: cust, type: 'PAYMENT' })
                        }
                        className="text-xs text-emerald-700 hover:bg-emerald-50 border-emerald-200"
                      >
                        <ArrowDownLeft className="w-3.5 h-3.5 mr-1" />
                        - Got (जमा)
                      </Button>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </>
      )}

      {/* Add Customer Modal */}
      <AddCustomerModal
        isOpen={isAddCustomerOpen}
        onClose={() => setIsAddCustomerOpen(false)}
      />

      {/* Transaction Modal for Quick Actions */}
      {txModalCustomer && (
        <TransactionModal
          isOpen={true}
          onClose={() => setTxModalCustomer(null)}
          customerId={txModalCustomer.customer.id}
          customerName={txModalCustomer.customer.name}
          currentBalance={txModalCustomer.customer.outstanding_balance}
          initialType={txModalCustomer.type}
        />
      )}
    </div>
  )
}
