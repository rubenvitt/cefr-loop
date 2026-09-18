# cefr-loop

Eine kleine Demo für die Zusammenarbeit von **Entscheidungsmodell und Sprachmodell**:
Ein typisiertes Entscheidungsmodell (TypeSafe Jev) misst, welches Sprachniveau ein
deutscher Absatz vom Leser verlangt. Liegt es über dem Ziel, schreibt ein Sprachmodell
den Absatz um — und das Entscheidungsmodell prüft nach, was dabei herauskam.

Drei Aufgaben, zwei Modelle, jedes dort, wo es stark ist:

| Aufgabe | Modell | Ausgabe |
|---|---|---|
| **Entscheiden** — wie schwer ist der Text? | Jev (`jev-latest`), Score über A1–C2 | Stufe, Verteilung, Confidence |
| **Erzeugen** — schreib ihn einfacher | Claude Sonnet 5 / Haiku 4.5 | Text |
| **Prüfen** — ist das jetzt einfacher? | Jev, dieselbe Frage | Stufe, Verteilung, Confidence |

Der Prüfschritt kostet einen Bruchteil des Erzeugens. Genau deshalb kann er bei jedem
Durchlauf mitlaufen, statt eingespart zu werden — die Bilanz am Ende jedes Laufs zeigt
das Verhältnis.

## Was die Oberfläche zeigt

Jeder Schritt wird als eigene Karte mitgeschrieben, farblich getrennt nach Modell.
Bei jedem Urteil des Entscheidungsmodells steht die **vollständige Verteilung über alle
sechs Stufen**, nicht nur die Gewinnerstufe. Das ist der eigentliche Unterschied zu einem
Sprachmodell mit JSON-Schema: Ein Absatz zwischen B2 und C1 sieht hier auch so aus, statt
zu einer einzelnen Behauptung zusammenzufallen.

Meldet das Modell hohe Confidence, während sich die Wahrscheinlichkeit über mehrere Stufen
verteilt, weist die Karte darauf hin. Kalibrierung ist eine Eigenschaft von Gruppen von
Vorhersagen; für die einzelne Antwort folgt daraus nichts. CEFR ist eine sechsstufige
Rubrik, an der sich auch Menschen streiten — der Ort, an dem sich ein Kalibrierungsfehler
am ehesten zeigt.

## Abbruchbedingungen

Der Kreis endet aus einem von drei Gründen, und die Oberfläche nennt welchen:

1. **Ziel erreicht** — der Score liegt auf oder unter der Zielstufe.
2. **Keine Verbesserung** — ein Durchlauf hat den Text um weniger als 0,15 Stufen bewegt.
   Ohne dieses Kriterium dreht die Schleife bei Absätzen, die das Sprachmodell nicht
   weiter vereinfachen kann, bis zur Obergrenze und sieht dabei wie ein Defekt aus.
3. **Obergrenze** — die eingestellte Zahl an Umschreibungen ist erreicht.

## Start

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env      # TYPESAFE_API_KEY eintragen
set -a && . ./.env && set +a
./.venv/bin/uvicorn app:app --port 8420
```

Dann `http://localhost:8420` öffnen.

**Sprachmodell-Zugang:** Ist `ANTHROPIC_API_KEY` gesetzt, geht der Umschreibeschritt direkt
an die Messages-API. Sonst läuft er über die lokale `claude`-CLI im Headless-Modus. Die CLI
bringt ihren eigenen Systemprompt mit, deshalb sind ihre Kostenangaben für einen Vergleich
unbrauchbar. Auf diesem Weg wird aus der Promptlänge geschätzt und in der Oberfläche mit ≈
markiert; mit `ANTHROPIC_API_KEY` sind beide Seiten der Bilanz gemessen.

## Aufbau

```
cefr.py       CEFR-Stufen als Rubrik (Deskriptoren, nicht nur Stufennamen)
jev.py        Client für POST /v1/systemone
rewriter.py   Sprachmodell, zwei Backends
loop.py       der Regelkreis als Generator
app.py        FastAPI, Kreislauf als Server-Sent-Events
samples.py    Beispielabsätze
static/       Oberfläche, ohne Build-Schritt
```

## Beispieldaten

Alle Absätze in `samples.py` sind **selbst geschrieben und synthetisch**. Sie imitieren
Behörden-, Medizin-, Produkt- und Vertragssprache, beschreiben aber erfundene Sachverhalte.
Keine Zeile stammt aus einem echten Dokument.

## Grenzen

- Das Entscheidungsmodell liefert eine Zahl, keine Belegstelle. Wo eine Begründung geschuldet
  ist, taugt diese Bauform nicht als alleinige Instanz.
- Gemessen wird die sprachliche Anforderung, nicht ob das Sprachmodell den Inhalt korrekt
  erhalten hat. Für den produktiven Einsatz gehörte eine zweite Frage dazu: Steht im
  umgeschriebenen Absatz noch dasselbe?
- Ein einziger Anbieter, Seed-Phase, keine offenen Gewichte — der Client liegt deshalb hinter
  einer eigenen Schnittstelle.
