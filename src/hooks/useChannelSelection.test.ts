import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useChannelSelection } from './useChannelSelection'

describe('useChannelSelection', () => {
  it('starts with no selection and chapter 1', () => {
    const { result } = renderHook(() => useChannelSelection())
    expect(result.current.selected).toBeNull()
    expect(result.current.activeChapter).toBe(1)
  })

  it('getOpacity returns 1.0 when no channel is selected', () => {
    const { result } = renderHook(() => useChannelSelection())
    expect(result.current.getOpacity('Walmart')).toBe(1.0)
    expect(result.current.getOpacity('DTC')).toBe(1.0)
  })

  it('select() sets the selected channel', () => {
    const { result } = renderHook(() => useChannelSelection())
    act(() => result.current.select('Walmart'))
    expect(result.current.selected).toBe('Walmart')
  })

  it('getOpacity returns 1.0 for selected channel, 0.25 for others', () => {
    const { result } = renderHook(() => useChannelSelection())
    act(() => result.current.select('Costco'))
    expect(result.current.getOpacity('Costco')).toBe(1.0)
    expect(result.current.getOpacity('Walmart')).toBe(0.25)
    expect(result.current.getOpacity('DTC')).toBe(0.25)
  })

  it('select() on already-selected channel clears the selection (toggle)', () => {
    const { result } = renderHook(() => useChannelSelection())
    act(() => result.current.select('Walmart'))
    act(() => result.current.select('Walmart'))
    expect(result.current.selected).toBeNull()
  })

  it('clearSelection() removes any active selection', () => {
    const { result } = renderHook(() => useChannelSelection())
    act(() => result.current.select('DTC'))
    act(() => result.current.clearSelection())
    expect(result.current.selected).toBeNull()
  })

  it('setChapter() changes the active chapter', () => {
    const { result } = renderHook(() => useChannelSelection())
    act(() => result.current.setChapter(3))
    expect(result.current.activeChapter).toBe(3)
  })

  it('selection auto-clears when chapter changes', () => {
    const { result } = renderHook(() => useChannelSelection())
    act(() => result.current.select('Walmart'))
    expect(result.current.selected).toBe('Walmart')
    act(() => result.current.setChapter(2))
    expect(result.current.selected).toBeNull()
  })

  it('setChapter() to the same chapter preserves selection (no state change = no effect)', () => {
    const { result } = renderHook(() => useChannelSelection())
    act(() => result.current.select('DTC'))
    act(() => result.current.setChapter(1)) // already on 1 — no chapter change, no selection clear
    expect(result.current.selected).toBe('DTC')
  })
})
