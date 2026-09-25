import { useEffect, useState } from 'react'
import { Link, NavLink, Route, Routes } from 'react-router'
import RecipeForm from './coffee/RecipeForm'
import CoffeeList from './coffee/CoffeeList'
import './App.css'

type ApiState =
  | { status: 'loading'; message: string }
  | { status: 'ready'; message: string }
  | { status: 'error'; message: string }

const modules = [
  { icon: '☕', name: 'Coffee', description: 'Dial in recipes and keep the great ones.' },
  { icon: '↗', name: 'Running', description: 'See your miles, workouts, and progress.' },
  { icon: '✎', name: 'Journal', description: 'Write, reflect, and rediscover old thoughts.' },
  { icon: '⌘', name: 'Crawlers', description: 'Collect useful things from around the web.' },
]

function HomePage() {
  const [api, setApi] = useState<ApiState>({ status: 'loading', message: 'Connecting to the API…' })

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/hello', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error('The API returned an error')
        return response.json() as Promise<{ message: string }>
      })
      .then((data) => setApi({ status: 'ready', message: data.message }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setApi({ status: 'error', message: 'API is offline' })
      })
    return () => controller.abort()
  }, [])

  return (
    <main className="home-content">
      <section className="hero">
        <p className="eyebrow">Your life, in one thoughtful place</p>
        <h1>A quieter home for the things you care about.</h1>
        <p className="intro">Homebase is taking shape. Soon it will bring your rituals, movement,
          writing, and collections together without turning your life into a dashboard.</p>
      </section>
      <section className="modules" aria-label="Planned modules">
        {modules.map((module) => (
          <article key={module.name}>
            <span className="module-icon" aria-hidden="true">{module.icon}</span>
            <div><h2>{module.name}</h2><p>{module.description}</p></div>
            <span className="soon">Someday</span>
          </article>
        ))}
      </section>
      <footer>
        <span>Built slowly, for daily life.</span>
        <span className={`api-status ${api.status}`}><span className="status-dot" />{api.message}</span>
      </footer>
    </main>
  )
}

function App() {
  return (
    <>
      <header className="site-header">
        <nav className="site-nav" aria-label="Main navigation">
          <Link className="wordmark" to="/" aria-label="Homebase home">
            <span className="mark">H</span>Homebase
          </Link>
          <NavLink className="nav-link" to="/coffee" end={false}>Coffee</NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/coffee" element={<CoffeeList />} />
        <Route path="/coffee/new" element={<RecipeForm />} />
      </Routes>
    </>
  )
}

export default App
