import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Modal } from '../../components/ui/Modal'
import { Input } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { createCustomer } from '../../services/customerService'
import { ApiError } from '../../lib/api'
import { UserPlus } from 'lucide-react'

export interface AddCustomerModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: (customerId: string) => void
}

export const AddCustomerModal: React.FC<AddCustomerModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: createCustomer,
    onSuccess: (newCustomer) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      handleReset()
      onClose()
      if (onSuccess) onSuccess(newCustomer.id)
    },
    onError: (err: ApiError) => {
      setFormError(err.message || 'Failed to create customer.')
    },
  })

  const handleReset = () => {
    setName('')
    setPhone('')
    setAddress('')
    setFormError(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (!name.trim()) {
      setFormError('Customer name is required.')
      return
    }

    mutation.mutate({
      name: name.trim(),
      phone: phone.trim() || undefined,
      address: address.trim() || undefined,
    })
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        handleReset()
        onClose()
      }}
      title="Add New Customer"
      description="Register a new kirana customer to manage their credit ledger."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {formError && (
          <div className="p-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg">
            {formError}
          </div>
        )}

        <Input
          label="Customer Name *"
          placeholder="e.g. Ramesh Kumar"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          autoFocus
        />

        <Input
          label="Phone Number (Optional)"
          placeholder="e.g. +91 98765 43210"
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          helperText="Used for customer search and future SMS reminders."
        />

        <Input
          label="Address / Shop Landmark (Optional)"
          placeholder="e.g. Shop #4, Gandhi Market"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              handleReset()
              onClose()
            }}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={mutation.isPending}
            className="gap-2"
          >
            <UserPlus className="w-4 h-4" />
            Create Customer
          </Button>
        </div>
      </form>
    </Modal>
  )
}
