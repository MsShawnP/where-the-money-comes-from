import { useChannelSelection } from './hooks/useChannelSelection'
import { ChapterNav } from './components/ChapterNav'
import { ChapterLayout } from './components/ChapterLayout'
import './App.css'

// Chapter components are imported as they are built (U5–U9).
// Placeholders render until each chapter is implemented.
function ChapterPlaceholder({ number, title }: { number: number; title: string }) {
  return (
    <section>
      <h2 className="chapter-heading">
        Chapter {number} — {title}
      </h2>
      <p style={{ color: 'var(--color-text-secondary)' }}>Coming soon…</p>
    </section>
  )
}

const CHAPTER_TITLES: Record<number, string> = {
  1: 'The Revenue Illusion',
  2: 'The Per-Unit Showdown',
  3: 'The Hidden Tax of Retail',
  4: 'The Scale Trap',
  5: 'The Capital Allocation Question',
}

function renderChapter(chapter: number) {
  return (
    <ChapterPlaceholder
      number={chapter}
      title={CHAPTER_TITLES[chapter] ?? ''}
    />
  )
}

function App() {
  const { activeChapter, setChapter } = useChannelSelection(1)

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="brand-name">Where the Money Comes From</span>
      </header>

      <ChapterNav
        activeChapter={activeChapter}
        onChapterChange={setChapter}
      />

      <main>
        <ChapterLayout>
          {renderChapter(activeChapter)}
        </ChapterLayout>
      </main>
    </div>
  )
}

export default App
