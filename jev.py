"""Client für das Entscheidungsmodell (TypeSafe Jev, POST /v1/systemone).

Bewusst hinter einer eigenen Schnittstelle: ein einziger Anbieter, Seed-Phase,
keine offenen Gewichte. Was hier zurückkommt, ist eine Entscheidung mit
Wahrscheinlichkeitsverteilung — kein Text.
"""

import os
import time

import httpx

import cefr

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"

# 42 USD je Milliarde Eingabe-Token, Ausgabe-Token kostenlos (Herstellerangabe).
USD_PER_INPUT_TOKEN = 42 / 1_000_000_000


class JevError(RuntimeError):
    pass


def assess(text: str, timeout: float = 30.0) -> dict:
    """Ein Absatz rein, eine CEFR-Stufe mit voller Verteilung raus."""
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        raise JevError("TYPESAFE_API_KEY ist nicht gesetzt (siehe .env.example).")

    payload = {
        "state": text,
        "model": MODEL,
        "questions": {
            "cefr": {
                "type": "score",
                "instructions": cefr.INSTRUCTIONS,
                "criteria": cefr.CRITERIA,
            }
        },
    }

    started = time.perf_counter()
    try:
        response = httpx.post(
            ENDPOINT,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise JevError(f"Jev nicht erreichbar: {exc}") from exc
    latency_ms = round((time.perf_counter() - started) * 1000)

    if response.status_code != 200:
        raise JevError(f"Jev antwortet {response.status_code}: {response.text[:300]}")

    body = response.json()
    answer = body["answers"]["cefr"]
    usage = body.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)

    return {
        "score": answer["score"],
        "label": cefr.label(answer["score"]),
        "confidence": answer["confidence"],
        # Stufenindex → Wahrscheinlichkeit, umgeschlüsselt auf die Stufennamen.
        "probabilities": {
            cefr.LEVELS[int(index)]: value
            for index, value in sorted(answer["probabilities"].items(), key=lambda kv: int(kv[0]))
        },
        "model": body.get("model", MODEL),
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "cost_usd": input_tokens * USD_PER_INPUT_TOKEN,
    }
