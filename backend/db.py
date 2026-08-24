import os
import sqlite3

PASTA_BACKEND = os.path.dirname(os.path.abspath(__file__))
# O banco vive um nível acima (pasta webapp/), onde o popular_banco.py também roda
DB_PATH = os.path.join(PASTA_BACKEND, "..", "analises.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def limpar_analises_antigas(conn, dias=30):
    conn.execute(
        "DELETE FROM analises WHERE criado_em < datetime('now', ?)",
        (f"-{dias} days",),
    )
    conn.commit()
