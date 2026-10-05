"""Minimale lokale webinterface (alleen standaardbibliotheek). Start: legal-radar-web"""
from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

from dotenv import load_dotenv

from .areas import load_knowledge_base
from .classify import TOOL_NAME, assess, get_model_name
from .models import AreaStatus, CheckedAssessment, KnowledgeBase

# Demo-modus: trefwoorden i.p.v. een model. Alleen om de interface te tonen, niet voor echte beoordeling.
DEMO_KEYWORDS = {
    "privacy": ("privacy_q1", ["account", "klantgegevens", "locatie", "gebruikers", "klantenpas", "profiel"]),
    "consumentenrecht": ("consumenten_q1", ["webshop", "consument", "abonnement", "verkoop"]),
    "productaansprakelijkheid": ("product_q1", ["product", "importeer", "produceren", "airbag"]),
    "voedsel_gezondheidsclaims": ("voedsel_q2", ["spierkramp", "supplement", "shot", "gezondheid", "herstel"]),
    "financieel": ("financieel_q1", ["bitcoin", "crypto", "wallet", "krediet", "belegg"]),
}


class DemoClient:
    """Bootst de API na met trefwoorden; levert een citaat dat letterlijk in de invoer staat."""

    def __init__(self):
        self.messages = self

    def create(self, **kw):
        text = kw["messages"][0]["content"]
        low = text.casefold()
        areas = []
        for area_id, (trigger, words) in DEMO_KEYWORDS.items():
            hit = next((w for w in words if w in low), None)
            if hit:
                i = low.index(hit)
                areas.append({"area_id": area_id, "status": "relevant", "trigger_id": trigger, "quote": text[i:i + len(hit)]})
            else:
                areas.append({"area_id": area_id, "status": "niet_relevant"})
        return SimpleNamespace(content=[SimpleNamespace(type="tool_use", name=TOOL_NAME, input={"areas": areas})])


def build_view(kb: KnowledgeBase, items: list[CheckedAssessment]) -> list[dict]:
    """Alle wetsverwijzingen en bronnen komen uit de YAML, nooit uit de modeloutput."""
    out = []
    for it in items:
        a = kb.area(it.area_id)
        t = next((t for t in a.trigger_questions if t.id == it.trigger_id), None)
        row = {"area": a.name, "status": it.status.value, "reason": t.text if t else None,
               "quote": it.quote, "note": it.note}
        if it.status is not AreaStatus.niet_relevant:
            row["summary"] = a.summary_nl.strip()
            row["laws"] = [{"text": f"{l.reference}: {l.what_nl}", "url": l.source_url} for l in a.laws]
            row["sources"] = [{"title": s.title, "url": s.url} for s in a.sources]
        out.append(row)
    return out


PAGE = """<!doctype html><html lang="nl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Legal Radar</title>
<style>
:root{--bg:#fafaf7;--fg:#1c1c1a;--mut:#6b6b66;--card:#fff;--line:#e3e2dc;--ok:#2f6b3f;--warn:#9a6a00;--rel:#a3341f}
@media(prefers-color-scheme:dark){:root{--bg:#161614;--fg:#eeeee9;--mut:#a09f98;--card:#1f1f1c;--line:#34332f;--ok:#7fc08f;--warn:#e0b04a;--rel:#ee8a76}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}
main{max-width:760px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.5rem;margin:0 0 4px}p.sub{color:var(--mut);margin:0 0 16px}
textarea{width:100%;min-height:140px;padding:12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font:inherit;box-sizing:border-box}
button{margin-top:10px;padding:10px 18px;border:0;border-radius:8px;background:var(--fg);color:var(--bg);font:inherit;cursor:pointer}
button:disabled{opacity:.5}
.mode{font-size:.85rem;color:var(--mut);margin-top:6px}.demo{color:var(--warn)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-top:12px}
.card h2{font-size:1.05rem;margin:0}.tag{font-weight:600}.relevant{color:var(--rel)}.onzeker{color:var(--warn)}.niet_relevant{color:var(--ok)}
blockquote{margin:8px 0;padding-left:10px;border-left:3px solid var(--line);color:var(--mut)}
details{margin-top:8px}summary{cursor:pointer;color:var(--mut)}li{margin:4px 0}a{color:inherit}
.disc{margin-top:24px;color:var(--mut);font-size:.9rem}.err{color:var(--rel)}
</style>
<main>
<h1>Legal Radar</h1>
<p class="sub">Beschrijf uw idee. U ziet op welke rechtsgebieden u moet letten. Dit is geen oordeel over wat mag.</p>
<textarea id="idea" placeholder="Bijvoorbeeld: Ik verkoop een sportshot met magnesium dat spierkramp voorkomt, via een webshop."></textarea>
<button id="go">Toon rechtsgebieden</button>
<div class="mode" id="mode"></div>
<div id="out"></div>
<p class="disc" id="disc"></p>
</main>
<script>
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const label={relevant:"Relevant: hier moet u naar kijken",onzeker:"Onzeker: uitzoeken",niet_relevant:"Niet relevant volgens de invoer"};
fetch("/api/info").then(r=>r.json()).then(i=>{
  $("mode").innerHTML=i.demo?'<span class="demo">Demo-modus: trefwoorden in plaats van een model (geen API-sleutel gevonden).</span>':"Model: "+esc(i.model);
  $("disc").textContent=i.disclaimer});
$("go").onclick=async()=>{
  const idea=$("idea").value.trim(); if(!idea) return;
  $("go").disabled=true; $("out").innerHTML="<p>Bezig...</p>";
  try{
    const r=await fetch("/api/assess",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({idea})});
    const d=await r.json(); if(!r.ok) throw new Error(d.error||r.status);
    $("out").innerHTML=d.areas.map(a=>`<div class="card"><h2>${esc(a.area)}</h2>
      <div class="tag ${a.status}">${label[a.status]}</div>
      ${a.reason?`<div><b>Reden:</b> ${esc(a.reason)}</div>`:""}
      ${a.quote?`<blockquote>“${esc(a.quote)}”</blockquote>`:""}
      ${a.note?`<div class="onzeker">${esc(a.note)}</div>`:""}
      ${a.laws?`<details><summary>Wetsverwijzingen en bronnen (uit de kennisbank, nog niet door een jurist gecontroleerd)</summary>
        <p>${esc(a.summary)}</p><ul>${a.laws.map(l=>`<li>${esc(l.text)} <a href="${esc(l.url)}" target="_blank" rel="noopener">bron</a></li>`).join("")}</ul>
        <b>Bronnen</b><ul>${a.sources.map(s=>`<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join("")}</ul></details>`:""}
    </div>`).join("");
  }catch(e){$("out").innerHTML='<p class="err">Er ging iets mis: '+esc(e.message)+'</p>'}
  $("go").disabled=false};
</script></html>"""


def make_handler(kb: KnowledgeBase, demo: bool):
    client = DemoClient() if demo else None

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def do_GET(self):
            if self.path == "/":
                self._send(200, PAGE.encode(), "text/html; charset=utf-8")
            elif self.path == "/api/info":
                self._json(200, {"demo": demo, "model": get_model_name(), "disclaimer": kb.meta.disclaimer_nl})
            else:
                self._send(404, b"niet gevonden", "text/plain")

        def do_POST(self):
            if self.path != "/api/assess":
                return self._send(404, b"niet gevonden", "text/plain")
            try:
                length = int(self.headers.get("Content-Length", 0))
                idea = json.loads(self.rfile.read(min(length, 20000)))["idea"].strip()
                if not idea:
                    return self._json(400, {"error": "Geen omschrijving ontvangen."})
                c = client
                if c is None:
                    import anthropic
                    c = anthropic.Anthropic()
                items = assess(c, kb, idea, model=get_model_name())
                self._json(200, {"areas": build_view(kb, items)})
            except Exception as e:  # toon een nette fout in de pagina
                self._json(500, {"error": str(e)})

        def log_message(self, *a):
            pass

    return Handler


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(prog="legal-radar-web")
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args(argv)
    demo = not os.environ.get("ANTHROPIC_API_KEY")
    kb = load_knowledge_base()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(kb, demo))
    print(f"Legal Radar draait op http://127.0.0.1:{args.port}  ({'demo-modus' if demo else 'model: ' + get_model_name()})  Stop met Ctrl-C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
