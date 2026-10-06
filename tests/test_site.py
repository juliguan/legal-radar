import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_site  # noqa: E402


def test_site_data_builds_and_manual_runs_pass_the_real_quote_check():
    totals = build_site.build()
    data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
    assert len(data["runs"]) == 8
    assert sum(v["quote_fail"] for v in totals.values()) == 0  # echte voorbeelden: citaten staan in de invoer
    assert "handmatig" in data["run_label"].lower()  # eerlijk label blijft meegeleverd


def test_tamper_example_is_rejected_by_the_code():
    data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
    row = next(i for i in data["tamper"]["items"] if i["area_id"] == "voedsel_gezondheidsclaims")
    assert row["status"] == "onzeker" and row["quote_ok"] is False and row["note"]


def test_timeline_has_dated_items_with_sources():
    data = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
    dated = [t for t in data["timeline"] if t["date"]]
    assert len(dated) >= 15
    assert all(t["url"].startswith("http") for t in data["timeline"])
    assert [t["date"] for t in dated] == sorted(t["date"] for t in dated)
