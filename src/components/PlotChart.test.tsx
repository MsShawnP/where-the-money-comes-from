import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlotChart } from './PlotChart'

describe('PlotChart', () => {
  it('mounts the element returned by render() into the container', () => {
    const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    svgEl.setAttribute('data-testid', 'plot-svg')

    const renderFn = vi.fn(() => svgEl)
    const { container } = render(<PlotChart render={renderFn} />)

    expect(renderFn).toHaveBeenCalledTimes(1)
    expect(container.querySelector('[data-testid="plot-svg"]')).toBeTruthy()
  })

  it('adds role="img" and aria-label to SVG elements', () => {
    const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    render(<PlotChart render={() => svgEl} ariaLabel="Test chart" />)

    expect(svgEl.getAttribute('role')).toBe('img')
    expect(svgEl.getAttribute('aria-label')).toBe('Test chart')
  })

  it('does not error when render() returns null', () => {
    expect(() =>
      render(<PlotChart render={() => null} />)
    ).not.toThrow()
  })

  it('applies className to the container div', () => {
    const { container } = render(
      <PlotChart render={() => null} className="my-chart" />
    )
    expect(container.querySelector('.my-chart')).toBeTruthy()
  })

  it('clears previous output when re-rendered', () => {
    let callCount = 0
    const renderFn = () => {
      callCount++
      const el = document.createElement('div')
      el.setAttribute('data-call', String(callCount))
      return el
    }

    const { rerender } = render(<PlotChart render={renderFn} />)
    const { container } = render(<PlotChart render={renderFn} />)
    rerender(<PlotChart render={renderFn} />)

    // Only one chart element should be present (no DOM leak)
    const chartContainer = container.querySelector('[data-chart-container]')
    expect(chartContainer?.children.length).toBeLessThanOrEqual(1)
  })
})
