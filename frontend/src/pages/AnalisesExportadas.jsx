import { useState } from 'react'
import { getAnalisesExportadas, getAnaliseExportada } from '../api.js'
import Report from '../components/Report.jsx'

// As mesmas 3 competições que o pipeline de automação processa hoje
// (coleta → análise primária → refinamento SofaScore → publicação).
// Se o pipeline passar a cobrir outra liga, adicionar aqui também.
const LIGAS_PIPELINE = [
  { id_api: 140, nome: 'La Liga' },
  { id_api: 39, nome: 'Premier League' },
  { id_api: 78, nome: 'Bundesliga' },
]

function formatarData(iso) {
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export default function AnalisesExportadas() {
  const [ligaAberta, setLigaAberta] = useState(null)
  const [jogosPorLiga, setJogosPorLiga] = useState({})
  const [erroPorLiga, setErroPorLiga] = useState({})
  const [fixtureSelecionado, setFixtureSelecionado] = useState(null)
  const [detalhe, setDetalhe] = useState(null)
  const [erroDetalhe, setErroDetalhe] = useState(null)

  function toggleLiga(idLiga) {
    if (ligaAberta === idLiga) {
      setLigaAberta(null)
      return
    }
    setLigaAberta(idLiga)
    if (jogosPorLiga[idLiga] === undefined) {
      getAnalisesExportadas(idLiga)
        .then((lista) => setJogosPorLiga((atual) => ({ ...atual, [idLiga]: lista })))
        .catch((e) => setErroPorLiga((atual) => ({ ...atual, [idLiga]: e.message })))
    }
  }

  function abrirJogo(fixtureId) {
    setFixtureSelecionado(fixtureId)
    setDetalhe(null)
    setErroDetalhe(null)
    getAnaliseExportada(fixtureId)
      .then(setDetalhe)
      .catch((e) => setErroDetalhe(e.message))
  }

  if (fixtureSelecionado) {
    return (
      <div>
        <button className="btn-secundario" onClick={() => setFixtureSelecionado(null)} style={{ marginBottom: 16 }}>
          ← Voltar à lista
        </button>
        {erroDetalhe && <div className="aviso-fallback">{erroDetalhe}</div>}
        {!erroDetalhe && !detalhe && <p className="campo-ajuda">Carregando…</p>}
        {detalhe && <Report resultado={detalhe.analise_primaria} refinamento={detalhe.refinamento_sofascore} />}
      </div>
    )
  }

  return (
    <div>
      {LIGAS_PIPELINE.map((liga) => {
        const aberta = ligaAberta === liga.id_api
        const jogos = jogosPorLiga[liga.id_api]
        const erro = erroPorLiga[liga.id_api]
        return (
          <div className={`liga-card ${aberta ? 'aberta' : ''}`} key={liga.id_api}>
            <div className="liga-card-header" onClick={() => toggleLiga(liga.id_api)}>
              <span className="liga-card-nome">{liga.nome}</span>
              <span className="liga-card-contagem">
                {jogos ? `${jogos.length} jogo(s)` : ''}
                <span className="liga-card-seta" style={{ marginLeft: 10 }}>›</span>
              </span>
            </div>

            {aberta && (
              <div className="liga-jogos-lista">
                {erro && <div className="aviso-fallback">{erro}</div>}
                {!erro && jogos === undefined && <p className="campo-ajuda" style={{ padding: '8px 10px' }}>Carregando…</p>}
                {!erro && jogos && jogos.length === 0 && (
                  <p className="campo-ajuda" style={{ padding: '8px 10px' }}>
                    Nenhum jogo exportado ainda pra esta competição — o pipeline publica automaticamente
                    conforme os jogos são analisados e refinados.
                  </p>
                )}
                {jogos && jogos.map((j) => (
                  <div className="jogo-item" key={j.fixture_id} onClick={() => abrirJogo(j.fixture_id)}>
                    <span className="jogo-item-confronto">{j.time_casa} × {j.time_fora}</span>
                    <span className="jogo-item-data">{formatarData(j.data_partida)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
