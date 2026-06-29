import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Chapter5 } from './Chapter5'

// Observable Plot uses ResizeObserver and SVG APIs not fully supported in jsdom.
// Mock it so tests focus on Chapter5 behaviour, not Plot internals.
vi.mock('@observablehq/plot', () => {
  const makeSvg = () => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    svg.setAttribute('data-testid', 'mock-plot')
    return svg
  }
  return {
    plot: vi.fn(() => makeSvg()),
    barX: vi.fn(() => ({ type: 'barX' })),
    ruleX: vi.fn(() => ({ type: 'ruleX' })),
    text: vi.fn(() => ({ type: 'text' })),
  }
})

describe('Chapter5', () => {
  it('renders the framing prose', () => {
    render(<Chapter5 />)
    expect(
      screen.getByText(/The question is not whether to be in distribution/i)
    ).toBeInTheDocument()
  })

  it('renders the delta callout text', () => {
    render(<Chapter5 />)
    // Retail contribution ($510k) > distributor ($456k), so "Retail expansion generates" path fires
    expect(screen.getByText(/Retail expansion generates/i)).toBeInTheDocument()
  })

  it('renders the closing prose', () => {
    render(<Chapter5 />)
    expect(
      screen.getByText(/Every brand at this stage faces the same decision/i)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/The implication is not to exit distribution/i)
    ).toBeInTheDocument()
  })

  it('mounts the chart container', () => {
    render(<Chapter5 />)
    const container = document.querySelector('.ch5-chart-container')
    expect(container).toBeInTheDocument()
  })
})
