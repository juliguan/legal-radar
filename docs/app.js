// Alle wettekst, bronnen, voorbeelden en data komen uit data.json (gegenereerd uit de YAML door build_site.py).
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const LABEL = { relevant: "Hier kijken", onzeker: "Onzeker", niet_relevant: "Niet aan de orde" };
const EVLABEL = { text_checked: "wettekst nagelezen", primary_page: "primaire pagina gelezen", search_snippet: "alleen zoekresultaat", secondary: "secundaire bron" };
const EXAMPLES = [
  "Ik verkoop een sportshot met magnesium dat spierkramp voorkomt, via mijn webshop.",
  "Een app die verloren bitcoin opspoort en een voorschot vraagt.",
  "Ik schrijf een statische site over de geschiedenis van mijn dorp, zonder cookies of accounts.",
];
const SHORT = { privacy: "Privacy", consumentenrecht: "Consumentenrecht", productaansprakelijkheid: "Product", voedsel_gezondheidsclaims: "Voedsel & claims", financieel: "Financieel" };
const MONTHS = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"];
let DATA, tlArea = "all";

// Zelfde regel als quotes.py: hoofdletters en witruimte tellen niet.
const norm = (t) => t.replace(/\s+/g, " ").trim().toLowerCase();
const quoteInText = (q, text) => !!q && norm(text).includes(norm(q));

function highlight(text, quotes) {
  const low = text.toLowerCase();
  const spans = quotes.map((q) => { const i = low.indexOf(q.toLowerCase()); return i < 0 ? null : [i, i + q.length]; })
    .filter(Boolean).sort((a, b) => a[0] - b[0]);
  let out = "", pos = 0;
  for (const [a, b] of spans) { if (a < pos) continue; out += esc(text.slice(pos, a)) + "<mark>" + esc(text.slice(a, b)) + "</mark>"; pos = b; }
  return out + esc(text.slice(pos));
}

function assess(text) {
  const low = text.toLowerCase();
  return DATA.areas.map((a) => {
    const hit = a.keywords.find((k) => low.includes(k));
    if (!hit) return { a, status: "niet_relevant" };
    const i = low.indexOf(hit), quote = text.slice(i, i + hit.length);
    return quoteInText(quote, text) ? { a, status: "relevant", quote } : { a, status: "onzeker", note: "Citaat niet gevonden in de invoer." };
  });
}

function renderDemo(text, items) {
  const quotes = items.filter((x) => x.quote).map((x) => x.quote);
  $("marked").hidden = !quotes.length;
  $("marked").innerHTML = `<b>Jouw tekst, met de citaten die de check bevestigde</b>${highlight(text, quotes)}`;
  $("results").innerHTML = items.map(({ a, status, quote, note }) => `
    <article class="res">
      <div class="row"><h3>${esc(a.name)}</h3><span class="chip chip--${status}">${LABEL[status]}</span></div>
      ${status === "niet_relevant" ? `<p class="why">Op basis van uw omschrijving lijkt dit gebied niet aan de orde. Dit is geen oordeel.</p>` : `
        <p class="why"><b>Reden</b><br>${esc(a.trigger)}</p>
        ${quote ? `<blockquote>“${esc(quote)}”</blockquote>` : ""}
        ${note ? `<p class="why">${esc(note)}</p>` : ""}
        <details><summary>Wetsverwijzingen en bronnen</summary>
          <p style="font-size:14px;margin-top:10px">${esc(a.summary)}</p>
          <ul>${a.laws.map((l) => `<li>${esc(l.ref)}. ${esc(l.what)} <a href="${esc(l.url)}" target="_blank" rel="noopener">bron</a></li>`).join("")}</ul>
          <p style="font-size:13px"><em>Nog niet door een jurist gecontroleerd (verified: false). Geraadpleegd ${esc(DATA.accessed)}.</em></p>
          <ul>${a.sources.map((s) => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join("")}</ul>
        </details>`}
    </article>`).join("") + `<p class="demo-note">${esc(DATA.disclaimer)}</p>`;
}

function renderCase(i) {
  const r = DATA.runs[i];
  document.querySelectorAll("#casetabs button").forEach((b, j) => b.classList.toggle("is-on", j === i));
  const quotes = r.items.filter((x) => x.quote).map((x) => x.quote);
  const exp = r.expected.length ? r.expected.join(", ") : "geen";
  $("case").innerHTML = `<p class="idea">${highlight(r.idea, quotes)}</p>
    <div class="mini">${r.items.map((x) => `<div class="r"><b>${esc(x.area)}</b><span class="chip chip--${x.status}">${LABEL[x.status]}</span>
      ${x.quote ? `<small>“${esc(x.quote)}” · ${esc(x.trigger || "")}</small>` : ""}${x.note ? `<small class="bad">${esc(x.note)}</small>` : ""}</div>`).join("")}</div>
    <p class="exp">Verwacht relevant (eigen inschatting): ${esc(exp)}${r.optional.length ? ` · optioneel: ${esc(r.optional.join(", "))}` : ""}</p>`;
}

function renderRuns() {
  $("honest").innerHTML = `<b>Let op, lees dit eerst.</b> ${esc(DATA.run_label)} (${esc(DATA.run_date)}). Deze beoordelingen zijn zonder API handmatig opgesteld volgens dezelfde regels als de systeemprompt. De citaat-check en de scoring zijn wel de echte code uit de repo. Het is geen meting van een model via <code>eval.py</code>, en niet blind: de verwachtingen zijn door dezelfde auteur geschreven.`;
  $("casetabs").innerHTML = DATA.runs.map((r, i) => `<button type="button" class="pill">${esc(r.id.slice(0, 2))} ${esc(r.id.slice(3).replace(/_/g, " "))}</button>`).join("");
  document.querySelectorAll("#casetabs button").forEach((b, i) => (b.onclick = () => renderCase(i)));
  renderCase(0);
  const rows = DATA.areas.map((a) => { const s = DATA.scoreboard[a.id] || {}; return `<tr><td>${esc(a.name)}</td><td>${s.missed ?? 0}</td><td>${s.onzeker_expected ?? 0}</td><td>${s.false_alarm ?? 0}</td><td>${s.quote_fail ?? 0}</td></tr>`; });
  const tot = (k) => DATA.areas.reduce((n, a) => n + ((DATA.scoreboard[a.id] || {})[k] || 0), 0);
  $("score").innerHTML = `<tr><th>Gebied</th><th>Gemist</th><th>Onzeker*</th><th>Onterecht alarm</th><th>Citaat-fout</th></tr>${rows.join("")}<tr><td>Totaal</td><td>${tot("missed")}</td><td>${tot("onzeker_expected")}</td><td>${tot("false_alarm")}</td><td>${tot("quote_fail")}</td></tr>`;
  $("scorenote").textContent = "* Verwacht relevant, maar als onzeker beoordeeld. Een totaal van nul zegt hier weinig: de beoordelaar kende de verwachtingen. Een echte meting vraagt een blinde run van eval.py met een model.";
  const t = DATA.tamper, bad = t.items.find((x) => x.note);
  $("tamper").innerHTML = `<p class="idea">${esc(t.idea)}</p>
    <p><b>Het model beweert:</b> “voedsel- en gezondheidsclaims: relevant”, met als citaat <s>“helpt tegen krampen in de kuiten”</s>.</p>
    <p><b>De code controleert:</b> staat dit letterlijk in de invoer? ${quoteInText("helpt tegen krampen in de kuiten", t.idea) ? "Ja" : "<span class='bad'>Nee.</span>"}</p>
    <p><b>Uitkomst:</b> <span class="chip chip--${bad.status}">${LABEL[bad.status]}</span> <span class="bad">${esc(bad.note)}</span></p>
    <p class="exp">${esc(t.note)} Gewone citaten ziet u hierboven oplichten in de tekst.</p>`;
}

function fmt(d) { const [y, m, dd] = d.split("-"); return `${dd ? dd + " " : ""}${MONTHS[+m - 1]} ${y}`; }
function renderTimeline() {
  const today = DATA.today;
  const items = DATA.timeline.filter((x) => tlArea === "all" || x.area_id === tlArea);
  const card = (x, past) => `<div class="it ${past ? "past" : ""}"><span class="d">${x.date ? fmt(x.date) : esc(x.date_label)}</span><span class="t">${esc(x.area)} · ${EVLABEL[x.evidence]}</span>
    <p>${esc(x.text.length > 230 ? x.text.slice(0, 227) + "…" : x.text)} <a href="${esc(x.url)}" target="_blank" rel="noopener">bron</a></p></div>`;
  const dated = items.filter((x) => x.date), undated = items.filter((x) => !x.date);
  const key = (x) => (x.date.length === 7 ? x.date + "-31" : x.date);
  const up = dated.filter((x) => key(x) >= today), past = dated.filter((x) => key(x) < today).reverse();
  $("tl").innerHTML = `<div class="tl"><span class="today">Vandaag · ${fmt(today)}</span>${up.map((x) => card(x, false)).join("") || "<p>Niets gepland.</p>"}</div>
    <details><summary>Al ingegaan (${past.length})</summary><div class="tl">${past.map((x) => card(x, true)).join("")}</div></details>
    ${undated.length ? `<details><summary>Zonder vaste datum (${undated.length})</summary><div class="tl">${undated.map((x) => card(x, false)).join("")}</div></details>` : ""}`;
}

function renderCards() {
  $("cards").innerHTML = DATA.areas.map((a, i) => {
    const total = Object.values(a.evidence).reduce((x, y) => x + y, 0), tc = a.evidence.text_checked || 0;
    const bar = ["text_checked", "primary_page", "search_snippet", "secondary"].filter((k) => a.evidence[k])
      .map((k) => `<i class="ev-${k}" style="width:${(a.evidence[k] / total) * 100}%" title="${a.evidence[k]}× ${EVLABEL[k]}"></i>`).join("");
    return `<div class="card"><div class="n">0${i + 1}</div><h3>${esc(a.name)}</h3><p>${esc(a.summary)}</p>
      <div class="evbar" role="img" aria-label="Onderbouwing: ${tc} van ${total} feiten in wettekst nagelezen">${bar}</div>
      <div class="evnote">${tc} van ${total} feiten in de wettekst nagelezen</div></div>`;
  }).join("");
}

fetch("data.json").then((r) => r.json()).then((d) => {
  DATA = d;
  renderCards(); renderRuns();
  $("tlfilter").innerHTML = `<button type="button" class="pill is-on" data-a="all">Alles</button>` + d.areas.map((a) => `<button type="button" class="pill" data-a="${a.id}">${esc(SHORT[a.id] || a.name)}</button>`).join("");
  document.querySelectorAll("#tlfilter button").forEach((b) => (b.onclick = () => { tlArea = b.dataset.a; document.querySelectorAll("#tlfilter button").forEach((x) => x.classList.toggle("is-on", x === b)); renderTimeline(); }));
  renderTimeline();
  $("go").disabled = false;
});
$("examples").innerHTML = EXAMPLES.map((t) => `<button type="button" class="pill">${esc(t.slice(0, 34))}…</button>`).join("");
document.querySelectorAll("#examples button").forEach((b, i) => (b.onclick = () => { $("idea").value = EXAMPLES[i]; $("go").click(); }));
$("go").onclick = () => { const t = $("idea").value.trim(); if (t && DATA) renderDemo(t, assess(t)); };
