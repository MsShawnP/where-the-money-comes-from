import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { WaterfallChart } from './WaterfallChart'
import type { WaterfallStep } from './WaterfallChart'

const sampleSteps: WaterfallStep[] = [
  { label: 'Gross Revenue', value: 1000, cumulative: 1000 },
  { label: 'Deduction A', value: -200, cumulative: 800 },
  { label: 'Net Revenue', value: 0, cumulative: 800, is_subtotal: true },
  { label: 'COGS', value: -500, cumulative: 300 },
  { label: 'Contribution', value: 0, cumulative: 300, is_total: true },
]

describe('WaterfallChart', () => {
  it('renders with valid steps data', () => {
    const { container } = render(
      <WaterfallChart title="Test Channel" steps={sampleSteps} />
    )
    expect(container.querySelector('.waterfall-chart')).toBeTruthy()
    expect(container.querySelector('.waterfall-chart__title')?.textContent).toBe('Test Channel')
  })

  it('does not error with an empty steps array', () => {
    expect(() =>
      render(<WaterfallChart title="Empty" steps={[]} />)
    ).not.toThrow()
  })

  it('renders the chart title', () => {
    const { getByText } = render(
      <WaterfallChart title="Walmart" steps={sampleSteps} />
    )
    expect(getByText('Walmart')).toBeTruthy()
  })
})
