"""Webserver für die Demo: Beispiele ausliefern, den Kreislauf als Stream fahren."""

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import cefr
import loop
import rewriter
import samples

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="CEFR-Loop", docs_url=None, redoc_url=None)


@app.get("/api/config")
def config() -> dict:
    return {
        "levels": cefr.LEVELS,
        "criteria": cefr.CRITERIA,
        "instructions": cefr.INSTRUCTIONS,
        "samples": samples.SAMPLES,
        "models": [
            {"id": key, "label": value["label"]} for key, value in rewriter.MODELS.items()
        ],
        "default_model": rewriter.DEFAULT_MODEL,
        "llm_backend": "api" if os.environ.get("ANTHROPIC_API_KEY") else "cli",
        "jev_ready": bool(os.environ.get("TYPESAFE_API_KEY")),
    }


@app.get("/api/loop")
def stream_loop(
    text: str,
    target: str = "B1",
    max_iterations: int = 3,
    model: str = rewriter.DEFAULT_MODEL,
) -> StreamingResponse:
    def events():
        for event in loop.run(text, target, max_iterations, model):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
