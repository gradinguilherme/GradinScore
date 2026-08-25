"""
Popula o banco local (analises.db) com ligas e times das competições confirmadas.
Idempotente: pode ser interrompido e rodado de novo sem duplicar dado (usa INSERT OR IGNORE).

Antes de rodar:
    1. sqlite3 analises.db < schema.sql   (cria as tabelas, uma vez só)
    2. Windows (PowerShell): $env:API_FOOTBALL_KEY = "sua_chave_aqui"
    3. python popular_banco.py

No free tier (100 req/dia), isso NÃO termina numa execução só — rode em partes ao
longo de alguns dias, ou de uma vez após assinar o Pro (7.500 req/dia).
O script pula ligas já totalmente populadas automaticamente.
"""

import os
import sqlite3
import time
import requests

API_KEY = os.environ.get("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
# Caminho relativo à pasta do próprio script — funciona não importa de onde o PowerShell é chamado
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PASTA_SCRIPT, "analises.db")
SCHEMA_PATH = os.path.join(PASTA_SCRIPT, "schema.sql")

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

if not API_KEY:
    raise SystemExit(
        "Variável de ambiente API_FOOTBALL_KEY não encontrada.\n"
        "Defina antes de rodar: $env:API_FOOTBALL_KEY = 'sua_chave'"
    )

HEADERS = {"x-apisports-key": API_KEY}


def conectar():
    """Retorna conexão com Turso se TURSO_DATABASE_URL estiver definida, senão SQLite local.
    Para popular o banco de produção, defina TURSO_DATABASE_URL e TURSO_AUTH_TOKEN antes de rodar."""
    if TURSO_URL:
        import libsql
        print(f"[conectando ao Turso: {TURSO_URL}]")
        return libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
    print(f"[conectando ao SQLite local: {DB_PATH}]")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def rodar_script(conn, sql_texto):
    """Roda um schema.sql inteiro — funciona igual em sqlite3 e libsql, sem depender de executescript.
    Filtra linhas de comentário: um trecho que sobra só com comentário (ex: nota final do schema.sql)
    quebra no Turso, que rejeita "statement" sem SQL real — o SQLite local é mais tolerante com isso."""
    for bruto in sql_texto.split(";"):
        linhas_uteis = [l for l in bruto.splitlines() if l.strip() and not l.strip().startswith("--")]
        instrucao = "\n".join(linhas_uteis).strip()
        if not instrucao:
            continue
        conn.execute(instrucao)
    conn.commit()


def inserir_varios(conn, sql, linhas):
    """Substitui executemany — evita depender de comportamento específico do driver."""
    for linha in linhas:
        conn.execute(sql, linha)
    conn.commit()


def garantir_schema(conn):
    """Cria as tabelas a partir do schema.sql se ainda não existirem."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        rodar_script(conn, f.read())


def migrar_colunas_novas(conn):
    """Adiciona colunas novas em bancos que já existiam antes delas serem criadas no schema.sql
    — evita ter que apagar e recriar o banco (local ou Turso) toda vez que o schema evolui.
    Seguro rodar sempre: se a coluna já existe (banco novo, criado direto com ela), só ignora."""
    try:
        conn.execute("ALTER TABLE ligas ADD COLUMN eh_liga_pontos_corridos INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print("[migração] coluna eh_liga_pontos_corridos adicionada à tabela ligas.")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            pass  # coluna já existe — nada a fazer
        else:
            raise

# Ligas já confirmadas nos testes anteriores:
# (id_api, nome, pais, tem_estatisticas, eh_liga_pontos_corridos, temporada_atual)
LIGAS_CONFIRMADAS = [
    (39,  "Premier League", "England", 1, 1, 2026),
    (140, "La Liga", "Spain", 1, 1, 2026),
    (135, "Serie A", "Italy", 1, 1, 2026),
    (78,  "Bundesliga", "Germany", 0, 1, 2026),  # sem statistics_fixtures — fica no fallback
    (61,  "Ligue 1", "France", 1, 1, 2026),
    (45,  "FA Cup", "England", 1, 0, 2025),      # sem flag "current", mas 2025 confirmado com estatística
    (143, "Copa del Rey", "Spain", 1, 0, 2025),
    (137, "Coppa Italia", "Italy", 1, 0, 2026),
    (81,  "DFB Pokal", "Germany", 1, 0, 2026),
    (66,  "Coupe de France", "France", 1, 0, 2025),
    (2,   "UEFA Champions League", "World", 1, 0, 2026),
    (3,   "UEFA Europa League", "World", 1, 0, 2026),
    (848, "UEFA Europa Conference League", "World", 1, 0, 2026),
    (71,  "Serie A", "Brazil", 1, 1, 2026),
    (72,  "Serie B", "Brazil", 1, 1, 2026),
    (73,  "Copa Do Brasil", "Brazil", 1, 0, 2026),
    (13,  "CONMEBOL Libertadores", "World", 1, 0, 2026),
    (11,  "CONMEBOL Sudamericana", "World", 1, 0, 2026),
]


def get(endpoint, params=None, tentativas=2):
    for tentativa in range(tentativas):
        resp = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params or {})
        resp.raise_for_status()
        data = resp.json()
        remaining = resp.headers.get("x-ratelimit-requests-remaining")
        limit = resp.headers.get("x-ratelimit-requests-limit")
        errors = data.get("errors")
        if errors and "rateLimit" in errors and tentativa < tentativas - 1:
            print("    [rate limit por minuto, aguardando 15s]")
            time.sleep(15)
            continue
        if errors:
            print(f"    [ERRO] {errors}")
        print(f"    [status] {endpoint} -> {resp.status_code} | restantes hoje: {remaining}/{limit}")
        return data


def liga_ja_populada(conn, id_liga):
    cur = conn.execute("SELECT COUNT(*) FROM times WHERE id_liga = ?", (id_liga,))
    return cur.fetchone()[0] > 0


def popular_ligas(conn):
    inserir_varios(
        conn,
        """INSERT OR REPLACE INTO ligas (id_api, nome, pais, tem_estatisticas, eh_liga_pontos_corridos, temporada_atual)
           VALUES (?, ?, ?, ?, ?, ?)""",
        LIGAS_CONFIRMADAS,
    )
    print(f"[OK] {len(LIGAS_CONFIRMADAS)} ligas registradas/atualizadas na tabela ligas.\n")


def popular_times(conn):
    for id_liga, nome_liga, pais, tem_stats, eh_liga, temporada in LIGAS_CONFIRMADAS:
        if liga_ja_populada(conn, id_liga):
            print(f"[SKIP] {nome_liga} ({pais}) já tem times cadastrados — pulando.")
            continue

        print(f"Buscando times de: {nome_liga} ({pais}) — liga id={id_liga}, temporada {temporada}")
        data = get("teams", {"league": id_liga, "season": temporada})
        if data is None:
            print(f"  [FALHOU] sem resposta para {nome_liga}, tente rodar de novo depois.")
            time.sleep(7)
            continue

        times_resp = data.get("response", [])
        linhas = [
            (t["team"]["id"], t["team"]["name"], id_liga, t["team"]["country"])
            for t in times_resp
        ]
        inserir_varios(
            conn,
            "INSERT OR IGNORE INTO times (id_api, nome, id_liga, pais) VALUES (?, ?, ?, ?)",
            linhas,
        )
        print(f"  [OK] {len(linhas)} times inseridos para {nome_liga}.\n")

        time.sleep(7)  # free tier: 10 req/min


if __name__ == "__main__":
    conn = conectar()
    garantir_schema(conn)
    migrar_colunas_novas(conn)

    print("=== Populando tabela de ligas ===")
    popular_ligas(conn)

    print("=== Populando times por liga (idempotente — pode rodar em várias sessões) ===")
    popular_times(conn)

    total_times = conn.execute("SELECT COUNT(*) FROM times").fetchone()[0]
    total_ligas_completas = conn.execute(
        """SELECT COUNT(DISTINCT id_liga) FROM times"""
    ).fetchone()[0]
    print(f"\n=== Resumo: {total_times} times cadastrados, cobrindo {total_ligas_completas}/{len(LIGAS_CONFIRMADAS)} ligas ===")
    if total_ligas_completas < len(LIGAS_CONFIRMADAS):
        print("Rode o script de novo (hoje ou amanhã, conforme sua cota) para completar as ligas restantes.")

    conn.close()
