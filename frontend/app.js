// Frontend for Part 1. Plain JS, no build step. All text is inserted with textContent (no innerHTML) to avoid XSS.
const $ = (id) => document.getElementById(id);
const EXAMPLES = [
  "What are the major challenges companies face when deploying LLMs in production?",
  "What are the problems with models in production?",
  "How does fine-tuning compare with retrieval-augmented generation for enterprise use?",
  "Write me a poem about the sea at night",
];

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function setStatus(message, isError = false) {
  const s = $("status");
  s.hidden = !message;
  s.textContent = message || "";
  s.className = "status" + (isError ? " error" : "");
}

async function api(path, options) {
  const res = await fetch(path, options);
  let body = null;
  try { body = await res.json(); } catch (_) { /* non-JSON error */ }
  if (!res.ok) {
    const detail = body && body.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return body;
}

async function init() {
  EXAMPLES.forEach((q) => {
    const b = el("button", "chip-btn", q.length > 60 ? q.slice(0, 57) + "..." : q);
    b.type = "button"; b.title = q;
    b.addEventListener("click", () => { $("question").value = q; $("question").focus(); });
    $("examples").appendChild(b);
  });
  try {
    const [health, versions] = await Promise.all([api("/api/health"), api("/api/versions")]);
    versions.versions.forEach((v) => {
      const o = el("option", "", v); o.value = v; if (v === versions.default) o.selected = true;
      $("version").appendChild(o);
    });
    const banner = $("banner");
    if (health.mock) {
      banner.textContent = "DEMO MODE: output is canned, not produced by an LLM. Set LLM_MOCK=0 and add LLM_API_KEY in .env for real results.";
      banner.hidden = false;
    } else if (!health.has_key) {
      banner.textContent = "No API key found. Add LLM_API_KEY to .env (see .env.example), then restart the server.";
      banner.hidden = false;
    }
  } catch (e) {
    setStatus("Cannot reach the backend: " + e.message, true);
  }
}

function section(title) {
  const card = el("section", "card");
  card.appendChild(el("h2", "", title));
  return card;
}

function renderAnalysis(a) {
  const card = section("1. Understanding the question");
  const dl = el("dl", "grid");
  const add = (label, node) => { dl.appendChild(el("dt", "", label)); const dd = el("dd"); dd.appendChild(node); dl.appendChild(dd); };
  add("Intent", document.createTextNode(a.intent || "-"));
  add("Scope", document.createTextNode(a.scope || "-"));
  const chips = el("div", "chips");
  (a.key_concepts || []).forEach((c) => chips.appendChild(el("span", "chip", c)));
  add("Key concepts", chips);
  const amb = el("div");
  if (!(a.ambiguities || []).length) amb.textContent = "None identified";
  (a.ambiguities || []).forEach((text, i) => {
    const p = el("p", "amb");
    p.appendChild(document.createTextNode(text));
    if (a.assumptions && a.assumptions[i]) {
      p.appendChild(el("span", "arrow", "  →  assumption: "));
      p.appendChild(document.createTextNode(a.assumptions[i]));
    }
    amb.appendChild(p);
  });
  add("Ambiguities", amb);
  card.appendChild(dl);
  return card;
}

function renderSubQuestions(d) {
  const card = section(`2. Sub-questions (${d.sub_questions.length})`);
  d.sub_questions.forEach((s) => {
    const row = el("div", "sq");
    row.appendChild(el("div", "sq-id", s.id));
    const body = el("div");
    body.appendChild(el("span", `badge type-${s.info_type}`, s.info_type.replace("_", " ")));
    body.appendChild(el("p", "sq-q", s.question));
    if (s.rationale) body.appendChild(el("p", "sq-why", "Why: " + s.rationale));
    row.appendChild(body);
    card.appendChild(row);
  });
  return card;
}

function renderWarnings(list) {
  const box = el("div", "warnings");
  box.appendChild(el("h2", "", "Quality warnings"));
  const ul = el("ul");
  list.forEach((w) => ul.appendChild(el("li", "", w)));
  box.appendChild(ul);
  return box;
}

function renderRaw(data) {
  const details = el("details", "card");
  details.appendChild(el("summary", "", "Raw JSON (hand-off to the next stage)"));
  const bar = el("div", "toolbar");
  const copy = el("button", "secondary", "Copy JSON"); copy.type = "button";
  const json = JSON.stringify(data, null, 2);
  copy.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(json); copy.textContent = "Copied"; }
    catch (_) { copy.textContent = "Copy failed"; }
    setTimeout(() => (copy.textContent = "Copy JSON"), 1500);
  });
  bar.appendChild(copy);
  details.appendChild(bar);
  details.appendChild(el("pre", "", json));
  return details;
}

function render(data) {
  const out = $("results");
  out.replaceChildren();
  if (data.status === "not_researchable") {
    setStatus("This input can't be researched: " + (data.analysis.reason || "not a research question."), true);
    out.hidden = true;
    return;
  }
  setStatus("");
  out.appendChild(renderAnalysis(data.analysis));
  out.appendChild(renderSubQuestions(data.decomposition));
  if (data.warnings && data.warnings.length) out.appendChild(renderWarnings(data.warnings));
  out.appendChild(renderRaw(data));
  out.hidden = false;
}

async function run() {
  const question = $("question").value.trim();
  if (!question) { setStatus("Please enter a research question.", true); return; }
  const btn = $("run");
  btn.disabled = true; $("results").hidden = true;
  setStatus("Analysing and decomposing… this usually takes 5–20 seconds.");
  try {
    const data = await api("/api/decompose", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, version: $("version").value }),
    });
    render(data);
  } catch (e) {
    setStatus(e.message, true);
  } finally {
    btn.disabled = false;
  }
}

$("run").addEventListener("click", run);
$("question").addEventListener("keydown", (e) => { if (e.ctrlKey && e.key === "Enter") run(); });
init();
