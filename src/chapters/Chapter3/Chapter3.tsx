import { useCallback } from 'react'
import * as Plot from '@observablehq/plot'
import { PlotChart } from '../../components/PlotChart'
import { WaterfallChart } from './WaterfallChart'
import { DataTable } from '../../components/DataTable'
import { formatDollars } from '../../utils/format'
import type { UseChannelSelectionReturn } from '../../hooks/useChannelSelection'
import channelsData from '../../data/channels.json'
import deductionsData from '../../data/deductions.json'
import './Chapter3.css'

interface Chapter3Props {
  selection: UseChannelSelectionReturn
}

// Hong Kong teal palette — darkest to lightest, 6 steps for up to 6 channels
const HK_COLORS = [
  '#063d32', // HK-5
  '#0a5c4b', // HK-15
  '#0e6e5a', // HK-25
  '#158f75', // HK-35
  '#1fa282', // HK-45
  '#35b595', // HK-55
]

function getHKColor(index: number, total: number): string {
  const step = Math.min(
    Math.floor((index / total) * HK_COLORS.length),
    HK_COLORS.length - 1
  )
  return HK_COLORS[step]
}

type DeductionsKey = keyof typeof deductionsData

function getDeductionSteps(channel: string) {
  const key = channel as DeductionsKey
  return deductionsData[key]?.steps ?? []
}

function isRetailChannel(channel: string): boolean {
  const key = channel as DeductionsKey
  return deductionsData[key]?.type === 'retail'
}

const sortedByContribution = [...channelsData].sort(
  (a, b) => b.contribution_dollars - a.contribution_dollars
)

export function Chapter3({ selection }: Chapter3Props) {
  const renderSummaryChart = useCallback(
    (_container: HTMLDivElement) => {
      const chart = Plot.plot({
        marks: [
          Plot.barX(sortedByContribution, {
            x: 'contribution_dollars',
            y: 'channel',
            sort: { y: '-x' },
            fill: (_d, i) => getHKColor(i, sortedByContribution.length),
            opacity: (d) => selection.getOpacity(d.channel),
            title: (d) => `${d.channel}: ${formatDollars(d.contribution_dollars)}`,
          }),
          Plot.ruleX([0]),
          Plot.text(sortedByContribution, {
            x: 'contribution_dollars',
            y: 'channel',
            text: (d) => formatDollars(d.contribution_dollars),
            dx: 6,
            textAnchor: 'start',
            fontSize: 12,
            fill: 'var(--color-text-primary)',
            opacity: (d) => selection.getOpacity(d.channel),
          }),
        ],
        x: {
          label: 'Contribution Dollars',
          tickFormat: formatDollars,
          grid: true,
        },
        y: { label: null },
        marginLeft: 140,
        marginRight: 80,
        height: 280,
        style: {
          fontFamily: 'var(--font-sans)',
          fontSize: '12px',
          background: 'transparent',
          overflow: 'visible',
        },
      })

      // Attach data-channel to bar rects for click handling
      const rects = chart.querySelectorAll<SVGRectElement>('rect')
      let barIndex = 0
      rects.forEach((rect) => {
        const h = parseFloat(rect.getAttribute('height') ?? '0')
        if (h > 2 && barIndex < sortedByContribution.length) {
          rect.setAttribute('data-channel', sortedByContribution[barIndex].channel)
          rect.style.cursor = 'pointer'
          barIndex++
        }
      })

      return chart
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selection.selected]
  )

  const handleChartClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement
    const channel = target.getAttribute('data-channel')
    if (channel) {
      selection.select(channel)
    } else if (
      target === e.currentTarget ||
      target.tagName === 'svg' ||
      target.tagName === 'g'
    ) {
      selection.clearSelection()
    }
  }

  const selected = selection.selected
  const showWaterfall = selected !== null && deductionsData[selected as DeductionsKey] !== undefined
  const selectedIsRetail = selected !== null && isRetailChannel(selected)
  const showSideBySide = showWaterfall && selectedIsRetail && selected !== 'DTC'

  return (
    <section className="chapter-3">
      <h2 className="chapter-heading">Chapter 3 — The Hidden Tax of Retail</h2>

      <p className="ch3-framing">
        Every retail channel comes with a hidden layer of deductions between the invoice price and
        what actually reaches your bank account. Slotting fees, chargebacks, trade spend, OTIF
        penalties — each is individually negotiable but collectively they can consume most of your
        margin. Click any channel below to see where its revenue goes.
      </p>

      <div
        className="ch3-summary"
        onClick={handleChartClick}
        role="presentation"
      >
        <PlotChart
          render={renderSummaryChart}
          ariaLabel="Contribution dollars by channel — horizontal bar chart, click to expand waterfall"
        />
      </div>

      <p className="ch3-footnote">
        Contribution dollars = gross revenue minus all trade deductions, slotting, chargebacks,
        freight, and variable COGS. Fixed overhead excluded. Source: Cinderhaven FY2024 channel P&amp;L.
      </p>

      {/* Screen-reader summary table */}
      <DataTable
        caption="Contribution dollars by channel"
        columns={[
          { key: 'channel', label: 'Channel' },
          { key: 'contribution_dollars', label: 'Contribution Dollars', format: (v) => formatDollars(v as number) },
        ]}
        data={sortedByContribution as Record<string, unknown>[]}
      />

      {showWaterfall && (
        <div className="ch3-waterfall-section" data-testid="waterfall-section">
          <h3 className="ch3-waterfall-heading">
            {showSideBySide
              ? `Deduction Structure: ${selected} vs DTC`
              : `Deduction Structure: ${selected}`}
          </h3>

          <div className={showSideBySide ? 'ch3-waterfall-grid' : undefined}>
            <WaterfallChart
              title={selected}
              steps={getDeductionSteps(selected)}
              ariaLabel={`Waterfall deduction chart for ${selected}`}
            />

            {showSideBySide && (
              <WaterfallChart
                title="DTC"
                steps={getDeductionSteps('DTC')}
                ariaLabel="Waterfall deduction chart for DTC"
              />
            )}
          </div>

          {/* Screen-reader deduction table for selected channel */}
          <DataTable
            caption={`Deduction waterfall — ${selected}`}
            columns={[
              { key: 'label', label: 'Line Item' },
              { key: 'value', label: 'Amount', format: (v) => v === 0 ? '—' : formatDollars(v as number) },
              { key: 'cumulative', label: 'Running Total', format: (v) => formatDollars(v as number) },
            ]}
            data={getDeductionSteps(selected) as Record<string, unknown>[]}
          />

          {showSideBySide && (
            <DataTable
              caption="Deduction waterfall — DTC"
              columns={[
                { key: 'label', label: 'Line Item' },
                { key: 'value', label: 'Amount', format: (v) => v === 0 ? '—' : formatDollars(v as number) },
                { key: 'cumulative', label: 'Running Total', format: (v) => formatDollars(v as number) },
              ]}
              data={getDeductionSteps('DTC') as Record<string, unknown>[]}
            />
          )}
        </div>
      )}
    </section>
  )
}
