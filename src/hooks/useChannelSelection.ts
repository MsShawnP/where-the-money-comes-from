import { useState, useEffect } from 'react'

export interface ChannelSelectionState {
  selected: string | null
  activeChapter: number
}

export interface ChannelSelectionActions {
  select: (channel: string) => void
  clearSelection: () => void
  setChapter: (chapter: number) => void
  getOpacity: (channel: string) => number
}

export type UseChannelSelectionReturn = ChannelSelectionState & ChannelSelectionActions

/**
 * Manages channel selection and active chapter state.
 *
 * - Chapters 1–3 use selection to highlight one channel and dim others.
 * - Chapters 4–5 do not use channel selection (different interaction models).
 * - Selection automatically clears when the active chapter changes.
 *
 * getOpacity(channel):
 *   - No selection active → 1.0 (all channels fully visible)
 *   - Selection active, channel matches → 1.0
 *   - Selection active, channel does not match → 0.25 (dimmed)
 */
export function useChannelSelection(initialChapter = 1): UseChannelSelectionReturn {
  const [selected, setSelected] = useState<string | null>(null)
  const [activeChapter, setActiveChapter] = useState(initialChapter)

  // Clear selection whenever the chapter changes
  useEffect(() => {
    setSelected(null)
  }, [activeChapter])

  const select = (channel: string) => {
    setSelected(prev => (prev === channel ? null : channel))
  }

  const clearSelection = () => {
    setSelected(null)
  }

  const setChapter = (chapter: number) => {
    setActiveChapter(chapter)
    // Selection is cleared by the useEffect above
  }

  const getOpacity = (channel: string): number => {
    if (selected === null) return 1.0
    return selected === channel ? 1.0 : 0.25
  }

  return {
    selected,
    activeChapter,
    select,
    clearSelection,
    setChapter,
    getOpacity,
  }
}
