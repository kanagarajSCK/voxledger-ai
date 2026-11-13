import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../app/App'

describe('VoxLedger AI Frontend Phase 2 Shell', () => {
  it('renders application brand and header navigation elements', () => {
    render(<App />)
    const brandElements = screen.getAllByText(/VoxLedger/i)
    expect(brandElements.length).toBeGreaterThan(0)
    const phaseElements = screen.getAllByText(/PHASE 2/i)
    expect(phaseElements.length).toBeGreaterThan(0)
  })

  it('renders dashboard hero banner and ledger action elements', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /Shopkeeper Ledger Dashboard/i })).toBeInTheDocument()
    expect(screen.getByText(/DIGITAL KHATA • KIRANA LEDGER/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Add Customer/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /View All Customers/i })).toBeInTheDocument()
  })

  it('renders desktop and mobile navigation links', () => {
    render(<App />)
    const dashboardLinks = screen.getAllByRole('link', { name: /Dashboard/i })
    expect(dashboardLinks.length).toBeGreaterThan(0)
    const customerLinks = screen.getAllByRole('link', { name: /Customers/i })
    expect(customerLinks.length).toBeGreaterThan(0)
  })
})
