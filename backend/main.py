import json
import os
from dotenv import load_dotenv

# Usa o mesmo .env de webapp/ (um nível acima), compartilhado com popular_banco.py e consultar_times.py.
# Na Vercel, o arquivo não existe e isso não faz nada — as variáveis já vêm do ambiente configurado no dashboard.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import api_football
from db import get_conn, garantir_schema, limpar_analises_antigas

app = FastAPI(title="GradinScore API")

# Em producao, troque "*" pela URL real do frontend na Vercel (variavel FRONTEND_URL)
import os
origens = os.environ.get("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origens] if origens != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    conn = get_conn()
    if conn.modo == "sqlite":
        garantir_schema(conn)  # no Turso, o schema ja foi rodado manualmente uma vez
    limpar_analises_antigas(conn, dias=30)
    conn.close()


@app.get("/ligas")
def listar_ligas():
    conn = get_conn()
    linhas = conn.query(
        """SELECT id_api, nome, pais, tem_estatisticas, eh_liga_pontos_corridos, temporada_atual
           FROM ligas ORDER BY nome"""
    )
    conn.close()
    return linhas


@app.get("/ligas/{id_liga}/tabela")
def tabela_liga(id_liga: int):
    conn = get_conn()
    ligas = conn.query("SELECT * FROM ligas WHERE id_api = ?", (id_liga,))
    conn.close()
    if not ligas:
        raise HTTPException(404, "Liga não encontrada no banco local.")
    liga = ligas[0]
    if not liga["eh_liga_pontos_corridos"]:
        raise HTTPException(400, "Esta competição não tem tabela de classificação única (é copa/mata-mata).")

    return api_football.tabela_liga(liga["id_api"], liga["temporada_atual"])


@app.get("/ligas/{id_liga}/times")
def listar_times(id_liga: int, q: str = Query(default="", description="Filtro de busca por nome")):
    conn = get_conn()
    if q:
        linhas = conn.query(
            "SELECT id_api, nome, pais FROM times WHERE id_liga = ? AND nome LIKE ? ORDER BY nome LIMIT 50",
            (id_liga, f"%{q}%"),
        )
    else:
        linhas = conn.query(
            "SELECT id_api, nome, pais FROM times WHERE id_liga = ? ORDER BY nome LIMIT 50",
            (id_liga,),
        )
    conn.close()
    return linhas


@app.get("/jogos-proximos")
def jogos_proximos(
    ligas: str = Query(default="39,140,78", description="IDs de liga (id_api) separados por vírgula. Padrão: Premier League, La Liga, Bundesliga."),
    dias: int = Query(default=10, ge=1, le=30, description="Janela de dias a partir de hoje"),
):
    ids_liga = [int(x) for x in ligas.split(",") if x.strip()]

    conn = get_conn()
    resultado = []
    for id_liga in ids_liga:
        linhas = conn.query("SELECT * FROM ligas WHERE id_api = ?", (id_liga,))
        if not linhas:
            continue  # liga não cadastrada localmente - pula sem derrubar a resposta inteira
        liga = linhas[0]

        # times já cadastrados dessa liga, pra sinalizar se dá pra chamar /analise direto
        # ou se precisa rodar popular_banco.py antes (ex: time recém-promovido ainda não seedado)
        times_liga = conn.query("SELECT id_api FROM times WHERE id_liga = ?", (id_liga,))
        ids_times_cadastrados = {t["id_api"] for t in times_liga}

        for f in api_football.fixtures_proximos(id_liga, liga["temporada_atual"], dias=dias):
            id_casa = f["teams"]["home"]["id"]
            id_fora = f["teams"]["away"]["id"]
            resultado.append({
                "fixture_id": f["fixture"]["id"],
                "id_liga": id_liga,
                "liga": liga["nome"],
                "data_partida": f["fixture"]["date"],
                "id_time_casa": id_casa,
                "time_casa": f["teams"]["home"]["name"],
                "id_time_fora": id_fora,
                "time_fora": f["teams"]["away"]["name"],
                "times_cadastrados": id_casa in ids_times_cadastrados and id_fora in ids_times_cadastrados,
            })
    conn.close()

    resultado.sort(key=lambda j: j["data_partida"])
    return resultado


class PedidoAnalise(BaseModel):
    id_liga: int
    id_time_casa: int
    id_time_fora: int
    data_partida: str | None = None


@app.post("/analise")
def gerar_analise(pedido: PedidoAnalise):
    conn = get_conn()
    ligas = conn.query("SELECT * FROM ligas WHERE id_api = ?", (pedido.id_liga,))
    if not ligas:
        conn.close()
        raise HTTPException(404, "Liga nao encontrada no banco local.")
    liga = ligas[0]

    times_casa = conn.query(
        "SELECT * FROM times WHERE id_api = ? AND id_liga = ?", (pedido.id_time_casa, pedido.id_liga)
    )
    times_fora = conn.query(
        "SELECT * FROM times WHERE id_api = ? AND id_liga = ?", (pedido.id_time_fora, pedido.id_liga)
    )
    if not times_casa or not times_fora:
        conn.close()
        raise HTTPException(404, "Time nao encontrado no banco local.")
    time_casa = times_casa[0]
    time_fora = times_fora[0]

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
        "data_partida": pedido.data_partida,
    }

    conn.executar(
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
    conn.close()

    return resultado


@app.get("/analises")
def listar_historico(limite: int = 20):
    conn = get_conn()
    linhas = conn.query(
        """SELECT a.id, l.nome as liga, tc.nome as time_casa, tf.nome as time_fora,
                  a.data_partida, a.resultado_json, a.criado_em
           FROM analises a
           JOIN ligas l ON l.id_api = a.id_liga
           JOIN times tc ON tc.id_api = a.id_time_casa
           JOIN times tf ON tf.id_api = a.id_time_fora
           ORDER BY a.criado_em DESC
           LIMIT ?""",
        (limite,),
    )
    conn.close()

    resultado = []
    for item in linhas:
        item["resultado"] = json.loads(item.pop("resultado_json"))
        resultado.append(item)
    return resultado
