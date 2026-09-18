"""Der erzeugende Teil: ein Sprachmodell schreibt den Absatz um.

Zwei Backends. Liegt ein ANTHROPIC_API_KEY vor, geht der Aufruf direkt an die
Messages-API. Sonst läuft er über die lokale `claude`-CLI im Headless-Modus —
bequem, aber sie bringt ihren eigenen Systemprompt mit, weshalb die dort
gemeldeten Kosten für einen Vergleich unbrauchbar sind. Gerechnet wird deshalb
auf beiden Wegen aus den reinen Aufgaben-Token zu Listenpreisen; nur das ist
die Zahl, die eine echte Integration auch zahlen würde.
"""

import json
import os
import shutil
import subprocess
import time

import httpx

MODELS = {
    "claude-sonnet-5": {"label": "Sonnet 5", "in": 3.0, "out": 15.0},
    "claude-haiku-4-5-20251001": {"label": "Haiku 4.5", "in": 1.0, "out": 5.0},
}
DEFAULT_MODEL = "claude-sonnet-5"

PROMPT = """Schreibe den folgenden deutschen Absatz sprachlich einfacher.

Zielniveau: {target} (Gemeinsamer Europäischer Referenzrahmen).
Ein Entscheidungsmodell hat den Absatz auf {current} eingestuft.{hint}

Regeln:
- Der Inhalt bleibt vollständig und sachlich korrekt. Nichts weglassen, nichts erfinden.
- Kürzere Sätze, Aktiv statt Passiv, Verben statt Nominalisierungen.
- Fachbegriffe, die bleiben müssen, beim ersten Vorkommen kurz erklären.
- Keine Anrede, keine Einleitung, kein Kommentar.

Gib ausschließlich den umgeschriebenen Absatz aus.

Absatz:
{text}"""


class RewriteError(RuntimeError):
    pass


def _cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = MODELS.get(model, MODELS[DEFAULT_MODEL])
    return (input_tokens * prices["in"] + output_tokens * prices["out"]) / 1_000_000


def _build_prompt(text: str, target: str, current: str, attempt: int) -> str:
    hint = ""
    if attempt > 1:
        hint = (
            f" Der vorherige Versuch hat das Ziel nicht erreicht — dieser Absatz ist "
            f"bereits eine Überarbeitung. Geh sprachlich deutlich weiter herunter."
        )
    return PROMPT.format(target=target, current=current, hint=hint, text=text)


def _via_api(prompt: str, model: str, timeout: float) -> tuple[str, int, int]:
    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )
    if response.status_code != 200:
        raise RewriteError(f"Anthropic-API antwortet {response.status_code}: {response.text[:300]}")
    body = response.json()
    usage = body.get("usage", {})
    return (
        "".join(block.get("text", "") for block in body.get("content", [])).strip(),
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
    )


def _via_cli(prompt: str, model: str, timeout: float) -> tuple[str, int, int]:
    if not shutil.which("claude"):
        raise RewriteError("Weder ANTHROPIC_API_KEY noch die claude-CLI sind verfügbar.")
    try:
        completed = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/tmp",
        )
    except subprocess.TimeoutExpired as exc:
        raise RewriteError(f"claude-CLI hat nach {timeout:.0f}s nicht geantwortet.") from exc
    if completed.returncode != 0:
        raise RewriteError(f"claude-CLI bricht ab: {completed.stderr[:300]}")

    body = json.loads(completed.stdout)
    usage = body.get("usage", {})
    # Die CLI verbucht den Prompt in ihren Cache-Feldern und meldet als
    # input_tokens nur einen Rest. Die Cache-Zahlen mitzunehmen wäre falsch — sie
    # enthalten den Systemprompt des Werkzeugs. Deshalb für den Kostenvergleich
    # aus der Promptlänge schätzen: knapp 3,5 Zeichen je Token für deutschen Text.
    reported = usage.get("input_tokens", 0)
    estimated = round(len(prompt) / 3.5)
    return (
        body.get("result", "").strip(),
        max(reported, estimated),
        usage.get("output_tokens", 0),
    )


def rewrite(
    text: str,
    target: str,
    current: str,
    attempt: int = 1,
    model: str = DEFAULT_MODEL,
    timeout: float = 120.0,
) -> dict:
    prompt = _build_prompt(text, target, current, attempt)
    backend = "api" if os.environ.get("ANTHROPIC_API_KEY") else "cli"

    started = time.perf_counter()
    if backend == "api":
        result, input_tokens, output_tokens = _via_api(prompt, model, timeout)
    else:
        result, input_tokens, output_tokens = _via_cli(prompt, model, timeout)
    latency_ms = round((time.perf_counter() - started) * 1000)

    if not result:
        raise RewriteError("Das Sprachmodell hat keinen Text geliefert.")

    return {
        "text": result,
        "prompt": prompt,
        "backend": backend,
        "model": model,
        "model_label": MODELS.get(model, {}).get("label", model),
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": _cost(model, input_tokens, output_tokens),
        # Über die CLI sind die Eingabe-Token aus der Promptlänge geschätzt, nicht
        # gemessen. Die Oberfläche kennzeichnet das, weil die Zahl als
        # Vergleichsgröße gegen die gemessenen Jev-Kosten steht.
        "tokens_estimated": backend == "cli",
    }
