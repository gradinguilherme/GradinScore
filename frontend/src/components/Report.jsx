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

export default function Report({ resultado }) {
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
          a análise abaixo usa só gols e confrontos diretos.
        </div>
      )}

      <div className="time-sheet">
        <div className="time-coluna casa">
          <div className="time-nome">{time_casa} <span style={{ color: 'var(--chalk-dim)', fontSize: 13 }}>(casa)</span></div>
          {linhaStat('Gols marcados (média)', casa.gols_marcados)}
          {linhaStat('Gols sofridos (média)', casa.gols_sofridos)}
          {!fallback && linhaStat('Chutes (média)', casa.chutes)}
          {!fallback && linhaStat('Chutes ao gol (média)', casa.chutes_gol)}
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
    </div>
  )
}
