import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { fetchDashboardSummary } from '../../services/dashboardService'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { LoadingSpinner } from '../../components/ui/LoadingSpinner'
import { ErrorAlert } from '../../components/ui/ErrorAlert'
import { EmptyState } from '../../components/ui/EmptyState'
import { AddCustomerModal } from '../customers/AddCustomerModal'
import { useVoiceAssistant } from '../voice/VoiceContext'
import {
  Users,
  TrendingUp,
  UserPlus,
  ArrowUpRight,
  ArrowDownLeft,
  ChevronRight,
  Receipt,
  Sparkles,
  Mic,
} from 'lucide-react'

export const DashboardPage: React.FC = () => {
  const [isAddCustomerOpen, setIsAddCustomerOpen] = useState(false)
  const { openVoiceModal } = useVoiceAssistant()

  const { data: summary, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
    staleTime: 5000,
  })

  return (
    <div className="space-y-6">
      {/* Top Welcome Banner with Quick Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 sm:p-6 bg-gradient-to-r from-slate-900 via-slate-800 to-emerald-950 rounded-2xl text-white shadow-lg">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
            <Sparkles className="w-3 h-3" />
            DIGITAL KHATA • KIRANA LEDGER
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight">
            Shopkeeper Ledger Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-slate-300">
            Real-time balance tracking, customer credit, and collection summary.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto">
          <Button
            variant="primary"
            size="md"
            onClick={openVoiceModal}
            className="w-full sm:w-auto gap-2 bg-emerald-500 hover:bg-emerald-600 text-white shadow-md shadow-emerald-500/20"
          >
            <Mic className="w-4 h-4 animate-pulse" />
            Voice Ledger
          </Button>
          <Button
            variant="outline"
            size="md"
            onClick={() => setIsAddCustomerOpen(true)}
            className="w-full sm:w-auto gap-2 bg-white/10 text-white border-white/20 hover:bg-white/20"
          >
            <UserPlus className="w-4 h-4" />
            Add Customer
          </Button>
          <Link to="/customers" className="w-full sm:w-auto">
            <Button variant="outline" size="md" className="w-full sm:w-auto bg-white/10 text-white border-white/20 hover:bg-white/20">
              View All Customers
            </Button>
          </Link>
        </div>
      </div>

      {/* Voice Assistant Kirana Helper Strip */}
      <div className="bg-emerald-50/80 border border-emerald-200/80 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-slate-700">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-sm">
            <Mic className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-emerald-950 block sm:inline mr-2">
              Gnani Prisma v3.0 Voice AI Active:
            </span>
            <span className="text-slate-600">
              बोलें: <span className="font-semibold text-emerald-900 bg-emerald-100/60 px-1.5 py-0.5 rounded">"रमेश का 340 रुपये उधार लिखो"</span> or <span className="font-semibold text-emerald-900 bg-emerald-100/60 px-1.5 py-0.5 rounded">"Ramesh paid 200 rupees"</span>
            </span>
          </div>
        </div>
        <button
          onClick={openVoiceModal}
          className="text-xs font-bold text-emerald-700 hover:text-emerald-900 underline underline-offset-2 shrink-0"
        >
          Try Voice Assistant &rarr;
        </button>
      </div>

      {isLoading && (
        <LoadingSpinner size="lg" label="Loading live ledger metrics from database..." />
      )}

      {isError && (
        <ErrorAlert
          title="Could Not Load Dashboard Data"
          message={error?.message || 'Failed to fetch summary from server.'}
          onRetry={() => refetch()}
        />
      )}

      {summary && (
        <>
          {/* 4 Financial KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Outstanding Balance */}
            <Card className="border-l-4 border-l-red-500 shadow-sm">
              <CardContent className="p-4 sm:p-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Total Due (उधार)
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-red-50 text-red-600 flex items-center justify-center">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    ₹{parseFloat(summary.total_outstanding_credit).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-slate-500 font-medium">
                  Net credit balance across all customers
                </p>
              </CardContent>
            </Card>

            {/* Total Customers */}
            <Card className="border-l-4 border-l-blue-500 shadow-sm">
              <CardContent className="p-4 sm:p-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Customers (ग्राहक)
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                    <Users className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {summary.total_customers}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">registered</span>
                </div>
                <p className="mt-1 text-[11px] text-slate-500 font-medium">
                  Active customer khata profiles
                </p>
              </CardContent>
            </Card>

            {/* Today's Credit */}
            <Card className="border-l-4 border-l-amber-500 shadow-sm">
              <CardContent className="p-4 sm:p-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Today's Credit (आज दिया)
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                    <ArrowUpRight className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    ₹{parseFloat(summary.today_credit).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-slate-500 font-medium">
                  Goods sold on credit today
                </p>
              </CardContent>
            </Card>

            {/* Today's Payments Collected */}
            <Card className="border-l-4 border-l-emerald-500 shadow-sm">
              <CardContent className="p-4 sm:p-5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Today's Got (आज मिले)
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <ArrowDownLeft className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-2xl sm:text-3xl font-extrabold text-emerald-600 tracking-tight">
                    ₹{parseFloat(summary.today_payments).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-slate-500 font-medium">
                  Payments received today
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Recent Ledger Transactions */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base sm:text-lg">Recent Ledger Entries</CardTitle>
                <p className="text-xs text-slate-500">Live feed of latest credits and payments</p>
              </div>
              <Link to="/customers">
                <Button variant="ghost" size="sm" className="text-xs gap-1">
                  Manage Ledgers
                  <ChevronRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              {summary.recent_transactions.length === 0 ? (
                <div className="p-6">
                  <EmptyState
                    icon={Receipt}
                    title="No Transactions Recorded Yet"
                    description="Create your first customer profile to start recording credit and payments in your digital ledger."
                    actionLabel="Add Customer"
                    onAction={() => setIsAddCustomerOpen(true)}
                  />
                </div>
              ) : (
                <div className="divide-y divide-slate-100 overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm">
                    <thead className="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px] tracking-wider">
                      <tr>
                        <th className="px-4 py-3">Customer</th>
                        <th className="px-4 py-3">Type</th>
                        <th className="px-4 py-3">Description</th>
                        <th className="px-4 py-3">Date & Time</th>
                        <th className="px-4 py-3 text-right">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {summary.recent_transactions.map((tx) => (
                        <tr key={tx.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="px-4 py-3 font-semibold text-slate-900">
                            <Link
                              to={`/customers/${tx.customer_id}`}
                              className="hover:text-emerald-600 transition-colors flex items-center gap-1.5"
                            >
                              {tx.customer_name || 'Customer'}
                              <ChevronRight className="w-3 h-3 text-slate-400" />
                            </Link>
                          </td>
                          <td className="px-4 py-3">
                            <Badge
                              variant={tx.type === 'CREDIT' ? 'danger' : 'success'}
                              className="text-[10px]"
                            >
                              {tx.type === 'CREDIT' ? 'CREDIT (+ Udhar)' : 'PAYMENT (- Jama)'}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-slate-600 max-w-xs truncate">
                            {tx.description || '—'}
                          </td>
                          <td className="px-4 py-3 text-slate-500 text-xs font-mono">
                            {new Date(tx.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })},{' '}
                            {new Date(tx.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
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
        </>
      )}

      {/* Add Customer Modal */}
      <AddCustomerModal
        isOpen={isAddCustomerOpen}
        onClose={() => setIsAddCustomerOpen(false)}
      />
    </div>
  )
}
