"""Der Regelkreis: entscheiden → umschreiben → nachprüfen.

Drei Aufgaben, zwei Modelle. Das Entscheidungsmodell stellt fest, wie schwer ein
Absatz ist, das Sprachmodell schreibt ihn um, das Entscheidungsmodell prüft das
Ergebnis des Sprachmodells nach. Der Prüfschritt ist billig genug, um bei jedem
Durchlauf zu laufen — das ist der Grund, warum der Kreis überhaupt zumacht.

Der Generator gibt jeden Schritt einzeln heraus, damit die Oberfläche den Verlauf
mitschreiben kann statt nur das Ergebnis zu zeigen.
"""

from typing import Iterator

import cefr
import jev
import rewriter

# Ab dieser Verbesserung je Durchlauf gilt der Kreis als konvergierend. Fällt sie
# darunter, bringt das Sprachmodell den Absatz nicht weiter herunter, und weitere
# Runden kosten nur Geld.
MIN_IMPROVEMENT = 0.15


def run(
    text: str,
    target_level: str = "B1",
    max_iterations: int = 3,
    model: str = rewriter.DEFAULT_MODEL,
) -> Iterator[dict]:
    target_index = cefr.LEVELS.index(target_level)
    current_text = text
    previous_score: float | None = None

    for iteration in range(max_iterations + 1):
        # Prüfen. In Runde 0 ist das die Eingangsmessung, danach die Nachprüfung
        # dessen, was das Sprachmodell geliefert hat.
        try:
            verdict = jev.assess(current_text)
        except jev.JevError as exc:
            yield {"type": "error", "stage": "jev", "message": str(exc)}
            return

        yield {
            "type": "assess",
            "iteration": iteration,
            "text": current_text,
            "target": target_level,
            **verdict,
        }

        if verdict["score"] <= target_index + 0.5:
            yield {
                "type": "done",
                "reason": "ziel-erreicht",
                "message": f"Zielniveau {target_level} erreicht.",
                "iterations": iteration,
            }
            return

        if previous_score is not None:
            improvement = previous_score - verdict["score"]
            if improvement < MIN_IMPROVEMENT:
                yield {
                    "type": "done",
                    "reason": "keine-verbesserung",
                    "message": (
                        f"Der Durchlauf hat nur {improvement:+.2f} Stufen gebracht — "
                        f"unterhalb der Schwelle von {MIN_IMPROVEMENT}. Abbruch, bevor "
                        f"weitere Runden Geld kosten, ohne den Text zu bewegen."
                    ),
                    "iterations": iteration,
                }
                return
        previous_score = verdict["score"]

        if iteration == max_iterations:
            yield {
                "type": "done",
                "reason": "limit",
                "message": f"Obergrenze von {max_iterations} Umschreibungen erreicht.",
                "iterations": iteration,
            }
            return

        # Erzeugen.
        try:
            rewritten = rewriter.rewrite(
                current_text,
                target=target_level,
                current=verdict["label"],
                attempt=iteration + 1,
                model=model,
            )
        except rewriter.RewriteError as exc:
            yield {"type": "error", "stage": "llm", "message": str(exc)}
            return

        yield {"type": "rewrite", "iteration": iteration + 1, **rewritten}
        current_text = rewritten["text"]
