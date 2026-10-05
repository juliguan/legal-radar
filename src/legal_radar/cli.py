"""CLI: legal-radar "omschrijving van uw idee" """
from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from .areas import load_knowledge_base
from .classify import assess, get_model_name
from .report import render_report


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(prog="legal-radar", description="Waar moet u juridisch op letten bij uw idee? (oriëntatie, geen advies)")
    p.add_argument("idea", nargs="?", help="Omschrijving van het idee. Zonder argument wordt stdin gelezen.")
    p.add_argument("-f", "--file", help="Lees de omschrijving uit een bestand.")
    p.add_argument("--json", action="store_true", help="Toon de gevalideerde JSON in plaats van het rapport.")
    args = p.parse_args(argv)

    if args.file:
        idea = open(args.file, encoding="utf-8").read()
    elif args.idea:
        idea = args.idea
    else:
        print("Typ uw omschrijving en sluit af met Ctrl-D:", file=sys.stderr)
        idea = sys.stdin.read()
    if not idea.strip():
        print("Geen omschrijving ontvangen.", file=sys.stderr)
        return 2

    import anthropic  # pas hier, zodat tests zonder API-sleutel werken

    kb = load_knowledge_base()
    client = anthropic.Anthropic()  # leest ANTHROPIC_API_KEY uit de omgeving (.env)
    items = assess(client, kb, idea, model=get_model_name())
    if args.json:
        import json
        print(json.dumps([i.model_dump(mode="json") for i in items], ensure_ascii=False, indent=2))
    else:
        print(render_report(kb, items, idea))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
