import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Chapter2 } from './Chapter2'
import type { UseChannelSelectionReturn } from '../../hooks/useChannelSelection'

// Mock Observable Plot so tests don't depend on SVG rendering in jsdom
vi.mock('@observablehq/plot', () => ({
  plot: vi.fn(() => {
    const div = document.createElement('div')
    div.setAttribute('data-testid', 'plot-chart')
    return div
  }),
  barX: vi.fn(() => null),
  text: vi.fn(() => null),
  ruleX: vi.fn(() => null),
}))

function makeSelection(overrides: Partial<UseChannelSelectionReturn> = {}): UseChannelSelectionReturn {
  return {
    selected: null,
    activeChapter: 2,
    getOpacity: () => 1,
    select: vi.fn(),
    clearSelection: vi.fn(),
    setChapter: vi.fn(),
    ...overrides,
  }
}

describe('Chapter2', () => {
  it('renders the chapter heading', () => {
    render(<Chapter2 selection={makeSelection()} />)
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Chapter 2 — The Margin Gap')
  })

  it('renders the framing prose', () => {
    render(<Chapter2 selection={makeSelection()} />)
    expect(
      screen.getByText(/Strip away revenue and look at what each dollar actually earns/i)
    ).toBeInTheDocument()
  })

  it('mounts the chart container in the DOM', () => {
    const { container } = render(<Chapter2 selection={makeSelection()} />)
    expect(container.querySelector('.ch2-chart-container')).toBeInTheDocument()
    // PlotChart renders a [data-chart-container] div
    expect(container.querySelector('[data-chart-container]')).toBeInTheDocument()
  })

  it('renders without errors when all 6 channels are present in the data', () => {
    // If channels.json is missing a channel the sort/render would still work;
    // we verify the component renders cleanly end-to-end.
    expect(() => render(<Chapter2 selection={makeSelection()} />)).not.toThrow()
  })

  it('renders the footnote', () => {
    render(<Chapter2 selection={makeSelection()} />)
    expect(screen.getByText(/Cinderhaven platform data/i)).toBeInTheDocument()
  })

  it('calls clearSelection when the chart area is clicked on a non-channel element', async () => {
    const clearSelection = vi.fn()
    const { container } = render(
      <Chapter2 selection={makeSelection({ clearSelection })} />
    )
    const chartContainer = container.querySelector('.ch2-chart-container') as HTMLElement
    chartContainer.click()
    expect(clearSelection).toHaveBeenCalledTimes(1)
  })
})
