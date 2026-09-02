import { useState } from 'react'
import TelaInicial from './pages/TelaInicial.jsx'
import AnalisesExportadas from './pages/AnalisesExportadas.jsx'
import NovaAnalise from './pages/NovaAnalise.jsx'
import Historico from './pages/Historico.jsx'

export default function App() {
  const [tela, setTela] = useState('home') // 'home' | 'exportadas' | 'novas'
  const [aba, setAba] = useState('nova') // sub-aba de 'novas': 'nova' | 'historico'

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">
          Gradin<span>Score</span>
        </h1>
        {tela !== 'home' && (
          <button className="btn-secundario" onClick={() => setTela('home')}>
            ← Início
          </button>
        )}
      </header>

      {tela === 'home' && (
        <>
          <p className="app-tagline">Análise pré-jogo com forma recente casa/fora e confrontos diretos.</p>
          <TelaInicial onEscolher={setTela} />
        </>
      )}

      {tela === 'exportadas' && (
        <>
          <p className="app-tagline">Jogos já processados pelo pipeline automático, por competição.</p>
          <AnalisesExportadas />
        </>
      )}

      {tela === 'novas' && (
        <>
          <p className="app-tagline">Gere uma análise sob demanda pra qualquer competição e times cadastrados.</p>
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
        </>
      )}
    </div>
  )
}
