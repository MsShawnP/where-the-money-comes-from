import { useChannelSelection } from './hooks/useChannelSelection'
import { ScrollNav } from './components/ScrollNav'
import { ChapterLayout } from './components/ChapterLayout'
import { Chapter1 } from './chapters/Chapter1/Chapter1'
import { Chapter2 } from './chapters/Chapter2/Chapter2'
import { Chapter3 } from './chapters/Chapter3/Chapter3'
import { Chapter4 } from './chapters/Chapter4/Chapter4'
import { Chapter5 } from './chapters/Chapter5/Chapter5'
import './App.css'

function App() {
  const selection = useChannelSelection()

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__inner">
          <h1 className="brand-name">Where the Money Comes From</h1>
          <p className="brand-subtitle">Cinderhaven's biggest channel by revenue is not its most profitable. Retail out-earns distribution on every dollar — and pushing more volume through the giant accounts erodes the very margin that makes them worth having.</p>
        </div>
      </header>

      <ScrollNav />

      <main>
        <ChapterLayout>
          <section id="chapter-1" className="chapter-section">
            <div className="chapter-sticky-header">
              <span className="chapter-number">Chapter 1</span>
              <h2 className="chapter-heading">The Revenue Illusion</h2>
            </div>
            <Chapter1 selection={selection} />
          </section>

          <section id="chapter-2" className="chapter-section">
            <div className="chapter-sticky-header">
              <span className="chapter-number">Chapter 2</span>
              <h2 className="chapter-heading">The Per-Unit Showdown</h2>
            </div>
            <Chapter2 selection={selection} />
          </section>

          <section id="chapter-3" className="chapter-section">
            <div className="chapter-sticky-header">
              <span className="chapter-number">Chapter 3</span>
              <h2 className="chapter-heading">The Hidden Tax of Retail</h2>
            </div>
            <Chapter3 selection={selection} />
          </section>

          <section id="chapter-4" className="chapter-section">
            <div className="chapter-sticky-header">
              <span className="chapter-number">Chapter 4</span>
              <h2 className="chapter-heading">The Scale Trap</h2>
            </div>
            <Chapter4 />
          </section>

          <section id="chapter-5" className="chapter-section">
            <div className="chapter-sticky-header">
              <span className="chapter-number">Chapter 5</span>
              <h2 className="chapter-heading">The Capital Allocation Question</h2>
            </div>
            <Chapter5 />
          </section>
        </ChapterLayout>
      </main>

      <footer className="app-footer">
        <div className="app-footer__inner">
          <p>Built by <a href="https://lailarallc.com" className="footer-link">Lailara LLC</a> — data hygiene and analytics consulting for specialty food brands scaling into national retail.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
