import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AddCustomerModal } from '../features/customers/AddCustomerModal'

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

describe('AddCustomerModal Component', () => {
  it('renders customer creation modal with required form fields', () => {
    render(<AddCustomerModal isOpen={true} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    })

    expect(screen.getByText(/Add New Customer/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/e.g. Ramesh Kumar/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/e.g. \+91 98765 43210/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create Customer/i })).toBeInTheDocument()
  })

  it('validates that customer name is required on submit', () => {
    const { container } = render(<AddCustomerModal isOpen={true} onClose={vi.fn()} />, {
      wrapper: createWrapper(),
    })

    const form = container.querySelector('form')!
    fireEvent.submit(form)

    expect(screen.getByText(/Customer name is required/i)).toBeInTheDocument()
  })
})
