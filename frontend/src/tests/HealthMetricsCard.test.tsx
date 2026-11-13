import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HealthMetricsCard } from '../features/health/HealthMetricsCard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

describe('HealthMetricsCard Component', () => {
  it('renders health section card title and description', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <HealthMetricsCard />
      </QueryClientProvider>
    )

    expect(screen.getByText(/Backend System Health/i)).toBeInTheDocument()
    expect(screen.getByText(/Live connectivity metrics and database status from FastAPI/i)).toBeInTheDocument()
  })
})
