import { useState } from 'react'
import { nomeLigaExibicao, ligaCasaComBusca } from '../data/nomesLigas.js'

export default function LeagueSearch({ ligas, selecionada, onSelecionar }) {
  const [termo, setTermo] = useState('')
  const [aberto, setAberto] = useState(false)

  const resultados = termo.length >= 1
    ? ligas.filter((l) => ligaCasaComBusca(l, termo))
    : ligas

  if (selecionada) {
    return (
      <div className="campo">
        <label>Competição</label>
        <div className="time-selecionado">
          <span>{nomeLigaExibicao(selecionada)}</span>
          <button type="button" onClick={() => onSelecionar(null)} aria-label="Trocar competição">
            ×
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="campo">
      <label htmlFor="busca-liga">Competição</label>
      <div className="busca-time">
        <input
          id="busca-liga"
          type="text"
          value={termo}
          placeholder="Digite em português ou inglês — ex: brasileirão, premier league…"
          onChange={(e) => setTermo(e.target.value)}
          onFocus={() => setAberto(true)}
          onBlur={() => setTimeout(() => setAberto(false), 150)}
          autoComplete="off"
        />
        {aberto && resultados.length > 0 && (
          <div className="busca-resultados">
            {resultados.map((l) => (
              <div
                key={l.id_api}
                className="busca-resultado-item"
                onMouseDown={() => {
                  onSelecionar(l)
                  setAberto(false)
                  setTermo('')
                }}
              >
                <span>{nomeLigaExibicao(l)}</span>
                {!l.tem_estatisticas && (
                  <span style={{ color: 'var(--alerta)', fontSize: 12 }}>sem chutes</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      <p className="campo-ajuda">
        As 18 competições cadastradas cobrem as 5 grandes ligas europeias e suas copas,
        Champions/Europa/Conference League, Brasileirão A e B, Copa do Brasil, Libertadores
        e Sul-Americana.
      </p>
    </div>
  )
}
