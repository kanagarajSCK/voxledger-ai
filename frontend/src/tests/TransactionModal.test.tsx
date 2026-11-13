import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TransactionModal } from '../features/transactions/TransactionModal'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('TransactionModal Component', () => {
  it('renders credit transaction modal with customer name', () => {
    render(
      <TransactionModal
        isOpen={true}
        onClose={vi.fn()}
        customerId="cust-123"
        customerName="Ramesh Kirana"
        currentBalance="500.00"
        initialType="CREDIT"
      />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText(/Give Credit \(उधार दिया\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Customer: Ramesh Kirana/i)).toBeInTheDocument()
    expect(screen.getByText(/Current Due: ₹500.00/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/0.00/i)).toBeInTheDocument()
  })

  it('rejects payment exceeding customer outstanding balance', () => {
    const { container } = render(
      <TransactionModal
        isOpen={true}
        onClose={vi.fn()}
        customerId="cust-123"
        customerName="Ramesh Kirana"
        currentBalance="200.00"
        initialType="PAYMENT"
      />,
      { wrapper: createWrapper() }
    )

    const amountInput = screen.getByPlaceholderText(/0.00/i)
    fireEvent.change(amountInput, { target: { value: '350.00' } })

    const form = container.querySelector('form')!
    fireEvent.submit(form)

    expect(
      screen.getByText(/Payment \(₹350.00\) cannot exceed outstanding balance \(₹200.00\)/i)
    ).toBeInTheDocument()
  })

  it('allows valid payment and transitions to confirmation step', () => {
    const { container } = render(
      <TransactionModal
        isOpen={true}
        onClose={vi.fn()}
        customerId="cust-123"
        customerName="Ramesh Kirana"
        currentBalance="500.00"
        initialType="PAYMENT"
      />,
      { wrapper: createWrapper() }
    )

    const amountInput = screen.getByPlaceholderText(/0.00/i)
    fireEvent.change(amountInput, { target: { value: '150.00' } })

    const form = container.querySelector('form')!
    fireEvent.submit(form)

    expect(screen.getByText(/PAYMENT RECEIVED \(- Jama\)/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Confirm & Save/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Back/i })).toBeInTheDocument()
  })

  it('validates that transaction amount must be greater than zero', () => {
    const { container } = render(
      <TransactionModal
        isOpen={true}
        onClose={vi.fn()}
        customerId="cust-123"
        customerName="Ramesh Kirana"
        currentBalance="500.00"
        initialType="CREDIT"
      />,
      { wrapper: createWrapper() }
    )

    const amountInput = screen.getByPlaceholderText(/0.00/i)
    fireEvent.change(amountInput, { target: { value: '0' } })

    const form = container.querySelector('form')!
    fireEvent.submit(form)

    expect(
      screen.getByText(/Please enter a valid amount greater than ₹0/i)
    ).toBeInTheDocument()
  })
})
