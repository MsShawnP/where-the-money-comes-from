import { useState } from 'react'

export interface UseChannelSelectionReturn {
  selected: string | null
  select: (channel: string) => void
  clearSelection: () => void
  getOpacity: (channel: string) => number
}

/**
 * Manages channel highlight state across the scrollable narrative.
 *
 * Selection persists as the reader scrolls — clicking a channel in any
 * chapter highlights it everywhere until cleared or toggled off.
 *
 * getOpacity(channel):
 *   - No selection active → 1.0 (all channels fully visible)
 *   - Selection active, channel matches → 1.0
 *   - Selection active, channel does not match → 0.25 (dimmed)
 */
export function useChannelSelection(): UseChannelSelectionReturn {
  const [selected, setSelected] = useState<string | null>(null)

  const select = (channel: string) => {
    setSelected(prev => (prev === channel ? null : channel))
  }

  const clearSelection = () => {
    setSelected(null)
  }

  const getOpacity = (channel: string): number => {
    if (selected === null) return 1.0
    return selected === channel ? 1.0 : 0.25
  }

  return {
    selected,
    select,
    clearSelection,
    getOpacity,
  }
}
