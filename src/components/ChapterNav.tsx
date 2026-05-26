import './ChapterNav.css'

interface Chapter {
  number: number
  label: string
}

const CHAPTERS: Chapter[] = [
  { number: 1, label: 'The Revenue Illusion' },
  { number: 2, label: 'The Per-Unit Showdown' },
  { number: 3, label: 'The Hidden Tax of Retail' },
  { number: 4, label: 'The Scale Trap' },
  { number: 5, label: 'The Capital Allocation Question' },
]

interface ChapterNavProps {
  activeChapter: number
  onChapterChange: (chapter: number) => void
}

/**
 * Horizontal chapter navigation bar.
 * Initial active chapter: 1 (controlled by parent via activeChapter prop).
 * Active chapter has a navy underline indicator.
 * Clicking a chapter updates the active chapter via onChapterChange,
 * which also clears any channel selection (handled by useChannelSelection.setChapter).
 */
export function ChapterNav({ activeChapter, onChapterChange }: ChapterNavProps) {
  return (
    <nav className="chapter-nav" aria-label="Chapter navigation">
      <ol className="chapter-nav__list">
        {CHAPTERS.map((ch) => (
          <li key={ch.number} className="chapter-nav__item">
            <button
              className={`chapter-nav__btn${activeChapter === ch.number ? ' chapter-nav__btn--active' : ''}`}
              onClick={() => onChapterChange(ch.number)}
              aria-current={activeChapter === ch.number ? 'true' : undefined}
            >
              <span className="chapter-nav__number">{ch.number}</span>
              <span className="chapter-nav__label">{ch.label}</span>
            </button>
          </li>
        ))}
      </ol>
    </nav>
  )
}
