import * as Plot from '@observablehq/plot'
import channelsData from '../../data/channels.json'
import { PlotChart } from '../../components/PlotChart'
import type { UseChannelSelectionReturn } from '../../hooks/useChannelSelection'
import { formatDollars } from '../../utils/format'
import './Chapter2.css'

// Hong Kong teal steps — 6 channels, darkest for highest contribution (DTC), lightest for lowest (Walmart)
const HK_TEAL = ['#b5e4d8', '#6dcdb5', '#35b595', '#1fa282', '#158f75', '#063d32']

// Sort ascending: Walmart (lowest) first, DTC (highest) last
const sortedData = [...channelsData].sort((a, b) => a.contribution_per_unit - b.contribution_per_unit)

export function Chapter2({ selection }: { selection: UseChannelSelectionReturn }) {
  const renderChart = (_container: HTMLDivElement) => {
    const chart = Plot.plot({
      marks: [
        Plot.barX(sortedData, {
          x: 'contribution_per_unit',
          y: 'channel',
          sort: { y: 'x' },  // ascending
          fill: (_d, i) => HK_TEAL[i] ?? HK_TEAL[HK_TEAL.length - 1],
          opacity: (d) => selection.getOpacity(d.channel),
          tip: {
            format: {
              x: (v: number) => formatDollars(v),
              y: String,
            }
          },
        }),
        Plot.text(sortedData, {
          x: 'contribution_per_unit',
          y: 'channel',
          text: (d) => formatDollars(d.contribution_per_unit),
          dx: 6,
          textAnchor: 'start',
          fontSize: 12,
          fill: 'var(--color-text-primary)',
        }),
        Plot.ruleX([0]),
      ],
      x: {
        label: 'Contribution per unit shipped ($)',
        tickFormat: (v: number) => formatDollars(v),
      },
      y: { label: null },
      marginLeft: 140,
      marginRight: 60,
      style: {
        fontFamily: 'var(--font-sans)',
        fontSize: '12px',
        background: 'transparent',
      },
    })
    return chart
  }

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as Element
    const channelEl = target.closest('[data-channel]')
    if (channelEl) {
      selection.select(channelEl.getAttribute('data-channel')!)
    } else {
      selection.clearSelection()
    }
  }

  return (
    <section className="ch2">
      <h2 className="chapter-heading">Chapter 2 — The Per-Unit Showdown</h2>
      <p className="ch2-framing">
        Strip away volume and look at what each channel actually pays per unit shipped — after every deduction, every chargeback, every fee. The gap between Walmart and DTC is not a rounding error.
      </p>
      <div className="ch2-chart-container" onClick={handleClick}>
        <PlotChart
          render={renderChart}
          ariaLabel="Contribution per unit shipped by channel, ranked lowest to highest"
        />
      </div>
      <p className="ch2-footnote">
        Source: Cinderhaven platform data. Contribution = net revenue after all deductions minus COGS. DTC deductions include customer acquisition cost, fulfillment, and payment processing.
      </p>
    </section>
  )
}
