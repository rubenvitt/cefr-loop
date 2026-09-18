"""CEFR-Stufen als Rubrik für den Jev-Score.

Die Deskriptoren sind an den Gemeinsamen Europäischen Referenzrahmen (Skala
Leseverstehen) angelehnt und um syntaktische Merkmale ergänzt, weil Jev
wörtlich liest: eine Stufenbeschreibung, die nur "B1" sagt, überlässt dem
Modell die halbe Rubrik.
"""

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

CRITERIA = [
    "A1 — Einzelne vertraute Wörter und ganz einfache, kurze Hauptsätze. "
    "Alltagswortschatz, keine Nebensätze, keine Fachbegriffe.",
    "A2 — Kurze, einfache Texte zu vertrauten konkreten Themen. Häufiger "
    "Alltags- und Berufswortschatz, einfache Satzverbindungen mit und/aber/weil.",
    "B1 — Texte über vertraute Themen aus Alltag, Arbeit und Schule in klarer "
    "Standardsprache. Überwiegend Hauptsätze und einfache Nebensätze, "
    "Fachbegriffe werden erklärt, wo sie vorkommen.",
    "B2 — Längere sachbezogene Texte und Berichte zu aktuellen Fragen. "
    "Mehrgliedrige Satzgefüge, abstrakte Begriffe, Passiv und Nominalisierungen "
    "kommen vor, bleiben aber auflösbar.",
    "C1 — Lange, anspruchsvolle Sachtexte, auch mit impliziten Bedeutungen. "
    "Verschachtelte Satzgefüge, dichter Nominalstil, Fachwortschatz ohne "
    "Erklärung, Verweise auf anderes (Absätze, Vorschriften, Vorwissen).",
    "C2 — Praktisch jeder Text, auch strukturell oder sprachlich hochkomplex. "
    "Juristisch-wissenschaftliche Fachsprache, Schachtelsätze über mehrere "
    "Zeilen, Idiomatik und Bedeutungsnuancen tragen den Inhalt.",
]

INSTRUCTIONS = (
    "Welches Sprachniveau muss ein Leser mitbringen, um diesen deutschen Absatz "
    "beim ersten Lesen zu verstehen? Beurteile die sprachliche Anforderung des "
    "Textes — Satzbau, Wortschatz, Informationsdichte —, nicht die Fachlichkeit "
    "des Themas und nicht die Qualität des Inhalts."
)


def label(score: float) -> str:
    """Score (auch zwischen zwei Stufen) als lesbare Stufe."""
    lo = max(0, min(len(LEVELS) - 1, int(score)))
    rest = score - lo
    if rest < 0.15 or lo == len(LEVELS) - 1:
        return LEVELS[lo]
    if rest > 0.85:
        return LEVELS[lo + 1]
    return f"{LEVELS[lo]}–{LEVELS[lo + 1]}"
