import { useState, useEffect } from 'react'
import { getLigas, gerarAnalise } from '../api.js'
import TeamSearch from '../components/TeamSearch.jsx'
import LeagueSearch from '../components/LeagueSearch.jsx'
import Report from '../components/Report.jsx'

export default function NovaAnalise() {
  const [ligas, setLigas] = useState([])
  const [liga, setLiga] = useState(null)
  const [timeCasa, setTimeCasa] = useState(null)
  const [timeFora, setTimeFora] = useState(null)
  const [dataPartida, setDataPartida] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)
  const [resultado, setResultado] = useState(null)

  useEffect(() => {
    getLigas().then(setLigas).catch(() => setErro('Não foi possível carregar as competições.'))
  }, [])

  const passo1ok = Boolean(liga)
  const passo2ok = Boolean(timeCasa && timeFora)

  function onMudarLiga(novaLiga) {
    setLiga(novaLiga)
    setTimeCasa(null)
    setTimeFora(null)
    setResultado(null)
  }

  async function onGerar() {
    setCarregando(true)
    setErro(null)
    setResultado(null)
    try {
      const dados = await gerarAnalise({
        id_liga: liga.id_api,
        id_time_casa: timeCasa.id_api,
        id_time_fora: timeFora.id_api,
        data_partida: dataPartida || null,
      })
      setResultado(dados)
    } catch (e) {
      setErro(e.message)
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div>
      <div className="guia-passos">
        <div className={`guia-passo ${passo1ok ? 'concluido' : 'ativo'}`}>
          <span className="guia-passo-numero">Passo 1</span>
          <span className="guia-passo-texto">Escolha a competição</span>
        </div>
        <div className={`guia-passo ${passo2ok ? 'concluido' : passo1ok ? 'ativo' : ''}`}>
          <span className="guia-passo-numero">Passo 2</span>
          <span className="guia-passo-texto">Selecione os dois times</span>
        </div>
        <div className={`guia-passo ${resultado ? 'concluido' : passo2ok ? 'ativo' : ''}`}>
          <span className="guia-passo-numero">Passo 3</span>
          <span className="guia-passo-texto">Gere a análise</span>
        </div>
      </div>

      <div className="cartao">
        <LeagueSearch ligas={ligas} selecionada={liga} onSelecionar={onMudarLiga} />

        {liga && !liga.tem_estatisticas && (
          <div className="aviso-fallback">
            {liga.nome} não tem dados de chutes disponíveis na fonte — a análise vai trazer
            só gols e confrontos diretos.
          </div>
        )}

        {liga && (
          <>
            <TeamSearch
              idLiga={liga.id_api}
              label="Time da casa"
              ajuda="Comece a digitar o nome do time. Competições de mata-mata podem ter centenas de clubes cadastrados — a busca filtra conforme você digita."
              selecionado={timeCasa}
              onSelecionar={setTimeCasa}
            />
            <TeamSearch
              idLiga={liga.id_api}
              label="Time visitante"
              selecionado={timeFora}
              onSelecionar={setTimeFora}
            />
            <div className="campo">
              <label htmlFor="data-partida">Data da partida (opcional)</label>
              <input
                id="data-partida"
                type="date"
                value={dataPartida}
                onChange={(e) => setDataPartida(e.target.value)}
              />
              <p className="campo-ajuda">Só para identificar o relatório — não afeta os dados buscados.</p>
            </div>
          </>
        )}

        {erro && <div className="aviso-fallback">{erro}</div>}

        <button
          className="btn-primario"
          disabled={!passo2ok || carregando}
          onClick={onGerar}
        >
          {carregando ? 'Buscando dados…' : 'Gerar análise'}
        </button>
      </div>

      {resultado && <Report resultado={resultado} />}
    </div>
  )
}
