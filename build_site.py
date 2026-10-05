"""Genereert docs/data.json uit data/legal_areas.yaml (voor de statische GitHub-pagina)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from legal_radar.areas import load_knowledge_base  # noqa: E402
from legal_radar.web import DEMO_KEYWORDS  # noqa: E402

kb = load_knowledge_base()
areas = []
for a in kb.areas:
    trigger, words = DEMO_KEYWORDS[a.id]
    areas.append({
        "id": a.id, "name": a.name, "summary": a.summary_nl.strip(),
        "trigger_id": trigger,
        "trigger": next(t.text for t in a.trigger_questions if t.id == trigger),
        "keywords": words,
        "laws": [{"ref": l.reference, "what": l.what_nl, "url": l.source_url} for l in a.laws],
        "sources": [{"title": s.title, "url": s.url} for s in a.sources],
    })
Path("docs/data.json").write_text(json.dumps({"disclaimer": kb.meta.disclaimer_nl, "accessed": kb.meta.accessed, "areas": areas}, ensure_ascii=False), encoding="utf-8")
print("docs/data.json geschreven:", len(areas), "gebieden")
