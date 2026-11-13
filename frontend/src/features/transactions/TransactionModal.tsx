import React, { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '../../components/ui/Modal'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { createTransaction } from '../../services/transactionService'
import { TransactionType } from '../../types/transaction'
import { ApiError } from '../../lib/api'
import { ArrowUpRight, ArrowDownLeft, AlertCircle, CheckCircle2, ShieldCheck } from 'lucide-react'

export interface TransactionModalProps {
  isOpen: boolean
  onClose: () => void
  customerId: string
  customerName: string
  currentBalance: string
  initialType?: TransactionType
}

export const TransactionModal: React.FC<TransactionModalProps> = ({
  isOpen,
  onClose,
  customerId,
  customerName,
  currentBalance,
  initialType = 'CREDIT',
}) => {
  const queryClient = useQueryClient()
  const [type, setType] = useState<TransactionType>(initialType)
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [step, setStep] = useState<'input' | 'confirm'>('input')
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setType(initialType)
      setStep('input')
      setAmount('')
      setDescription('')
      setFormError(null)
    }
  }, [isOpen, initialType])

  const parsedCurrentBalance = parseFloat(currentBalance) || 0
  const parsedAmount = parseFloat(amount) || 0

  const mutation = useMutation({
    mutationFn: createTransaction,
    onSuccess: () => {
      // Invalidate relevant queries so balances refresh across the app
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      queryClient.invalidateQueries({ queryKey: ['customer', customerId] })
      queryClient.invalidateQueries({ queryKey: ['customer-transactions', customerId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      onClose()
    },
    onError: (err: ApiError) => {
      setFormError(err.message || 'Transaction processing failed.')
      setStep('input')
    },
  })

  const validateInput = (): boolean => {
    if (!amount || parsedAmount <= 0) {
      setFormError('Please enter a valid amount greater than ₹0.')
      return false
    }

    if (type === 'PAYMENT') {
      if (parsedCurrentBalance <= 0) {
        setFormError('Customer has ₹0.00 outstanding balance. No payment is owed.')
        return false
      }
      if (parsedAmount > parsedCurrentBalance) {
        setFormError(
          `Payment (₹${parsedAmount.toFixed(2)}) cannot exceed outstanding balance (₹${parsedCurrentBalance.toFixed(2)}).`
        )
        return false
      }
    }

    return true
  }

  const handleProceedToConfirm = (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    if (validateInput()) {
      setStep('confirm')
    }
  }

  const handleFinalSubmit = () => {
    setFormError(null)
    const idempotencyKey = `idemp_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`

    mutation.mutate({
      customer_id: customerId,
      amount: parsedAmount.toFixed(2),
      type,
      description: description.trim() || undefined,
      idempotency_key: idempotencyKey,
    })
  }

  const newProjectedBalance =
    type === 'CREDIT'
      ? parsedCurrentBalance + parsedAmount
      : parsedCurrentBalance - parsedAmount

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={type === 'CREDIT' ? 'Give Credit (उधार दिया)' : 'Record Payment (पैसे मिले)'}
      description={`Customer: ${customerName} • Current Due: ₹${parsedCurrentBalance.toFixed(2)}`}
    >
      {step === 'input' ? (
        <form onSubmit={handleProceedToConfirm} className="space-y-4">
          {formError && (
            <div className="p-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <span>{formError}</span>
            </div>
          )}

          {/* Type Toggle */}
          <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-lg">
            <button
              type="button"
              onClick={() => {
                setType('CREDIT')
                setFormError(null)
              }}
              className={`flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-md transition-colors ${
                type === 'CREDIT'
                  ? 'bg-red-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ArrowUpRight className="w-3.5 h-3.5" />
              Give Credit (उधार)
            </button>
            <button
              type="button"
              onClick={() => {
                setType('PAYMENT')
                setFormError(null)
              }}
              className={`flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-md transition-colors ${
                type === 'PAYMENT'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <ArrowDownLeft className="w-3.5 h-3.5" />
              Got Payment (जमा)
            </button>
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-700">Amount (₹) *</label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 font-bold text-base">
                ₹
              </span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                placeholder="0.00"
                value={amount}
                onChange={(e) => {
                  setAmount(e.target.value)
                  setFormError(null)
                }}
                required
                autoFocus
                className="w-full h-11 pl-8 pr-3.5 rounded-lg border border-slate-300 bg-white text-base font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
            </div>
            {type === 'PAYMENT' && parsedCurrentBalance > 0 && (
              <p className="text-[11px] text-slate-500">
                Maximum payable: <span className="font-semibold text-slate-700">₹{parsedCurrentBalance.toFixed(2)}</span>
              </p>
            )}
          </div>

          <Input
            label="Note / Item Description (Optional)"
            placeholder="e.g. 5kg Rice, 1L Oil or UPI Payment"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant={type === 'CREDIT' ? 'danger' : 'primary'}
            >
              Review Transaction
            </Button>
          </div>
        </form>
      ) : (
        /* Confirmation Step */
        <div className="space-y-4">
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Transaction Type</span>
              <span
                className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                  type === 'CREDIT' ? 'bg-red-100 text-red-800' : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {type === 'CREDIT' ? 'CREDIT GIVEN (+ Udhar)' : 'PAYMENT RECEIVED (- Jama)'}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Customer</span>
              <span className="font-semibold text-slate-900">{customerName}</span>
            </div>

            <div className="flex items-center justify-between border-t border-slate-200 pt-2">
              <span className="text-sm font-semibold text-slate-700">Transaction Amount</span>
              <span
                className={`text-xl font-extrabold ${
                  type === 'CREDIT' ? 'text-red-600' : 'text-emerald-600'
                }`}
              >
                ₹{parsedAmount.toFixed(2)}
              </span>
            </div>

            {description && (
              <div className="text-xs text-slate-600 bg-white p-2 rounded border border-slate-100">
                <span className="font-semibold text-slate-500">Note: </span>
                {description}
              </div>
            )}

            <div className="border-t border-slate-200 pt-2 flex items-center justify-between text-xs">
              <span className="text-slate-500">New Outstanding Balance</span>
              <span className="font-bold text-slate-900">
                ₹{newProjectedBalance.toFixed(2)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Immutable ledger record with duplicate-submission protection.</span>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setStep('input')}
              disabled={mutation.isPending}
            >
              Back
            </Button>
            <Button
              type="button"
              variant={type === 'CREDIT' ? 'danger' : 'primary'}
              onClick={handleFinalSubmit}
              isLoading={mutation.isPending}
              className="gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              Confirm & Save
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}
