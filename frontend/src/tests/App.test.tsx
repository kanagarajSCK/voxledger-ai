import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../app/App'

describe('VoxLedger AI Frontend Shell', () => {
  it('renders application brand and header elements', () => {
    render(<App />)
    const brandElements = screen.getAllByText(/VoxLedger/i)
    expect(brandElements.length).toBeGreaterThan(0)
    const phaseElements = screen.getAllByText(/PHASE 1/i)
    expect(phaseElements.length).toBeGreaterThan(0)
  })

  it('renders foundation hero banner and architecture cards', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /VoxLedger AI/i })).toBeInTheDocument()
    expect(screen.getByText(/PHASE 1 COMPLETE — FOUNDATION & ARCHITECTURE/i)).toBeInTheDocument()
    expect(screen.getByText(/Backend System Health/i)).toBeInTheDocument()
    expect(screen.getByText(/Database Model Scaffolding/i)).toBeInTheDocument()
    expect(screen.getByText(/Phase 1 Verification Matrix/i)).toBeInTheDocument()
  })
})
