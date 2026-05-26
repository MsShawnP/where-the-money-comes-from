/**
 * Formatting utilities for Lailara chart labels and prose claims.
 * All functions are pure — no side effects, no React dependencies.
 */

/**
 * Format a dollar amount compactly: $1.2M, $300K, $4.20
 * - >= 1,000,000 → $X.XM (one decimal)
 * - >= 1,000 → $XXXK (no decimal)
 * - < 1,000 → $X.XX (two decimals, per-unit style)
 */
export function formatDollars(n: number): string {
  if (Math.abs(n) >= 1_000_000) {
    return `$${(n / 1_000_000).toFixed(1)}M`
  }
  if (Math.abs(n) >= 1_000) {
    return `$${Math.round(n / 1_000)}K`
  }
  return `$${n.toFixed(2)}`
}

/**
 * Format a ratio as a percentage with one decimal place.
 * Input: 0.352 → "35.2%"
 */
export function formatPercent(n: number): string {
  return `${(n * 100).toFixed(1)}%`
}

/**
 * Format a unit count with thousands separator.
 * Input: 1200 → "1,200"
 */
export function formatUnits(n: number): string {
  return n.toLocaleString('en-US')
}
