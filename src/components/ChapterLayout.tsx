import { ReactNode } from 'react'
import './ChapterLayout.css'

interface ChapterLayoutProps {
  children: ReactNode
}

/**
 * Content wrapper that constrains width and applies vertical rhythm.
 * In the scrollable layout, this wraps ALL chapters (not one at a time).
 */
export function ChapterLayout({ children }: ChapterLayoutProps) {
  return (
    <div className="chapter-layout">
      <div className="chapter-layout__inner">
        {children}
      </div>
    </div>
  )
}
