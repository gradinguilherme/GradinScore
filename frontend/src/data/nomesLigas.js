// Nomes em português e apelidos buscáveis, por id_api da liga.
// Para adicionar mais formas de busca (abreviações, apelidos regionais etc.),
// inclua strings no array "aliases" — a busca do dropdown usa nome (API),
// nomePt e todos os aliases combinados.
//
// Ids conferidos nos testes anteriores (ver popular_banco.py para a lista completa).

export const NOMES_LIGAS = {
  39:  { nomePt: 'Premier League', aliases: ['inglaterra', 'inglesa', 'premiere league'] },
  140: { nomePt: 'La Liga', aliases: ['espanha', 'espanhola', 'laliga'] },
  135: { nomePt: 'Serie A Italiana', aliases: ['italia', 'italiana', 'calcio'] },
  78:  { nomePt: 'Bundesliga', aliases: ['alemanha', 'alema'] },
  61:  { nomePt: 'Ligue 1', aliases: ['franca', 'francesa'] },
  45:  { nomePt: 'Copa da Inglaterra', aliases: ['fa cup', 'inglaterra copa'] },
  143: { nomePt: 'Copa do Rei', aliases: ['copa del rey', 'espanha copa'] },
  137: { nomePt: 'Copa da Italia', aliases: ['coppa italia', 'italia copa'] },
  81:  { nomePt: 'Copa da Alemanha', aliases: ['dfb pokal', 'alemanha copa'] },
  66:  { nomePt: 'Copa da Franca', aliases: ['coupe de france', 'franca copa'] },
  2:   { nomePt: 'Liga dos Campeoes', aliases: ['champions league', 'champions'] },
  3:   { nomePt: 'Liga Europa', aliases: ['europa league'] },
  848: { nomePt: 'Liga Conferencia', aliases: ['conference league', 'europa conference'] },
  71:  { nomePt: 'Brasileirao Serie A', aliases: ['brasileirao', 'serie a brasil', 'brasil'] },
  72:  { nomePt: 'Brasileirao Serie B', aliases: ['serie b brasil'] },
  73:  { nomePt: 'Copa do Brasil', aliases: [] },
  13:  { nomePt: 'Libertadores', aliases: ['conmebol libertadores'] },
  11:  { nomePt: 'Sul-Americana', aliases: ['sudamericana', 'conmebol sudamericana'] },
}

export function nomeLigaExibicao(liga) {
  const traducao = NOMES_LIGAS[liga.id_api]
  return traducao ? `${traducao.nomePt} (${liga.pais})` : `${liga.nome} (${liga.pais})`
}

export function ligaCasaComBusca(liga, termoBusca) {
  const traducao = NOMES_LIGAS[liga.id_api]
  const alvo = [
    liga.nome,
    traducao?.nomePt || '',
    ...(traducao?.aliases || []),
  ]
    .join(' ')
    .toLowerCase()
  return alvo.includes(termoBusca.toLowerCase())
}
