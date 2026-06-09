import { useState, useEffect } from 'react'
import './ScrollNav.css'

const CHAPTERS = [
  { id: 'chapter-1', number: 1, label: 'Revenue Illusion' },
  { id: 'chapter-2', number: 2, label: 'Per-Unit Showdown' },
  { id: 'chapter-3', number: 3, label: 'Hidden Tax' },
  { id: 'chapter-4', number: 4, label: 'Scale Trap' },
  { id: 'chapter-5', number: 5, label: 'Capital Allocation' },
]

/**
 * Floating chapter nav fixed to the right edge of the viewport.
 * Uses IntersectionObserver to highlight the current chapter.
 * Click to smooth-scroll to a chapter section.
 */
export function ScrollNav() {
  const [activeChapter, setActiveChapter] = useState(1)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const sections = CHAPTERS.map(ch =>
      document.getElementById(ch.id)
    ).filter(Boolean) as HTMLElement[]

    if (sections.length === 0) return

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const id = entry.target.id
            const ch = CHAPTERS.find(c => c.id === id)
            if (ch) setActiveChapter(ch.number)
          }
        }
      },
      { rootMargin: '-20% 0px -60% 0px' }
    )

    sections.forEach(s => observer.observe(s))

    // Show nav after first scroll past the header
    const handleScroll = () => {
      setVisible(window.scrollY > 200)
    }
    handleScroll()
    window.addEventListener('scroll', handleScroll, { passive: true })

    return () => {
      observer.disconnect()
      window.removeEventListener('scroll', handleScroll)
    }
  }, [])

  const handleClick = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <nav
      className={`scroll-nav${visible ? ' scroll-nav--visible' : ''}`}
      aria-label="Chapter navigation"
    >
      <ol className="scroll-nav__list">
        {CHAPTERS.map(ch => (
          <li key={ch.number}>
            <button
              className={`scroll-nav__item${activeChapter === ch.number ? ' scroll-nav__item--active' : ''}`}
              onClick={() => handleClick(ch.id)}
              aria-current={activeChapter === ch.number ? 'true' : undefined}
              title={ch.label}
            >
              <span className="scroll-nav__dot" />
              <span className="scroll-nav__label">{ch.label}</span>
            </button>
          </li>
        ))}
      </ol>
    </nav>
  )
}
