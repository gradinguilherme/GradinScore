# GradinScore

Aplicativo de análise pré-jogo de futebol: forma recente separada por mando de campo, confrontos diretos e estatísticas de chutes, com um pipeline de automação que roda sozinho ao longo do dia.

Aplicação em produção: backend FastAPI e frontend React na Vercel, banco Turso (libSQL).

## Problema

Nasceu de uma tarefa manual: análise pré-jogo para apoiar decisão pessoal, feita algumas vezes por semana, coletando números à mão no Sofascore ou 365scores. O processo não escalava para mais de um ou dois jogos por vez e era frágil, quebrando toda vez que a interface do site mudava, o que de fato aconteceu na v1 (uma skill que navegava essas páginas via automação de browser). Scraping de tela também carregava risco de bloqueio por padrão de tráfego e limite de chamadas por execução em lote.

A solução foi migrar para uma API estruturada (API-Football, plano Pro) e construir um app completo em torno disso: backend FastAPI, banco Turso em produção e um pipeline de automação de 4 etapas que roda via tarefas agendadas.

## Decisões de arquitetura

**Camada de conexão dual (`backend/db.py`).** SQLite local para desenvolvimento e libsql (Turso) em produção, atrás da mesma interface (`.query` / `.executar`), escolhida automaticamente pela presença de `TURSO_DATABASE_URL`. Evita ramificação de código por ambiente, mas os dois bancos não se comportam igual em tudo: SQLite só aplica foreign key se `PRAGMA foreign_keys = ON` for setado explicitamente, Turso aplica por padrão. Qualquer migração que mexa em tabela referenciada por FK precisa desligar essa checagem antes do `DROP TABLE` e religar depois, senão o teste local passa e a produção quebra.

**Chave composta em `times` (`id_api`, `id_liga`).** Um mesmo time pode disputar mais de uma competição (Palmeiras no Brasileirão e na Copa do Brasil, por exemplo). A versão inicial usava `id_api` sozinho como chave, e `INSERT OR IGNORE` descartava silenciosamente o cadastro do time na segunda competição. A correção recria a tabela com chave composta sem perder dado; a migração está em `popular_banco.py` (`migrar_pk_times_composta`).

**Hospedagem: Vercel + Turso, não GitHub Pages.** GitHub Pages só serve estático, sem backend nem disco persistente. Ambiente serverless não mantém disco entre invocações, por isso Turso em vez de SQLite em produção. São dois projetos Vercel separados (frontend e backend), cada um com Root Directory própria, ambos apontando para este repositório, branch `main`.

**Modelo de análise.** Forma recente é sempre separada por mando de campo — últimos 5 jogos do mandante jogando em casa, últimos 5 do visitante jogando fora, nunca misturados, porque essa separação é o ponto central do modelo. H2H é filtrado só por jogos finalizados (status `FT`). Chutes e chutes ao gol sofridos exigem buscar a estatística do adversário no mesmo fixture, dobrando as chamadas por análise — aceito porque era prioridade declarada, ao contrário do xG, descartado por vir `null` consistentemente sem causa determinada. Quando a competição não tem cobertura de chutes (hoje só a Bundesliga na API-Football), a análise cai num fallback de gols + H2H com aviso explícito; o pipeline de automação compensa isso com um campo `total` de chutes vindo do SofaScore, calculado para todas as ligas monitoradas — manter um único cálculo é mais simples do que uma exceção por liga.

**Pipeline de automação.** 4 etapas sequenciais via tarefas agendadas, orquestradas fora deste repositório: coleta de jogos (API-Football), análise primária (API-Football), refinamento por tempo de jogo (SofaScore) e publicação no app via `POST /analises-finais`. O estado do pipeline entre etapas vive em arquivos de controle externos, não no banco do app — o banco só recebe o resultado final publicado. Cada etapa limpa do seu próprio estado os jogos cuja data já passou. A etapa de refinamento por SofaScore depende de navegação de página (não é chamada HTTP pura), o que a torna o ponto mais frágil da automação. Há retenção automática no banco: 30 dias para `analises`, 1 dia após a data da partida para `analises_finais_exportadas`, limpa a cada startup do backend.

## Como rodar

Localmente:

```bash
# backend
cd backend
pip install -r requirements.txt
# .env na raiz do projeto (git-ignorado), com API_FOOTBALL_KEY
uvicorn main:app --reload

# popular o banco (schema.sql é a fonte única de schema)
python popular_banco.py

# frontend
cd frontend
npm install
npm run dev
```

`schema.sql` é lido tanto por `popular_banco.py` quanto por `backend/db.py`. Qualquer mudança em `schema.sql` precisa vir acompanhada de uma função de migração correspondente em `popular_banco.py`, testada nos dois ambientes, bancos já existentes não são recriados automaticamente.

Diagnóstico ad-hoc: `consultar_times.py` (times cadastrados de uma liga) e `diagnostico_fixtures.py` (fixtures por fase/round de uma competição).

Em produção, o deploy é automático pelos dois projetos Vercel, disparado por push na branch `main`. Variáveis de ambiente (`TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `API_FOOTBALL_KEY`, `FRONTEND_URL`) são configuradas no dashboard da Vercel, não em arquivo. No Turso, o schema é aplicado manualmente uma vez; não há migração automática de schema em produção ainda.

## O que foi testado

Não há suite de teste automatizado. A validação é manual: cada migração em `popular_banco.py` é testada nos dois ambientes (SQLite local e Turso) antes de ir para produção, e os dois scripts de diagnóstico servem para conferir dado cadastrado contra a API-Football depois de qualquer mudança de schema. Esse é um gap conhecido, não um limite de escopo — testes automatizados de migração e de rota de API são a melhoria mais óbvia se o projeto continuar recebendo trabalho.

## Limitações

- Cobertura de estatísticas de chutes não existe para Bundesliga na API-Football; depende do fallback via SofaScore para preencher a lacuna.
- xG não está disponível: retorno `null` mesmo em ligas com cobertura confirmada, causa não diagnosticada.
- Tabela de classificação só existe para as 7 ligas de pontos corridos monitoradas pelo pipeline; copas e torneios de grupo mais mata-mata não têm essa exibição.
- `LIGAS_PIPELINE`, em `frontend/src/pages/AnalisesExportadas.jsx`, é hardcoded e não lê de `/ligas` como o resto do frontend — se o pipeline passar a cobrir outra liga, precisa ser atualizado manualmente.
- A etapa de refinamento por SofaScore é a única do pipeline que não roda puramente via chamada HTTP, o que a torna o ponto de falha mais provável da automação.
- Os tetos de segurança que existiam nas etapas de análise primária e refinamento (20 e 15 jogos por execução) foram removidos; o volume hoje só é limitado pela janela de 3 dias da coleta, o que significa que cobrir mais ligas no futuro cresce o custo de processamento sem limite superior automático.
- Sem suite de teste automatizado (ver seção anterior).
