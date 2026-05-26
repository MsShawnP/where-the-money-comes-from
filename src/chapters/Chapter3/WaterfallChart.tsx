import { useCallback } from 'react'
import * as Plot from '@observablehq/plot'
import { PlotChart } from '../../components/PlotChart'
import { formatDollars } from '../../utils/format'

export interface WaterfallStep {
  label: string
  value: number
  cumulative: number
  is_subtotal?: boolean
  is_total?: boolean
}

export interface WaterfallChartProps {
  title: string
  steps: WaterfallStep[]
  ariaLabel?: string
}

function getBarColor(step: WaterfallStep, index: number): string {
  if (step.is_subtotal || step.is_total) return 'var(--color-navy)'
  if (index === 0) return 'var(--color-hk-35)'
  // Operating cost steps (grey) — distinct from trade deductions (red)
  if (step.label === 'COGS' || step.label === 'Promo Costs' || step.label === 'Dispute Overhead') {
    return 'var(--color-reference)'
  }
  return 'var(--color-red)'
}

export function WaterfallChart({ title, steps, ariaLabel }: WaterfallChartProps) {
  const renderChart = useCallback(
    (_container: HTMLDivElement) => {
      if (steps.length === 0) return null

      const barData = steps.map((step, i) => {
        let y1: number
        let y2: number

        if (step.is_subtotal || step.is_total) {
          y1 = 0
          y2 = step.cumulative
        } else if (i === 0) {
          y1 = 0
          y2 = step.cumulative
        } else {
          const prev = steps[i - 1].cumulative
          y1 = Math.min(prev, step.cumulative)
          y2 = Math.max(prev, step.cumulative)
        }

        return {
          ...step,
          y1,
          y2,
          fill: getBarColor(step, i),
        }
      })

      const maxVal = Math.max(...barData.map(d => d.y2))

      const chart = Plot.plot({
        marks: [
          Plot.barY(barData, {
            x: 'label',
            y1: 'y1',
            y2: 'y2',
            fill: 'fill',
            title: (d) => `${d.label}: ${formatDollars(d.cumulative)}`,
          }),
          Plot.text(barData, {
            x: 'label',
            y: (d) => d.y2 + maxVal * 0.02,
            text: (d) => formatDollars(d.cumulative),
            textAnchor: 'middle',
            fontSize: 10,
            fill: 'var(--color-text-primary)',
          }),
          Plot.ruleY([0]),
        ],
        x: {
          label: null,
          tickRotate: -35,
        },
        y: {
          label: 'Dollars',
          tickFormat: formatDollars,
          grid: true,
        },
        marginBottom: 80,
        marginLeft: 60,
        marginRight: 16,
        height: 320,
        style: {
          fontFamily: 'var(--font-sans)',
          fontSize: '11px',
          background: 'transparent',
          overflow: 'visible',
        },
      })

      return chart
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [steps]
  )

  return (
    <div className="waterfall-chart">
      <h3 className="waterfall-chart__title">{title}</h3>
      <PlotChart
        render={renderChart}
        ariaLabel={ariaLabel ?? `Waterfall chart: ${title}`}
      />
    </div>
  )
}
