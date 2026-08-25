"""
Cliente fino da API-Football. Concentra as chamadas HTTP e a lógica de
"últimos 5 em casa/fora" + H2H que já validamos nos scripts de teste.
"""

import os
import time
import requests

API_KEY = os.environ.get("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

if not API_KEY:
    raise RuntimeError(
        "Variável de ambiente API_FOOTBALL_KEY não encontrada. "
        "Defina antes de subir o backend."
    )

HEADERS = {"x-apisports-key": API_KEY}


def _get(endpoint, params=None, tentativas=2):
    for tentativa in range(tentativas):
        resp = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params or {})
        resp.raise_for_status()
        data = resp.json()
        errors = data.get("errors")
        if errors and "rateLimit" in str(errors) and tentativa < tentativas - 1:
            time.sleep(7)
            continue
        return data
    return {"response": []}


def _fixtures_time(team_id, season, mandante: bool, n=5):
    """Últimos n jogos finalizados do time como mandante (mandante=True) ou visitante (mandante=False)."""
    data = _get("fixtures", {"team": team_id, "season": season})
    todos = data.get("response", [])
    filtrados = [
        f for f in todos
        if f["fixture"]["status"]["short"] == "FT"
        and (
            (mandante and f["teams"]["home"]["id"] == team_id)
            or (not mandante and f["teams"]["away"]["id"] == team_id)
        )
    ]
    filtrados.sort(key=lambda f: f["fixture"]["date"], reverse=True)
    return filtrados[:n]


def _estatisticas_fixture(fixture_id, team_id):
    data = _get("fixtures/statistics", {"fixture": fixture_id})
    for bloco in data.get("response", []):
        if bloco["team"]["id"] == team_id:
            stats = {s["type"]: s["value"] for s in bloco["statistics"]}
            return stats
    return {}


def _media(valores):
    numeros = [v for v in valores if isinstance(v, (int, float))]
    if not numeros:
        return None
    return round(sum(numeros) / len(numeros), 2)


def forma_recente(team_id, season, mandante: bool, tem_estatisticas: bool, n=5):
    """
    Retorna médias dos últimos n jogos do time (em casa OU fora, conforme 'mandante').
    Se tem_estatisticas=False (ex: Bundesliga), retorna só gols marcados/sofridos,
    sem chutes — a liga não expõe isso.
    """
    fixtures = _fixtures_time(team_id, season, mandante, n)

    gols_marcados, gols_sofridos = [], []
    chutes, chutes_gol = [], []
    chutes_sofridos, chutes_gol_sofridos = [], []

    for f in fixtures:
        eh_casa = f["teams"]["home"]["id"] == team_id
        gm = f["goals"]["home"] if eh_casa else f["goals"]["away"]
        gs = f["goals"]["away"] if eh_casa else f["goals"]["home"]
        gols_marcados.append(gm)
        gols_sofridos.append(gs)

        if tem_estatisticas:
            stats = _estatisticas_fixture(f["fixture"]["id"], team_id)
            chutes.append(stats.get("Total Shots"))
            chutes_gol.append(stats.get("Shots on Goal"))

            adversario_id = f["teams"]["away"]["id"] if eh_casa else f["teams"]["home"]["id"]
            stats_adv = _estatisticas_fixture(f["fixture"]["id"], adversario_id)
            chutes_sofridos.append(stats_adv.get("Total Shots"))
            chutes_gol_sofridos.append(stats_adv.get("Shots on Goal"))

    resultado = {
        "jogos_considerados": len(fixtures),
        "gols_marcados": _media(gols_marcados),
        "gols_sofridos": _media(gols_sofridos),
    }
    if tem_estatisticas:
        resultado.update({
            "chutes": _media(chutes),
            "chutes_gol": _media(chutes_gol),
            "chutes_sofridos": _media(chutes_sofridos),
            "chutes_gol_sofridos": _media(chutes_gol_sofridos),
        })
    return resultado


def h2h(team1_id, team2_id, n=5):
    data = _get("fixtures/headtohead", {"h2h": f"{team1_id}-{team2_id}"})
    todos = data.get("response", [])
    finalizados = [f for f in todos if f["fixture"]["status"]["short"] == "FT"]
    finalizados.sort(key=lambda f: f["fixture"]["date"], reverse=True)
    resultado = []
    for f in finalizados[:n]:
        resultado.append({
            "data": f["fixture"]["date"][:10],
            "mandante": f["teams"]["home"]["name"],
            "visitante": f["teams"]["away"]["name"],
            "placar": f"{f['goals']['home']}-{f['goals']['away']}",
        })
    return resultado


def tabela_liga(id_liga, temporada):
    """Retorna a classificação atual da liga. Só faz sentido para competições de pontos
    corridos — copas de mata-mata não têm tabela única (a API costuma retornar vazio ou
    uma estrutura por grupo, que não tratamos aqui)."""
    data = _get("standings", {"league": id_liga, "season": temporada})
    respostas = data.get("response", [])
    if not respostas:
        return []

    grupos = respostas[0]["league"].get("standings", [])
    if not grupos:
        return []

    primeiro_grupo = grupos[0]  # ligas de tabela única têm só um grupo
    tabela = []
    for time in primeiro_grupo:
        tabela.append({
            "posicao": time["rank"],
            "time": time["team"]["name"],
            "pontos": time["points"],
            "jogos": time["all"]["played"],
            "vitorias": time["all"]["win"],
            "empates": time["all"]["draw"],
            "derrotas": time["all"]["lose"],
            "saldo_gols": time["goalsDiff"],
        })
    return tabela
