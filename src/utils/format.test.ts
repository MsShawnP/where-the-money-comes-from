import { describe, it, expect } from 'vitest'
import { formatDollars, formatPercent, formatUnits } from './format'

describe('formatDollars', () => {
  it('formats millions with one decimal', () => {
    expect(formatDollars(1_200_000)).toBe('$1.2M')
    expect(formatDollars(2_500_000)).toBe('$2.5M')
  })

  it('formats thousands as rounded K', () => {
    expect(formatDollars(300_000)).toBe('$300K')
    expect(formatDollars(42_000)).toBe('$42K')
  })

  it('formats small dollar amounts with two decimals (per-unit style)', () => {
    expect(formatDollars(4.20)).toBe('$4.20')
    expect(formatDollars(0.42)).toBe('$0.42')
    expect(formatDollars(0.78)).toBe('$0.78')
  })

  it('formats exact million boundary correctly', () => {
    expect(formatDollars(1_000_000)).toBe('$1.0M')
  })

  it('handles negative values (deduction steps)', () => {
    expect(formatDollars(-154_000)).toBe('$-154K')
  })
})

describe('formatPercent', () => {
  it('converts ratio to percentage with one decimal', () => {
    expect(formatPercent(0.352)).toBe('35.2%')
    expect(formatPercent(0.54)).toBe('54.0%')
    expect(formatPercent(0.0057)).toBe('0.6%')
  })

  it('handles zero', () => {
    expect(formatPercent(0)).toBe('0.0%')
  })
})

describe('formatUnits', () => {
  it('formats numbers with thousands separator', () => {
    expect(formatUnits(1200)).toBe('1,200')
    expect(formatUnits(21000)).toBe('21,000')
    expect(formatUnits(123429)).toBe('123,429')
  })

  it('handles numbers under 1000 without separator', () => {
    expect(formatUnits(500)).toBe('500')
  })
})
