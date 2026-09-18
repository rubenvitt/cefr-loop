# Was der Bau gezeigt hat

Notizen aus dem Bau dieser Demo, 18.09.2026. Alle Zahlen stammen aus Läufen gegen die
echte API (`jev-1.13.0`, Claude Sonnet 5). Sie sind Beobachtungen aus wenigen Durchläufen,
keine Messreihe — wo das den Unterschied macht, steht es dabei.

## Worum es geht

Ein typisiertes Entscheidungsmodell und ein Sprachmodell arbeiten in einem Regelkreis
aneinander: Das Entscheidungsmodell misst, wie schwer ein deutscher Absatz zu lesen ist
(CEFR A1–C2), das Sprachmodell schreibt ihn einfacher, das Entscheidungsmodell prüft das
Ergebnis nach. Abbruch bei Zielstufe, Stillstand oder Obergrenze.

Der Fall ist so gewählt, dass **beide Modelle tragend** sind. Das ist seltener, als es
klingt: In den meisten Anwendungsfällen für typisierte Entscheidungsmodelle wäre ein
Sprachmodell Dekoration — es klassifiziert oder sortiert etwas, und danach passiert Code.
Hier wird die Ausgabe des einen zum Prüfgegenstand des anderen.

## 1. Der billige Prüfer ändert, welche Architektur man sich leisten kann

Das Muster „ein Aufruf erzeugt, ein zweiter bewertet, in einer Schleife" ist bekannt
(Evaluator-Optimizer). Es setzt stillschweigend voraus, dass beide Aufrufe an dieselbe
Modellklasse gehen — und dann kostet das Prüfen so viel wie das Erzeugen und wird als
erstes gespart.

Gemessen in dieser Demo:

| | Entscheiden und Prüfen | Erzeugen |
|---|---|---|
| Modell | Jev | Sonnet 5 |
| Dauer je Aufruf | ~700 ms | 5–6 s |
| Eingabe je Aufruf | ~740 Token | ~270 Token |
| Kosten je Aufruf | Bruchteil eines Cents | mittlerer einstelliger Cent-Bereich |

Der Prüfschritt verschwindet im Rauschen. Deshalb kann er bei **jedem** Durchlauf stehen
bleiben, statt eingespart zu werden.

Der zweite Effekt ist wichtiger als der Preis: Der Rückkanal wird **programmierbar**. Ein
Prosa-Urteil („der Text wirkt noch recht komplex") muss der nächste Aufruf interpretieren.
Eine Zahl vergleicht der Code mit einer Schwelle und verzweigt. Damit wandert die
Abbruchentscheidung aus dem Modell in den Kontrollfluss — und wird benennbar.

## 2. Ein Regelkreis braucht eine Konvergenzbedingung, nicht nur ein Limit

Drei Abbruchgründe, und der mittlere ist der, den man beim ersten Entwurf vergisst:

1. **Ziel erreicht** — der Wert liegt auf oder unter der Schwelle
2. **Keine Verbesserung** — eine Runde hat weniger als 0,15 Stufen gebracht
3. **Obergrenze** — die eingestellte Zahl an Runden ist erreicht

Ohne Nummer 2 dreht der Kreis bei Absätzen, die das Sprachmodell nicht weiter vereinfachen
kann, bis zur Obergrenze durch. Das kostet Geld in genau den Fällen, in denen nichts
passiert — und sieht in einer Vorführung wie ein Defekt aus, obwohl es einer ist.

## 3. Die Verteilung reagiert auf Grenzfälle

CEFR ist eine sechsstufige Rubrik, an der sich auch Menschen streiten — also der Ort, an
dem man einem Modell überzogene Sicherheit am ehesten zutraut. Ein Behördenabsatz durch
vier Runden:

| Zustand | Urteil | Confidence |
|---|---|---|
| unverändert | C1–C2 | 0,80 |
| nach einer Umschreibung | B2–C1 | 0,67 |
| nach zweien | B2–C1 | 0,75 |
| nach dreien | B1–B2 | 0,66 |
| Gegenprobe: Paketbenachrichtigung | A2–B1 | 0,67 |

Die Confidence fällt dort, wo der Text zwischen zwei Stufen liegt, und steigt bei klaren
Fällen. Das ist der praktische Unterschied zu einem Sprachmodell mit JSON-Schema: Dort
stünde „B2", und die Ambivalenz wäre verschwunden. Deshalb zeigt die Oberfläche die
**vollständige Verteilung über alle sechs Stufen**, nicht nur die Gewinnerstufe.

> **Was hier nicht gemessen wurde.** Das sind rund zehn Urteile ohne Ground Truth. Geprüft
> ist nicht, ob die Stufen *richtig* sind, sondern nur, ob sich die Verteilung plausibel
> verhält. Kalibrierung ist damit **nicht** gemessen — dafür bräuchte es ein Eval-Set über
> viele Fälle mit bekannter Antwort.

## 4. Der Kreis optimiert nur, was er misst

Die interessanteste Lücke ist die, die dieselbe Bauform schließen könnte und hier offen
bleibt: Der Kreislauf treibt das Sprachmodell gegen den CEFR-Score. Ob im umgeschriebenen
Absatz **noch dasselbe steht**, misst niemand.

Ein Text wird zuverlässig einfacher, wenn man die Hälfte weglässt — und der Regelkreis
würde das als Erfolg verbuchen, mit sinkendem Wert und wachsender Confidence. Das ist
Reward Hacking ohne Training, allein aus der Architektur.

Was fehlt, ist eine **Invariante** neben dem Zielmaß:

| | Frage | Rolle |
|---|---|---|
| Zielmaß | Wie schwer ist der Text? | treibt den Kreis, soll sinken |
| Invariante | Steht im neuen Absatz noch dasselbe? | bricht ab, wenn sie reißt |

Wichtig: Die Invariante gehört an die Abbruchbedingung, nicht in die Optimierung. Wer sie
ins Zielmaß mischt, bekommt einen gewichteten Kompromiss und merkt wieder nicht, wenn eine
Seite kippt.

Die Frage vor dem Bau jedes solchen Kreises: *Was soll sich nicht ändern, während das
Zielmaß sinkt — und wer prüft das?*

## 5. Werkzeug-Overhead verfälscht Kostenvergleiche

Die Aussage „das Erzeugen kostet ein Vielfaches des Prüfens" trägt das ganze Argument aus
Abschnitt 1. Sie hing an einer Zahl, die das Werkzeug falsch meldete.

Ein Umschreibeprompt von rund 950 Zeichen wurde von der `claude`-CLI mit **2 Eingabe-Token**
ausgewiesen. Der Prompt war nicht verschwunden — er lag in den Cache-Feldern, zusammen mit
dem Systemprompt der CLI, rund 27.000 Token Beiwerk ohne Bezug zur Aufgabe. Beide
naheliegenden Wege sind falsch:

| Vorgehen | Fehler |
|---|---|
| Gemeldete `input_tokens` nehmen | zu niedrig — der Prompt fehlt (2 statt ~270) |
| Cache-Felder addieren | zu hoch — der Systemprompt des Werkzeugs zählt mit |
| Aus dem Prompt rechnen | brauchbar, aber eine Schätzung |

Für einen Vergleich zwischen Modellklassen zählt nur, was eine echte Integration zahlen
würde. Diese Demo rechnet deshalb aus der Promptlänge und markiert die Zahl in der
Oberfläche mit `≈`. Eine geschätzte Zahl, die als Schätzung kenntlich ist, trägt einen
Vergleich; eine geschätzte Zahl, die wie eine Messung aussieht, ist der teurere Fehler —
sie wandert in Vorträge und Angebote, wo niemand mehr nachrechnet.

## Was offen ist

- **Stufen-Deskriptoren gegen bloße Stufennamen.** Gebaut ist es mit ausformulierten
  Deskriptoren je Stufe, weil das Modell dokumentiert wörtlich liest. Ein kontrollierter
  Vergleich gegen `["A1", …, "C2"]` fand nie statt — die Entscheidung ist plausibel, aber
  unbelegt.
- **Die Invariante aus Abschnitt 4** ist nicht gebaut. Sie wäre eine zweite Frage im
  selben Aufruf und kostete praktisch nichts, weil der Sachverhalt ohnehin einmal
  eingelesen wird.
- **Kein Eval-Set.** Solange keins existiert, sind alle Aussagen über die Güte der Stufen
  Beobachtung, nicht Messung.
