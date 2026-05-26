import * as Plot from '@observablehq/plot'
import scenariosData from '../../data/scenarios.json'
import { PlotChart } from '../../components/PlotChart'
import { formatDollars } from '../../utils/format'
import './Chapter5.css'

const { capital_allocation } = scenariosData

const scenarioBars = [
  {
    scenario: capital_allocation.retail.label,
    incremental_contribution: capital_allocation.retail.incremental_contribution,
    color: '#b5e4d8',  // HK-85, lightest teal (retail, lower value)
    assumption: capital_allocation.retail.assumption,
  },
  {
    scenario: capital_allocation.dtc.label,
    incremental_contribution: capital_allocation.dtc.incremental_contribution,
    color: '#063d32',  // HK-5, darkest teal (DTC, higher value — visually dominant)
    assumption: capital_allocation.dtc.assumption,
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
          sort: { y: 'x' },  // ascending: retail shorter, DTC taller
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
      marginLeft: 180,
      marginRight: 100,
      style: {
        fontFamily: 'var(--font-sans)',
        fontSize: '12px',
        background: 'transparent',
      },
    })
  }

  const dtcWins = capital_allocation.dtc.incremental_contribution > capital_allocation.retail.incremental_contribution
  const deltaLabel = dtcWins
    ? `DTC generates ${formatDollars(capital_allocation.delta)} more contribution on the same $1M invested — ${capital_allocation.delta_pct.toFixed(1)}× more`
    : `Retail generates ${formatDollars(Math.abs(capital_allocation.delta))} more contribution on the same $1M invested`

  return (
    <section className="ch5">
      <h2 className="chapter-heading">Chapter 5 — The Capital Allocation Question</h2>
      <p className="ch5-framing">
        The question is not whether to be in retail. The question is where the next dollar of growth investment earns the most. At Cinderhaven's current stage, the math is unambiguous.
      </p>

      <div className="ch5-chart-container">
        <PlotChart
          render={renderChart}
          ariaLabel="Bar chart comparing incremental contribution from $1M invested in retail vs DTC infrastructure"
        />
      </div>

      <div className="ch5-delta-callout">
        <p className="ch5-delta-text">{deltaLabel}</p>
        <p className="ch5-delta-assumption">
          Retail assumption: {capital_allocation.retail.assumption}.
        </p>
        <p className="ch5-delta-assumption">
          DTC assumption: {capital_allocation.dtc.assumption}.
        </p>
      </div>

      <div className="ch5-closing">
        <p className="ch5-closing-prose">
          Every brand at this stage faces the same decision. Retail is real revenue. But retail at scale, net of all deductions, often contributes far less per unit than DTC. The brands that figure this out first rebalance their investment mix — not by abandoning retail, but by growing DTC faster.
        </p>
        <p className="ch5-closing-prose">
          The analysis above uses Cinderhaven's actual platform data. The same methodology applies to any specialty food brand with structured deduction data. The numbers will differ. The pattern usually does not.
        </p>
      </div>

      <p className="ch5-footnote">
        Scenario projections assume current per-unit contribution rates and volume ramp consistent with historical trends. Retail scenario based on Walmart blended contribution. DTC scenario assumes infrastructure investment in Shopify, email, and subscription retention — not paid acquisition alone.
      </p>
    </section>
  )
}
