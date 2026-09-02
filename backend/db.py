"""
Conexao de banco que funciona em dois modos, escolhidos automaticamente:
- Local (dev): SQLite no arquivo analises.db, se TURSO_DATABASE_URL nao estiver definida.
- Producao (Vercel): Turso/libSQL, se TURSO_DATABASE_URL e TURSO_AUTH_TOKEN estiverem definidas.

Nenhum outro arquivo do backend precisa saber qual dos dois esta em uso.
"""

import os
import sqlite3

PASTA_BACKEND = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PASTA_BACKEND, "..", "analises.db")
SCHEMA_PATH = os.path.join(PASTA_BACKEND, "..", "schema.sql")

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")


class Conexao:
    """Abstrai SQLite local e Turso atras da mesma interface (.query / .executar)."""

    def __init__(self):
        if TURSO_URL:
            import libsql  # so importa se realmente for usar - evita exigir o pacote em dev local
            self._conn = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
            self.modo = "turso"
        else:
            self._conn = sqlite3.connect(DB_PATH)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self.modo = "sqlite"

    def query(self, sql, params=()):
        """SELECT - sempre retorna lista de dicts, independente do driver por tras."""
        cur = self._conn.execute(sql, params)
        colunas = [c[0] for c in cur.description]
        return [dict(zip(colunas, linha)) for linha in cur.fetchall()]

    def executar(self, sql, params=()):
        """INSERT/UPDATE/DELETE de uma linha - ja da commit."""
        self._conn.execute(sql, params)
        self._conn.commit()

    def executar_varios(self, sql, lista_de_params):
        """Insere varias linhas com o mesmo SQL - substitui executemany, que se comporta
        de forma inconsistente entre sqlite3 e libsql. Um commit so, no final."""
        for params in lista_de_params:
            self._conn.execute(sql, params)
        self._conn.commit()

    def rodar_script(self, sql_texto):
        """Roda um schema.sql inteiro - funciona igual nos dois drivers, sem depender
        de executescript (que o libsql nao garante suportar). Filtra trechos que sobram
        só com comentário (sem SQL real) — o Turso rejeita isso, o SQLite local não."""
        for bruto in sql_texto.split(";"):
            linhas_uteis = [l for l in bruto.splitlines() if l.strip() and not l.strip().startswith("--")]
            instrucao = "\n".join(linhas_uteis).strip()
            if not instrucao:
                continue
            self._conn.execute(instrucao)
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_conn():
    return Conexao()


def garantir_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.rodar_script(f.read())


def limpar_analises_antigas(conn, dias=30):
    conn.executar("DELETE FROM analises WHERE criado_em < datetime('now', ?)", (f"-{dias} days",))


def limpar_jogos_exportados_passados(conn, dias=1):
    """Remove da tabela de análises exportadas (etapa 4) jogos cuja data_partida já
    passou há mais de `dias` dias. Diferente de limpar_analises_antigas: o critério aqui
    é a data da PARTIDA, não a data de exportação — um jogo exportado com antecedência
    não pode ser apagado antes de acontecer só porque já faz alguns dias que foi exportado."""
    conn.executar(
        "DELETE FROM analises_finais_exportadas WHERE data_partida < datetime('now', ?)",
        (f"-{dias} days",),
    )
