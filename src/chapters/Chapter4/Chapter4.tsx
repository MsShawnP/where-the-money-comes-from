import * as Plot from '@observablehq/plot'
import scenariosData from '../../data/scenarios.json'
import { PlotChart } from '../../components/PlotChart'
import { DataTable } from '../../components/DataTable'
import { formatDollars, formatUnits } from '../../utils/format'
import './Chapter4.css'

const { walmart_volume_curve, walmart_inflection_volume } = scenariosData

export function Chapter4() {
  const renderChart = (_container: HTMLDivElement) => {
    return Plot.plot({
      marks: [
        // Main declining line
        Plot.lineY(walmart_volume_curve, {
          x: 'volume_units',
          y: 'marginal_contribution_per_unit',
          stroke: 'var(--color-navy)',
          strokeWidth: 2.5,
          curve: 'monotone-x',
        }),
        // Dots at each data point
        Plot.dot(walmart_volume_curve, {
          x: 'volume_units',
          y: 'marginal_contribution_per_unit',
          fill: 'var(--color-navy)',
          r: 4,
        }),
        // Zero line (break-even reference)
        Plot.ruleY([0], {
          stroke: 'var(--color-reference)',
          strokeDasharray: '4 3',
          strokeWidth: 1.5,
        }),
        // Inflection point reference line
        Plot.ruleX([walmart_inflection_volume], {
          stroke: 'var(--color-red)',
          strokeDasharray: '4 3',
          strokeWidth: 1.5,
        }),
        // Hover tooltip
        Plot.tip(walmart_volume_curve, Plot.pointerX({
          x: 'volume_units',
          y: 'marginal_contribution_per_unit',
          title: (d) => `${formatUnits(d.volume_units)} units\n${formatDollars(d.marginal_contribution_per_unit)}/unit`,
        })),
      ],
      x: {
        label: 'Total Walmart volume (units shipped)',
        tickFormat: (v: number) => formatUnits(v),
      },
      y: {
        label: 'Marginal contribution per unit ($)',
        tickFormat: (v: number) => formatDollars(v),
      },
      style: {
        fontFamily: 'var(--font-sans)',
        fontSize: '12px',
        background: 'transparent',
      },
      marginLeft: 80,
    })
  }

  return (
    <section className="ch4">
      <h2 className="chapter-heading">Chapter 4 — The Scale Trap</h2>
      <p className="ch4-framing">
        More Walmart volume does not mean more contribution. Trade spend and chargebacks scale faster than revenue — at roughly 1,070,000 units annually, Walmart becomes margin-negative. Cinderhaven ships about 151,000 Walmart units today. That is 7× below the inflection point, but Walmart's velocity requirements push brands toward it year over year.
      </p>
      <div className="ch4-chart-container">
        <PlotChart
          render={renderChart}
          ariaLabel="Line chart showing Walmart marginal contribution per unit declining as volume increases"
        />
      </div>
      <div className="ch4-annotation">
        <span className="ch4-annotation__line" /> Scale trap threshold: ~{formatUnits(walmart_inflection_volume)} units
      </div>
      <p className="ch4-footnote">
        Derived from Cinderhaven deduction rate schedules. Marginal contribution includes trade spend, chargebacks, slotting amortization, and swell at the applicable volume tier. COGS held constant.
      </p>

      {/* Screen-reader data table */}
      <DataTable
        caption="Walmart marginal contribution per unit at each volume tier"
        columns={[
          { key: 'volume_units', label: 'Volume (units)', format: (v) => formatUnits(v as number) },
          { key: 'marginal_contribution_per_unit', label: 'Marginal Contribution per Unit ($)', format: (v) => formatDollars(v as number) },
        ]}
        data={walmart_volume_curve as Record<string, unknown>[]}
      />
    </section>
  )
}
