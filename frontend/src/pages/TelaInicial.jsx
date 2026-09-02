export default function TelaInicial({ onEscolher }) {
  return (
    <div className="escolha-inicial">
      <button className="escolha-card" onClick={() => onEscolher('exportadas')}>
        <div className="escolha-card-titulo">Ver análises completas</div>
        <div className="escolha-card-desc">
          Jogos das próximas rodadas já analisados pelo pipeline automático — forma recente,
          confrontos diretos e refinamento por tempo (SofaScore), organizados por competição.
        </div>
      </button>

      <button className="escolha-card" onClick={() => onEscolher('novas')}>
        <div className="escolha-card-titulo">Fazer nova análise</div>
        <div className="escolha-card-desc">
          Escolha qualquer competição e dois times pra gerar uma análise sob demanda,
          na hora — cobre qualquer confronto, não só os das ligas do pipeline.
        </div>
      </button>
    </div>
  )
}
