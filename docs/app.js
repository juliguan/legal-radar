// Demo-modus in de browser: trefwoorden i.p.v. een model. Alle wettekst en bronnen komen uit data.json (= de YAML).
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const LABEL = { relevant: "Hier kijken", onzeker: "Onzeker", niet_relevant: "Niet aan de orde" };
const EXAMPLES = [
  "Ik verkoop een sportshot met magnesium dat spierkramp voorkomt, via mijn webshop.",
  "Een app die verloren bitcoin opspoort en een voorschot vraagt.",
  "Ik schrijf een statische site over de geschiedenis van mijn dorp, zonder cookies of accounts.",
];
let DATA;

function assess(text) {
  const low = text.toLowerCase();
  return DATA.areas.map((a) => {
    const hit = a.keywords.find((k) => low.includes(k));
    if (!hit) return { a, status: "niet_relevant" };
    const i = low.indexOf(hit);
    const quote = text.slice(i, i + hit.length);
    // zelfde controle als in Python: het citaat moet letterlijk in de invoer staan
    return text.includes(quote) ? { a, status: "relevant", quote } : { a, status: "onzeker", note: "Citaat niet gevonden in de invoer." };
  });
}

function render(items) {
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

fetch("data.json").then((r) => r.json()).then((d) => {
  DATA = d;
  $("cards").innerHTML = d.areas.map((a, i) => `<div class="card"><div class="n">0${i + 1}</div><h3>${esc(a.name)}</h3><p>${esc(a.summary)}</p></div>`).join("");
  $("go").disabled = false;
});
$("examples").innerHTML = EXAMPLES.map((t) => `<button type="button" class="pill">${esc(t.slice(0, 34))}…</button>`).join("");
document.querySelectorAll("#examples button").forEach((b, i) => (b.onclick = () => { $("idea").value = EXAMPLES[i]; $("go").click(); }));
$("go").onclick = () => { const t = $("idea").value.trim(); if (t && DATA) render(assess(t)); };
