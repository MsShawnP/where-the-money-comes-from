import { ReactNode } from 'react'
import './ChapterLayout.css'

interface ChapterLayoutProps {
  children: ReactNode
}

/**
 * Content wrapper that constrains width to 900px, applies section gap and page padding.
 * Wrap each chapter's content in this component.
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
