"""
Consulta ad-hoc: lista os times cadastrados de uma liga/copa específica.
Usa a mesma lógica de conexão dual (Turso se as variáveis estiverem definidas, senão local).

Uso:
    $env:TURSO_DATABASE_URL = "sua-url"      # opcional — omita para consultar o local
    $env:TURSO_AUTH_TOKEN = "seu-token"      # opcional
    python consultar_times.py 73             # 73 = Copa do Brasil
"""

import os
import sys
import sqlite3
from dotenv import load_dotenv

load_dotenv()

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PASTA_SCRIPT, "analises.db")

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")


def conectar():
    if TURSO_URL:
        import libsql
        print(f"[conectando ao Turso: {TURSO_URL}]")
        return libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
    print(f"[conectando ao SQLite local: {DB_PATH}]")
    return sqlite3.connect(DB_PATH)


if __name__ == "__main__":
    id_liga = int(sys.argv[1]) if len(sys.argv) > 1 else 73  # padrão: Copa do Brasil

    conn = conectar()

    cur = conn.execute("SELECT nome, pais, temporada_atual FROM ligas WHERE id_api = ?", (id_liga,))
    liga = cur.fetchone()
    if not liga:
        print(f"Liga id={id_liga} não encontrada no banco.")
        sys.exit(1)
    print(f"\nLiga: {liga[0]} ({liga[1]}) — temporada cadastrada: {liga[2]}\n")

    cur = conn.execute(
        "SELECT id_api, nome, pais FROM times WHERE id_liga = ? ORDER BY nome", (id_liga,)
    )
    times = cur.fetchall()
    print(f"Total de times cadastrados: {len(times)}\n")
    for id_api, nome, pais in times:
        print(f"  {id_api:>6}  {nome}  ({pais})")

    conn.close()
