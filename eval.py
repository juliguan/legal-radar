"""Draait alle cases en rapporteert per gebied: gemiste gebieden, onterechte alarmen en citaat-fouten.

Gebruik: python eval.py [--model MODEL] [--cases cases]
Vereist ANTHROPIC_API_KEY (via .env). Het resultaat per case wordt ook opgeslagen in output/eval_results.json.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import yaml
from dotenv import load_dotenv

from legal_radar.areas import load_knowledge_base
from legal_radar.classify import assess, get_model_name
from legal_radar.models import AreaStatus, CheckedAssessment


def load_case(folder: Path) -> tuple[str, dict]:
    idea = (folder / "idea.txt").read_text(encoding="utf-8")
    expected = yaml.safe_load((folder / "expected.yaml").read_text(encoding="utf-8")) or {}
    return idea, {"relevant": set(expected.get("relevant") or []), "optional": set(expected.get("optional") or [])}


def score_case(items: list[CheckedAssessment], expected: dict) -> dict[str, dict[str, int]]:
    """Per gebied: missed, onzeker_expected, false_alarm, quote_fail (0 of 1)."""
    out: dict[str, dict[str, int]] = {}
    for it in items:
        exp = it.area_id in expected["relevant"]
        opt = it.area_id in expected["optional"]
        out[it.area_id] = {
            "missed": int(exp and it.status is AreaStatus.niet_relevant),
            "onzeker_expected": int(exp and it.status is AreaStatus.onzeker),
            "false_alarm": int(it.status is AreaStatus.relevant and not exp and not opt),
            "quote_fail": int(not it.quote_ok),
        }
    return out


def summarize(per_case: dict[str, dict[str, dict[str, int]]]) -> dict[str, dict[str, int]]:
    total: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for scores in per_case.values():
        for area, s in scores.items():
            for k, v in s.items():
                total[area][k] += v
    return {a: dict(v) for a, v in total.items()}


def format_table(total: dict[str, dict[str, int]]) -> str:
    head = f"{'gebied':<28}{'gemist':>8}{'onzeker*':>10}{'onterecht':>11}{'citaat-fout':>13}"
    rows = [head, "-" * len(head)]
    sums = defaultdict(int)
    for area, s in total.items():
        rows.append(f"{area:<28}{s['missed']:>8}{s['onzeker_expected']:>10}{s['false_alarm']:>11}{s['quote_fail']:>13}")
        for k, v in s.items():
            sums[k] += v
    rows.append("-" * len(head))
    rows.append(f"{'totaal':<28}{sums['missed']:>8}{sums['onzeker_expected']:>10}{sums['false_alarm']:>11}{sums['quote_fail']:>13}")
    rows.append("* onzeker: verwacht relevant, maar het model (of de citaat-check) zei 'onzeker'. Telt niet als gemist.")
    return "\n".join(rows)


def main() -> int:
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--cases", default="cases")
    p.add_argument("--model", default=None)
    args = p.parse_args()

    import anthropic

    kb = load_knowledge_base()
    client = anthropic.Anthropic()
    model = args.model or get_model_name()
    per_case, details = {}, {}
    for folder in sorted(d for d in Path(args.cases).iterdir() if d.is_dir()):
        idea, expected = load_case(folder)
        items = assess(client, kb, idea, model=model)
        per_case[folder.name] = score_case(items, expected)
        details[folder.name] = [i.model_dump(mode="json") for i in items]
        flags = [f"{a}:{k}" for a, s in per_case[folder.name].items() for k, v in s.items() if v]
        print(f"{folder.name}: {', '.join(flags) or 'ok'}")
    total = summarize(per_case)
    print(f"\nModel: {model}\n")
    print(format_table(total))
    Path("output").mkdir(exist_ok=True)
    Path("output/eval_results.json").write_text(
        json.dumps({"model": model, "per_case": per_case, "total": total, "details": details}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
