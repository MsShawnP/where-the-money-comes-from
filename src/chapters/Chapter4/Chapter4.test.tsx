import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Chapter4 } from './Chapter4'

describe('Chapter4', () => {
  it('renders the chapter heading', () => {
    const { getByRole } = render(<Chapter4 />)
    const heading = getByRole('heading', { level: 2 })
    expect(heading).toHaveTextContent('Chapter 4 — The Scale Trap')
  })

  it('renders the framing prose', () => {
    const { getByText } = render(<Chapter4 />)
    expect(
      getByText(/More Walmart volume does not mean more contribution/)
    ).toBeTruthy()
  })

  it('mounts the chart container in the DOM', () => {
    const { container } = render(<Chapter4 />)
    const chartContainer = container.querySelector('[data-chart-container="true"]')
    expect(chartContainer).toBeTruthy()
  })

  it('renders the scale trap annotation text', () => {
    const { getByText } = render(<Chapter4 />)
    expect(
      getByText(/Scale trap threshold:/)
    ).toBeTruthy()
  })
})
