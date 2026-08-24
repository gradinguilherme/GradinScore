import { useState, useEffect } from 'react'
import { getHistorico } from '../api.js'
import Report from '../components/Report.jsx'

export default function Historico() {
  const [itens, setItens] = useState(null)
  const [selecionado, setSelecionado] = useState(null)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    getHistorico()
      .then(setItens)
      .catch(() => setErro('Não foi possível carregar o histórico.'))
  }, [])

  if (erro) return <div className="aviso-fallback">{erro}</div>
  if (itens === null) return <p className="campo-ajuda">Carregando…</p>

  if (itens.length === 0) {
    return (
      <div className="estado-vazio">
        <div className="estado-vazio-titulo">Ainda não há nenhuma análise aqui</div>
        <p>Gere sua primeira na aba "Nova análise" — ela aparece aqui automaticamente.</p>
      </div>
    )
  }

  return (
    <div>
      <p className="aviso-retencao">
        Análises ficam guardadas por 30 dias e depois são apagadas automaticamente.
      </p>

      {selecionado ? (
        <div>
          <button className="btn-secundario" onClick={() => setSelecionado(null)} style={{ marginBottom: 16 }}>
            ← Voltar ao histórico
          </button>
          <Report resultado={selecionado.resultado} />
        </div>
      ) : (
        itens.map((item) => (
          <div className="historico-item" key={item.id} onClick={() => setSelecionado(item)}>
            <div>
              <div className="historico-confronto">
                {item.time_casa} × {item.time_fora}
              </div>
              <div className="historico-meta">{item.liga}</div>
            </div>
            <div className="historico-meta">
              {item.data_partida || new Date(item.criado_em).toLocaleDateString('pt-BR')}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
