const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
};

let config = null;
let target = "B1";
let ledger = null;
let stream = null;

const money = (usd) =>
  usd >= 0.01 ? `${usd.toFixed(3)} $` : `${(usd * 100).toFixed(4)} ¢`;

// ---------- Aufbau ----------

async function boot() {
  config = await (await fetch("/api/config")).json();

  const status = $("status");
  status.append(
    pill(config.jev_ready ? "ok" : "warn",
      config.jev_ready ? "Jev verbunden" : "TYPESAFE_API_KEY fehlt"),
    pill("ok", config.llm_backend === "api"
      ? "Sprachmodell über Anthropic-API"
      : "Sprachmodell über lokale claude-CLI"),
  );

  config.samples.forEach((sample) => {
    const chip = el("button", "chip", sample.title);
    chip.type = "button";
    chip.title = sample.note;
    chip.setAttribute("aria-pressed", "false");
    chip.onclick = () => {
      document.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
      chip.setAttribute("aria-pressed", "true");
      $("text").value = sample.text;
    };
    $("samples").append(chip);
  });

  config.levels.forEach((level) => {
    const button = el("button", null, level);
    button.type = "button";
    button.setAttribute("aria-pressed", String(level === target));
    button.onclick = () => {
      target = level;
      $("target").querySelectorAll("button").forEach((b) =>
        b.setAttribute("aria-pressed", String(b.textContent === level)));
    };
    $("target").append(button);
  });

  config.models.forEach((model) => {
    const option = el("option", null, model.label);
    option.value = model.id;
    option.selected = model.id === config.default_model;
    $("model").append(option);
  });

  $("rubric-instructions").textContent = config.instructions;
  config.criteria.forEach((line) => $("rubric-levels").append(el("li", null, line)));

  $("run").onclick = start;
  $("samples").firstChild?.click();
}

const pill = (kind, text) => el("span", `pill ${kind}`, text);

// ---------- Kreislauf ----------

function start() {
  const text = $("text").value.trim();
  if (!text) return;

  stream?.close();
  $("timeline").innerHTML = "";
  $("summary").hidden = true;
  $("run").disabled = true;
  ledger = { jevCalls: 0, jevCost: 0, jevMs: 0, llmCalls: 0, llmCost: 0, llmMs: 0, from: null, to: null };

  const params = new URLSearchParams({
    text,
    target,
    model: $("model").value,
    max_iterations: $("max").value,
  });

  waiting("Entscheidungsmodell liest den Absatz …");
  stream = new EventSource(`/api/loop?${params}`);
  stream.onmessage = (event) => handle(JSON.parse(event.data));
  stream.onerror = () => {
    if (!$("run").disabled) return;
    clearWaiting();
    finish();
  };
}

function handle(event) {
  clearWaiting();
  if (event.type === "assess") return onAssess(event);
  if (event.type === "rewrite") return onRewrite(event);
  if (event.type === "done") return onDone(event);
  if (event.type === "error") return onError(event);
}

function onAssess(event) {
  ledger.jevCalls++;
  ledger.jevCost += event.cost_usd;
  ledger.jevMs += event.latency_ms;
  if (ledger.from === null) ledger.from = event;
  ledger.to = event;

  const first = event.iteration === 0;
  const card = el("article", "card jev");

  const head = el("div", "card-head");
  head.append(
    el("span", "who", "Entscheidungsmodell"),
    el("span", "role", first ? "misst den Ausgangstext" : "prüft nach, was das Sprachmodell geliefert hat"),
    el("span", "round", first ? "Eingang" : `nach Umschreibung ${event.iteration}`),
  );

  const verdict = el("div", "verdict");
  verdict.append(
    el("span", "level", event.label),
    el("span", "score", `Score ${event.score.toFixed(2)} · Confidence ${(event.confidence * 100).toFixed(0)} %`),
  );

  card.append(head, verdict, distribution(event), meta([
    ["Modell", event.model],
    ["Latenz", `${event.latency_ms} ms`],
    ["Eingabe", `${event.input_tokens} Token`],
    ["Kosten", money(event.cost_usd)],
  ]));

  if (event.confidence >= 0.85 && spread(event.probabilities) >= 2) {
    card.append(el("p", "hint",
      "Hohe Confidence bei einer Verteilung, die über mehrere Stufen läuft. Kalibrierung ist eine " +
      "Eigenschaft von Gruppen — für diese eine Antwort sagt die Zahl nichts."));
  }

  $("timeline").append(card);
  scroll(card);

  if (event.score > config.levels.indexOf(event.target) + 0.5) {
    waiting("Sprachmodell schreibt um …");
  }
}

function onRewrite(event) {
  ledger.llmCalls++;
  ledger.llmCost += event.cost_usd;
  ledger.llmMs += event.latency_ms;

  const card = el("article", "card llm");
  const head = el("div", "card-head");
  head.append(
    el("span", "who", "Sprachmodell"),
    el("span", "role", "schreibt den Absatz um"),
    el("span", "round", `Umschreibung ${event.iteration}`),
  );

  card.append(head, el("p", "passage", event.text), meta([
    ["Modell", event.model_label],
    ["Latenz", `${(event.latency_ms / 1000).toFixed(1)} s`],
    ["Token", `${event.input_tokens} ein / ${event.output_tokens} aus`],
    ["Kosten", money(event.cost_usd)],
  ]));

  $("timeline").append(card);
  scroll(card);
  waiting("Entscheidungsmodell prüft nach …");
}

function onDone(event) {
  const card = el("article", "card end");
  const head = el("div", "card-head");
  head.append(el("span", "who", "Abbruch"), el("span", "role", event.reason.replace(/-/g, " ")));
  card.append(head, el("p", "note", event.message));
  $("timeline").append(card);
  scroll(card);
  finish();
}

function onError(event) {
  const card = el("article", "card fail");
  const head = el("div", "card-head");
  head.append(el("span", "who", "Fehler"), el("span", "role", event.stage));
  card.append(head, el("p", "note", event.message));
  $("timeline").append(card);
  finish();
}

function finish() {
  stream?.close();
  stream = null;
  $("run").disabled = false;
  if (ledger?.jevCalls) renderSummary();
}

// ---------- Darstellung ----------

function distribution(event) {
  const box = el("div", "dist");
  config.levels.forEach((level) => {
    const value = event.probabilities[level] ?? 0;
    const bar = el("div", "bar");
    if (level === event.label) bar.classList.add("win");
    if (level === event.target) bar.classList.add("target");

    const fill = el("div", "fill");
    bar.append(el("div", "pct", value >= 0.005 ? `${Math.round(value * 100)}` : ""), fill, el("div", "lab", level));
    box.append(bar);
    requestAnimationFrame(() => { fill.style.height = `${Math.max(2, value * 52)}px`; });
  });
  return box;
}

function meta(pairs) {
  const box = el("div", "meta");
  pairs.forEach(([key, value]) => {
    const item = el("span");
    item.append(`${key} `, el("b", null, value));
    box.append(item);
  });
  return box;
}

/** Über wie viele Stufen verteilt sich nennenswerte Wahrscheinlichkeit? */
function spread(probabilities) {
  return Object.values(probabilities).filter((p) => p >= 0.05).length;
}

function renderSummary() {
  const box = $("summary");
  box.innerHTML = "";
  const moved = ledger.from.score - ledger.to.score;
  const factor = ledger.llmCost > 0 ? ledger.llmCost / Math.max(ledger.jevCost, 1e-12) : 0;

  box.append(el("h2", null, "Bilanz des Durchlaufs"));

  const grid = el("div", "ledger");
  grid.append(
    cell("jev", "Entscheiden und Prüfen", `${money(ledger.jevCost)}`,
         `${ledger.jevCalls} Aufrufe · ${ledger.jevMs} ms`),
    cell("llm", "Erzeugen", `${money(ledger.llmCost)}`,
         `${ledger.llmCalls} Aufrufe · ${(ledger.llmMs / 1000).toFixed(1)} s`),
    cell("", "Bewegt", `${ledger.from.label} → ${ledger.to.label}`,
         `${moved >= 0 ? "−" : "+"}${Math.abs(moved).toFixed(2)} Stufen`),
  );
  box.append(grid);

  if (factor > 1) {
    box.append(el("p", "note",
      `Das Erzeugen kostet in diesem Durchlauf das ${factor.toFixed(0)}-Fache des Prüfens. ` +
      `Genau deshalb kann der Prüfschritt bei jedem Durchlauf mitlaufen, statt gespart zu werden.`));
  }
  box.append(el("p", "note",
    "Die Kosten des Sprachmodells sind aus Aufgaben-Token zu Listenpreisen gerechnet. Läuft es über " +
    "die lokale CLI, bleibt deren eigener Systemprompt bewusst außen vor — er gehört zum Werkzeug, " +
    "nicht zur Aufgabe."));
  box.hidden = false;
}

function cell(kind, key, value, sub) {
  const box = el("div", `cell ${kind}`);
  box.append(el("div", "k", key), el("div", "v", value), el("div", "k", sub));
  return box;
}

function waiting(text) {
  clearWaiting();
  const box = el("div", "working");
  box.id = "working";
  box.append(el("span", "dot"), el("span", null, text));
  $("timeline").append(box);
  scroll(box);
}

const clearWaiting = () => $("working")?.remove();
const scroll = (node) => node.scrollIntoView({ behavior: "smooth", block: "nearest" });

boot();
