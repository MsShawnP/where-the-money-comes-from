import { useChannelSelection } from './hooks/useChannelSelection'
import type { UseChannelSelectionReturn } from './hooks/useChannelSelection'
import { ChapterNav } from './components/ChapterNav'
import { ChapterLayout } from './components/ChapterLayout'
import { Chapter1 } from './chapters/Chapter1/Chapter1'
import { Chapter2 } from './chapters/Chapter2/Chapter2'
import { Chapter3 } from './chapters/Chapter3/Chapter3'
import { Chapter4 } from './chapters/Chapter4/Chapter4'
import { Chapter5 } from './chapters/Chapter5/Chapter5'
import './App.css'

function renderChapter(chapter: number, selection: UseChannelSelectionReturn) {
  switch (chapter) {
    case 1: return <Chapter1 selection={selection} />
    case 2: return <Chapter2 selection={selection} />
    case 3: return <Chapter3 selection={selection} />
    case 4: return <Chapter4 />
    case 5: return <Chapter5 />
    default: return null
  }
}

function App() {
  const selection = useChannelSelection(1)

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="brand-name">Where the Money Comes From</span>
      </header>

      <ChapterNav
        activeChapter={selection.activeChapter}
        onChapterChange={selection.setChapter}
      />

      <main>
        <ChapterLayout>
          {renderChapter(selection.activeChapter, selection)}
        </ChapterLayout>
      </main>
    </div>
  )
}

export default App
