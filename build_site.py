"""Genereert docs/data.json uit data/legal_areas.yaml en data/manual_runs.yaml (voor de statische GitHub-pagina)."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, "src")
sys.path.insert(0, ".")
from eval import load_case, score_case, summarize  # noqa: E402
from legal_radar.areas import load_knowledge_base  # noqa: E402
from legal_radar.classify import normalize  # noqa: E402
from legal_radar.models import Assessment  # noqa: E402
from legal_radar.web import DEMO_KEYWORDS  # noqa: E402

ISO = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


def run_case(kb, idea, areas):
    return normalize(Assessment.model_validate({"areas": areas}), kb, idea)


def view(kb, items):
    out = []
    for it in items:
        a = kb.area(it.area_id)
        t = next((t for t in a.trigger_questions if t.id == it.trigger_id), None)
        out.append({"area_id": a.id, "area": a.name, "status": it.status.value, "trigger": t.text if t else None,
                    "quote": it.quote, "quote_ok": it.quote_ok, "note": it.note})
    return out


def build():
    kb = load_knowledge_base()
    manual = yaml.safe_load(Path("data/manual_runs.yaml").read_text(encoding="utf-8"))
    areas, timeline = [], []
    for a in kb.areas:
        trigger, words = DEMO_KEYWORDS[a.id]
        ev = Counter(x.evidence.value for x in [*a.laws, *a.common_mistakes, *a.recent_changes])
        areas.append({
            "id": a.id, "name": a.name, "summary": a.summary_nl.strip(),
            "trigger_id": trigger, "trigger": next(t.text for t in a.trigger_questions if t.id == trigger),
            "keywords": words, "evidence": dict(ev),
            "laws": [{"ref": l.reference, "what": l.what_nl, "url": l.source_url} for l in a.laws],
            "sources": [{"title": s.title, "url": s.url} for s in a.sources],
        })
        for c in a.recent_changes:
            timeline.append({"area_id": a.id, "area": a.name, "date": c.date if ISO.match(c.date) else None,
                             "date_label": c.date, "text": c.text, "url": c.source_url, "evidence": c.evidence.value})
    timeline.sort(key=lambda x: (x["date"] is None, x["date"] or ""))

    runs, per_case = [], {}
    for folder in sorted(d for d in Path("cases").iterdir() if d.is_dir()):
        idea, expected = load_case(folder)
        items = run_case(kb, idea.strip(), manual["runs"][folder.name]["areas"])
        per_case[folder.name] = score_case(items, expected)
        runs.append({"id": folder.name, "idea": idea.strip(), "expected": sorted(expected["relevant"]),
                     "optional": sorted(expected["optional"]), "items": view(kb, items), "score": per_case[folder.name]})
    t = manual["tamper_test"]
    idea, _ = load_case(Path("cases") / t["case"])
    tamper = {"idea": idea.strip(), "note": t["note"], "items": view(kb, run_case(kb, idea.strip(), t["areas"]))}

    Path("docs/data.json").write_text(json.dumps({
        "disclaimer": kb.meta.disclaimer_nl, "accessed": kb.meta.accessed, "today": "2026-10-06",
        "run_label": manual["meta"]["label"], "run_date": manual["meta"]["made_on"],
        "areas": areas, "timeline": timeline, "runs": runs, "tamper": tamper, "scoreboard": summarize(per_case),
    }, ensure_ascii=False), encoding="utf-8")
    print("docs/data.json:", len(areas), "gebieden,", len(runs), "runs,", len(timeline), "tijdlijnitems")
    return summarize(per_case)


if __name__ == "__main__":
    print(json.dumps(build(), indent=1))
