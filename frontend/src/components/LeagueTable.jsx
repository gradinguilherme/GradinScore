import { useState } from 'react'
import { getTabela } from '../api.js'

export default function LeagueTable({ liga }) {
  const [aberta, setAberta] = useState(false)
  const [tabela, setTabela] = useState(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)

  if (!liga || !liga.eh_liga_pontos_corridos) return null

  async function alternar() {
    if (aberta) {
      setAberta(false)
      return
    }
    setAberta(true)
    if (tabela) return // já carregada, não busca de novo
    setCarregando(true)
    setErro(null)
    try {
      const dados = await getTabela(liga.id_api)
      setTabela(dados)
    } catch (e) {
      setErro(e.message)
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="campo">
      <button type="button" className="btn-secundario" onClick={alternar}>
        {aberta ? '▲ Ocultar tabela' : '▼ Ver tabela da liga'}
      </button>

      {aberta && (
        <div style={{ marginTop: 12 }}>
          {carregando && <p className="campo-ajuda">Carregando tabela…</p>}
          {erro && <div className="aviso-fallback">{erro}</div>}
          {tabela && tabela.length > 0 && (
            <table className="tabela-classificacao">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Time</th>
                  <th>Pts</th>
                  <th>J</th>
                  <th>V</th>
                  <th>E</th>
                  <th>D</th>
                  <th>SG</th>
                </tr>
              </thead>
              <tbody>
                {tabela.map((t) => (
                  <tr key={t.posicao}>
                    <td>{t.posicao}</td>
                    <td>{t.time}</td>
                    <td>{t.pontos}</td>
                    <td>{t.jogos}</td>
                    <td>{t.vitorias}</td>
                    <td>{t.empates}</td>
                    <td>{t.derrotas}</td>
                    <td>{t.saldo_gols}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tabela && tabela.length === 0 && (
            <p className="campo-ajuda">Tabela não disponível para esta competição no momento.</p>
          )}
        </div>
      )}
    </div>
  )
}
