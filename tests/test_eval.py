import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import eval as ev  # noqa: E402
from legal_radar.areas import load_knowledge_base  # noqa: E402
from legal_radar.models import AreaStatus, CheckedAssessment  # noqa: E402


def _item(area, status, quote_ok=True):
    return CheckedAssessment(area_id=area, status=status, quote_ok=quote_ok)


def test_scoring_counts_missed_false_alarm_quote_fail():
    exp = {"relevant": {"privacy"}, "optional": {"financieel"}}
    items = [
        _item("privacy", AreaStatus.niet_relevant),                 # gemist
        _item("financieel", AreaStatus.relevant),                   # optioneel: geen alarm
        _item("consumentenrecht", AreaStatus.relevant, False),      # onterecht + citaat-fout
        _item("voedsel_gezondheidsclaims", AreaStatus.onzeker),     # geen verwachting, geen alarm
    ]
    s = ev.score_case(items, exp)
    assert s["privacy"]["missed"] == 1
    assert s["financieel"]["false_alarm"] == 0
    assert s["consumentenrecht"]["false_alarm"] == 1 and s["consumentenrecht"]["quote_fail"] == 1
    assert s["voedsel_gezondheidsclaims"]["false_alarm"] == 0


def test_onzeker_for_expected_is_not_missed():
    s = ev.score_case([_item("privacy", AreaStatus.onzeker)], {"relevant": {"privacy"}, "optional": set()})
    assert s["privacy"]["missed"] == 0 and s["privacy"]["onzeker_expected"] == 1


def test_all_cases_load_and_reference_known_areas():
    known = {a.id for a in load_knowledge_base().areas}
    folders = sorted(d for d in (ROOT / "cases").iterdir() if d.is_dir())
    assert len(folders) == 8
    for f in folders:
        idea, exp = ev.load_case(f)
        assert idea.strip()
        assert (exp["relevant"] | exp["optional"]) <= known, f.name
        assert not (exp["relevant"] & exp["optional"]), f.name
