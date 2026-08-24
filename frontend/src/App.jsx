import { useState } from 'react'
import NovaAnalise from './pages/NovaAnalise.jsx'
import Historico from './pages/Historico.jsx'

export default function App() {
  const [aba, setAba] = useState('nova')

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">
          Gradin<span>Score</span>
        </h1>
      </header>
      <p className="app-tagline">Análise pré-jogo com forma recente casa/fora e confrontos diretos.</p>

      <nav className="tabs">
        <button
          className={`tab-btn ${aba === 'nova' ? 'ativa' : ''}`}
          onClick={() => setAba('nova')}
        >
          Nova análise
        </button>
        <button
          className={`tab-btn ${aba === 'historico' ? 'ativa' : ''}`}
          onClick={() => setAba('historico')}
        >
          Histórico
        </button>
      </nav>

      {aba === 'nova' ? <NovaAnalise /> : <Historico />}
    </div>
  )
}
