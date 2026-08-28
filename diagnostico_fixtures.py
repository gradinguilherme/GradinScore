"""
Diagnóstico: consulta /fixtures direto na API-Football para uma competição e mostra
quais fases (rounds) existem e quantos jogos há em cada status.

Uso:
    python diagnostico_fixtures.py 73 2026    # 73 = Copa do Brasil
"""

import os
import sys
import requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

if __name__ == "__main__":
    id_liga = int(sys.argv[1]) if len(sys.argv) > 1 else 73
    temporada = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

    resp = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params={"league": id_liga, "season": temporada},
    )
    data = resp.json()

    if data.get("errors"):
        print(f"[ERRO] {data['errors']}")
        sys.exit(1)

    fixtures = data.get("response", [])
    print(f"Total de fixtures retornados: {len(fixtures)}\n")

    por_fase = defaultdict(list)
    for f in fixtures:
        fase = f["league"]["round"]
        status = f["fixture"]["status"]["short"]
        data_jogo = f["fixture"]["date"][:10]
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]
        por_fase[fase].append((data_jogo, status, home, away))

    for fase, jogos in por_fase.items():
        print(f"=== {fase} ({len(jogos)} jogos) ===")
        for data_jogo, status, home, away in jogos[:5]:  # só os 5 primeiros de cada fase, pra não poluir
            print(f"  {data_jogo}  [{status}]  {home} x {away}")
        if len(jogos) > 5:
            print(f"  ... e mais {len(jogos) - 5}")
        print()
