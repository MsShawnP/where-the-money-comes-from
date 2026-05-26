import * as Plot from '@observablehq/plot'
import scenariosData from '../../data/scenarios.json'
import { PlotChart } from '../../components/PlotChart'
import { DataTable } from '../../components/DataTable'
import { formatDollars } from '../../utils/format'
import './Chapter5.css'

const { capital_allocation } = scenariosData

const scenarioBars = [
  {
    scenario: capital_allocation.retailer.label,
    incremental_contribution: capital_allocation.retailer.incremental_contribution,
    color: '#b5e4d8',  // HK-85, lightest teal (retail, lower value)
    assumption: capital_allocation.retailer.assumption,
  },
  {
    scenario: capital_allocation.distributor.label,
    incremental_contribution: capital_allocation.distributor.incremental_contribution,
    color: '#063d32',  // HK-5, darkest teal (distributor, higher value — visually dominant)
    assumption: capital_allocation.distributor.assumption,
  },
]

export function Chapter5() {
  const renderChart = (_container: HTMLDivElement) => {
    return Plot.plot({
      marks: [
        Plot.barX(scenarioBars, {
          x: 'incremental_contribution',
          y: 'scenario',
          fill: 'color',
          sort: { y: 'x' },  // ascending: retail shorter, distributor taller
          tip: {
            format: {
              x: (v: number) => formatDollars(v),
              y: String,
            },
          },
        }),
        Plot.text(scenarioBars, {
          x: 'incremental_contribution',
          y: 'scenario',
          text: (d) => formatDollars(d.incremental_contribution),
          dx: 8,
          textAnchor: 'start',
          fontSize: 13,
          fontWeight: '600',
          fill: 'var(--color-text-primary)',
        }),
        Plot.ruleX([0]),
      ],
      x: {
        label: 'Projected incremental contribution',
        tickFormat: (v: number) => formatDollars(v),
      },
      y: { label: null },
      marginLeft: 210,
      marginRight: 100,
      style: {
        fontFamily: 'var(--font-sans)',
        fontSize: '12px',
        background: 'transparent',
      },
    })
  }

  const distributorWins =
    capital_allocation.distributor.incremental_contribution >
    capital_allocation.retailer.incremental_contribution

  const deltaLabel = distributorWins
    ? `Distribution growth generates ${formatDollars(capital_allocation.delta)} more contribution on the same $1M invested — ${(capital_allocation.delta_pct * 100).toFixed(1)}% more efficient`
    : `Retail expansion generates ${formatDollars(Math.abs(capital_allocation.delta))} more contribution on the same $1M invested`

  return (
    <section className="ch5">
      <h2 className="chapter-heading">Chapter 5 — The Capital Allocation Question</h2>
      <p className="ch5-framing">
        The question is not whether to be in retail. The question is where the next dollar of
        growth investment earns the most. At Cinderhaven's current margin structure, the math
        points clearly toward distribution.
      </p>

      <div className="ch5-chart-container">
        <PlotChart
          render={renderChart}
          ariaLabel="Bar chart comparing incremental contribution from $1M invested in retail expansion vs distribution growth"
        />
      </div>

      <div className="ch5-delta-callout">
        <p className="ch5-delta-text">{deltaLabel}</p>
        <p className="ch5-delta-assumption">
          Retail assumption: {capital_allocation.retailer.assumption}.
        </p>
        <p className="ch5-delta-assumption">
          Distribution assumption: {capital_allocation.distributor.assumption}.
        </p>
      </div>

      <div className="ch5-closing">
        <p className="ch5-closing-prose">
          Every brand at this stage faces the same decision. Retail is real revenue. But retail, net
          of all deductions, delivers roughly 81 cents of contribution per revenue dollar. Distribution
          delivers 90 cents. That 9-point difference is structural — it reflects the compliance overhead
          that retail imposes and distribution does not.
        </p>
        <p className="ch5-closing-prose">
          The implication is not to exit retail. It is to stop treating retail growth as the default
          answer to every investment decision. The brands that reallocate capital toward distribution
          do not sacrifice revenue — they recover margin the income statement had hidden.
        </p>
      </div>

      <p className="ch5-footnote">
        Scenario projections apply current blended contribution margin rates to a $1M incremental
        investment. Retail scenario blends Walmart, Kroger, Whole Foods, Sprouts, Costco, and
        Regional Group. Distribution scenario blends UNFI, KeHE, and DPI Northwest. Figures are
        based on Cinderhaven's FY2024–2026 channel P&amp;L data.
      </p>

      {/* Screen-reader data table */}
      <DataTable
        caption="Capital allocation scenarios — projected incremental contribution from $1M invested"
        columns={[
          { key: 'scenario', label: 'Scenario' },
          { key: 'incremental_contribution', label: 'Projected Incremental Contribution', format: (v) => formatDollars(v as number) },
          { key: 'assumption', label: 'Key Assumption' },
        ]}
        data={scenarioBars as Record<string, unknown>[]}
      />
    </section>
  )
}
