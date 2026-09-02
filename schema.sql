-- Schema do banco local (SQLite) para o web app de análise pré-jogo.
-- Rodar uma vez: sqlite3 analises.db < schema.sql

CREATE TABLE IF NOT EXISTS ligas (
    id_api INTEGER PRIMARY KEY,      -- id retornado pela API-Football (ex: 71 = Brasileirão)
    nome TEXT NOT NULL,
    pais TEXT NOT NULL,
    tem_estatisticas INTEGER NOT NULL DEFAULT 1,  -- 0 = sem statistics_fixtures (ex: Bundesliga) -> usar fallback
    eh_liga_pontos_corridos INTEGER NOT NULL DEFAULT 0,  -- 1 = liga de tabela única (mostra classificação), 0 = copa/mata-mata
    temporada_atual INTEGER,         -- ano da temporada corrente confirmada (ex: 2026)
    atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS times (
    id_api INTEGER NOT NULL,         -- id do time na API-Football — NÃO é único sozinho:
                                      -- o mesmo time pode aparecer em mais de uma competição
                                      -- (ex: Palmeiras no Brasileirão E na Copa do Brasil)
    nome TEXT NOT NULL,
    id_liga INTEGER NOT NULL,
    pais TEXT NOT NULL,
    PRIMARY KEY (id_api, id_liga),
    FOREIGN KEY (id_liga) REFERENCES ligas(id_api)
);

CREATE INDEX IF NOT EXISTS idx_times_liga ON times(id_liga);

-- Formato compacto: só os números finais já calculados, não os fixtures brutos.
-- resultado_json guarda algo como:
-- {"casa": {"gols":1.4,"gols_sofridos":1.0,"xg":1.57,"xg_sofrido":0.63,"chutes":15.6,"chutes_gol":5.2},
--  "fora":  {...},
--  "h2h": [{"data":"2026-08-09","placar":"0-0","mandante":"Bahia"}, ...],
--  "fallback": false}
CREATE TABLE IF NOT EXISTS analises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_liga INTEGER NOT NULL,
    id_time_casa INTEGER NOT NULL,
    id_time_fora INTEGER NOT NULL,
    data_partida TEXT,
    resultado_json TEXT NOT NULL,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_liga) REFERENCES ligas(id_api),
    FOREIGN KEY (id_time_casa, id_liga) REFERENCES times(id_api, id_liga),
    FOREIGN KEY (id_time_fora, id_liga) REFERENCES times(id_api, id_liga)
);

CREATE INDEX IF NOT EXISTS idx_analises_criado ON analises(criado_em);

-- Retenção: apaga análises com mais de 30 dias.
-- Rodar isso a cada início do app (é barato, não precisa de cron/task scheduler separado).
-- DELETE FROM analises WHERE criado_em < datetime('now', '-30 days');

-- Etapa 4 do pipeline de automação (Claude): análises já refinadas (API-Football + SofaScore)
-- publicadas pelo backend pra alimentar a tela "Ver análises completas" do frontend.
-- fixture_id é o id do jogo na API-Football — chave natural, evita duplicar o mesmo jogo
-- se a etapa 4 rodar de novo pro mesmo fixture (POST faz upsert por fixture_id).
CREATE TABLE IF NOT EXISTS analises_finais_exportadas (
    fixture_id INTEGER PRIMARY KEY,
    id_liga INTEGER NOT NULL,
    liga TEXT NOT NULL,
    id_time_casa INTEGER NOT NULL,
    time_casa TEXT NOT NULL,
    id_time_fora INTEGER NOT NULL,
    time_fora TEXT NOT NULL,
    data_partida TEXT NOT NULL,
    analise_primaria_json TEXT NOT NULL,   -- corpo completo da resposta de /analise (API-Football)
    refinamento_sofascore_json TEXT NOT NULL,  -- {"mandante": {...}, "visitante": {...}}
    exportado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_liga) REFERENCES ligas(id_api)
);

CREATE INDEX IF NOT EXISTS idx_analises_finais_liga_data ON analises_finais_exportadas(id_liga, data_partida);

-- Retenção: apaga jogos já disputados (não por data de exportação — por data de partida).
-- Rodar no startup do backend, igual limpar_analises_antigas.
-- DELETE FROM analises_finais_exportadas WHERE data_partida < datetime('now', '-1 day');
