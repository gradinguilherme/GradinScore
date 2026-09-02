function linhaStat(rotulo, valor) {
  const disponivel = valor !== null && valor !== undefined
  return (
    <div className="stat-linha">
      <span className="stat-rotulo">{rotulo}</span>
      <span className={`stat-valor ${disponivel ? '' : 'indisponivel'}`}>
        {disponivel ? valor : 'sem dado'}
      </span>
    </div>
  )
}

function blocoPeriodo(rotulo, periodo) {
  const disponivel = periodo && (periodo.chutes !== null && periodo.chutes !== undefined)
  return (
    <div className="refinamento-periodo">
      <div className="refinamento-periodo-rotulo">{rotulo}</div>
      <div className="stat-linha">
        <span className="stat-rotulo">Chutes (média)</span>
        <span className={`stat-valor ${disponivel ? '' : 'indisponivel'}`}>
          {disponivel ? periodo.chutes : 'sem dado'}
        </span>
      </div>
      <div className="stat-linha">
        <span className="stat-rotulo">Chutes no alvo (média)</span>
        <span className={`stat-valor ${disponivel ? '' : 'indisponivel'}`}>
          {disponivel ? periodo.chutes_gol : 'sem dado'}
        </span>
      </div>
    </div>
  )
}

function ladoRefinamento(lado, nomeExibicao) {
  if (!lado) {
    return (
      <div className="refinamento-lado">
        <div className="refinamento-time-nome">{nomeExibicao}</div>
        <p className="campo-ajuda">Refinamento por tempo não disponível para este time.</p>
      </div>
    )
  }
  if (lado.erro) {
    return (
      <div className="refinamento-lado">
        <div className="refinamento-time-nome">{nomeExibicao}</div>
        <p className="campo-ajuda">{lado.erro}</p>
      </div>
    )
  }
  return (
    <div className="refinamento-lado">
      <div className="refinamento-time-nome">{lado.nome_sofascore || nomeExibicao}</div>
      {blocoPeriodo('1º tempo', lado.t1)}
      {blocoPeriodo('2º tempo', lado.t2)}
      {blocoPeriodo('Total do jogo', lado.total)}
      <div className="campo-ajuda">Baseado em {lado.jogos_considerados ?? 0} jogo(s) considerado(s).</div>
      {lado.obs && <div className="campo-ajuda" style={{ fontStyle: 'italic' }}>{lado.obs}</div>}
    </div>
  )
}

export default function Report({ resultado, refinamento }) {
  if (!resultado) return null
  const { liga, time_casa, time_fora, casa, fora, h2h, fallback, data_partida } = resultado

  return (
    <div className="relatorio">
      <div className="relatorio-cabecalho">
        <div className="relatorio-confronto">
          {time_casa} <span style={{ color: 'var(--chalk-dim)' }}>×</span> {time_fora}
        </div>
        <div className="relatorio-meta">
          {liga}
          {data_partida ? ` · ${data_partida}` : ''}
        </div>
      </div>

      {fallback && (
        <div className="aviso-fallback" style={{ margin: '16px 20px 0' }}>
          Esta competição não tem estatísticas de chutes disponíveis na fonte de dados —
          a análise abaixo usa só gols e confrontos diretos
          {refinamento ? ', mas o refinamento por tempo abaixo (SofaScore) traz chutes mesmo assim.' : '.'}
        </div>
      )}

      <div className="time-sheet">
        <div className="time-coluna casa">
          <div className="time-nome">{time_casa} <span style={{ color: 'var(--chalk-dim)', fontSize: 13 }}>(casa)</span></div>
          {linhaStat('Gols marcados (média)', casa.gols_marcados)}
          {linhaStat('Gols sofridos (média)', casa.gols_sofridos)}
          {!fallback && linhaStat('Chutes (média)', casa.chutes)}
          {!fallback && linhaStat('Chutes ao gol (média)', casa.chutes_gol)}
          {!fallback && linhaStat('Chutes sofridos (média)', casa.chutes_sofridos)}
          {!fallback && linhaStat('Chutes ao gol sofridos (média)', casa.chutes_gol_sofridos)}
          <div className="campo-ajuda" style={{ marginTop: 8 }}>
            Baseado nos últimos {casa.jogos_considerados} jogos em casa.
          </div>
        </div>

        <div className="time-divisor" />

        <div className="time-coluna fora">
          <div className="time-nome"><span style={{ color: 'var(--chalk-dim)', fontSize: 13 }}>(fora)</span> {time_fora}</div>
          {linhaStat('Gols marcados (média)', fora.gols_marcados)}
          {linhaStat('Gols sofridos (média)', fora.gols_sofridos)}
          {!fallback && linhaStat('Chutes (média)', fora.chutes)}
          {!fallback && linhaStat('Chutes ao gol (média)', fora.chutes_gol)}
          {!fallback && linhaStat('Chutes sofridos (média)', fora.chutes_sofridos)}
          {!fallback && linhaStat('Chutes ao gol sofridos (média)', fora.chutes_gol_sofridos)}
          <div className="campo-ajuda" style={{ marginTop: 8, textAlign: 'right' }}>
            Baseado nos últimos {fora.jogos_considerados} jogos fora.
          </div>
        </div>
      </div>

      <div className="h2h-central">
        <div className="h2h-titulo">Confrontos diretos</div>
        {h2h && h2h.length > 0 ? (
          <div className="h2h-lista">
            {h2h.map((jogo, i) => (
              <div className="h2h-jogo" key={i}>
                <span className="h2h-data">{jogo.data}</span>
                <span className="h2h-mandante">{jogo.mandante}</span>
                <span className="h2h-placar">{jogo.placar}</span>
                <span className="h2h-visitante">{jogo.visitante}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="h2h-vazio">Nenhum confronto direto recente registrado.</div>
        )}
      </div>

      {refinamento && (
        <div className="refinamento-sofascore">
          <div className="h2h-titulo">Refinamento por tempo (SofaScore)</div>
          <div className="refinamento-grid">
            {ladoRefinamento(refinamento.mandante, time_casa)}
            {ladoRefinamento(refinamento.visitante, time_fora)}
          </div>
        </div>
      )}
    </div>
  )
}
