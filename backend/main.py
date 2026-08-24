import json
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import api_football
from db import get_conn, limpar_analises_antigas

app = FastAPI(title="Análise Pré-Jogo API")

# Em produção (Vercel), restrinja para o domínio real do frontend em vez de "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    conn = get_conn()
    limpar_analises_antigas(conn, dias=30)
    conn.close()


@app.get("/ligas")
def listar_ligas():
    conn = get_conn()
    linhas = conn.execute(
        "SELECT id_api, nome, pais, tem_estatisticas, temporada_atual FROM ligas ORDER BY nome"
    ).fetchall()
    conn.close()
    return [dict(l) for l in linhas]


@app.get("/ligas/{id_liga}/times")
def listar_times(id_liga: int, q: str = Query(default="", description="Filtro de busca por nome")):
    conn = get_conn()
    if q:
        linhas = conn.execute(
            "SELECT id_api, nome, pais FROM times WHERE id_liga = ? AND nome LIKE ? ORDER BY nome LIMIT 50",
            (id_liga, f"%{q}%"),
        ).fetchall()
    else:
        linhas = conn.execute(
            "SELECT id_api, nome, pais FROM times WHERE id_liga = ? ORDER BY nome LIMIT 50",
            (id_liga,),
        ).fetchall()
    conn.close()
    return [dict(t) for t in linhas]


class PedidoAnalise(BaseModel):
    id_liga: int
    id_time_casa: int
    id_time_fora: int
    data_partida: str | None = None


@app.post("/analise")
def gerar_analise(pedido: PedidoAnalise):
    conn = get_conn()
    liga = conn.execute(
        "SELECT * FROM ligas WHERE id_api = ?", (pedido.id_liga,)
    ).fetchone()
    if not liga:
        conn.close()
        raise HTTPException(404, "Liga não encontrada no banco local.")

    time_casa = conn.execute(
        "SELECT * FROM times WHERE id_api = ?", (pedido.id_time_casa,)
    ).fetchone()
    time_fora = conn.execute(
        "SELECT * FROM times WHERE id_api = ?", (pedido.id_time_fora,)
    ).fetchone()
    if not time_casa or not time_fora:
        conn.close()
        raise HTTPException(404, "Time não encontrado no banco local.")

    tem_estatisticas = bool(liga["tem_estatisticas"])
    temporada = liga["temporada_atual"]

    forma_casa = api_football.forma_recente(
        time_casa["id_api"], temporada, mandante=True, tem_estatisticas=tem_estatisticas
    )
    forma_fora = api_football.forma_recente(
        time_fora["id_api"], temporada, mandante=False, tem_estatisticas=tem_estatisticas
    )
    confrontos = api_football.h2h(time_casa["id_api"], time_fora["id_api"])

    resultado = {
        "liga": liga["nome"],
        "time_casa": time_casa["nome"],
        "time_fora": time_fora["nome"],
        "casa": forma_casa,
        "fora": forma_fora,
        "h2h": confrontos,
        "fallback": not tem_estatisticas,
    }

    conn.execute(
        """INSERT INTO analises (id_liga, id_time_casa, id_time_fora, data_partida, resultado_json)
           VALUES (?, ?, ?, ?, ?)""",
        (
            pedido.id_liga,
            pedido.id_time_casa,
            pedido.id_time_fora,
            pedido.data_partida,
            json.dumps(resultado, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()

    return resultado


@app.get("/analises")
def listar_historico(limite: int = 20):
    conn = get_conn()
    linhas = conn.execute(
        """SELECT a.id, l.nome as liga, tc.nome as time_casa, tf.nome as time_fora,
                  a.data_partida, a.resultado_json, a.criado_em
           FROM analises a
           JOIN ligas l ON l.id_api = a.id_liga
           JOIN times tc ON tc.id_api = a.id_time_casa
           JOIN times tf ON tf.id_api = a.id_time_fora
           ORDER BY a.criado_em DESC
           LIMIT ?""",
        (limite,),
    ).fetchall()
    conn.close()

    resultado = []
    for l in linhas:
        item = dict(l)
        item["resultado"] = json.loads(item.pop("resultado_json"))
        resultado.append(item)
    return resultado
