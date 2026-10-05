import yaml
import pytest
from pydantic import ValidationError

from legal_radar.areas import DEFAULT_PATH, load_knowledge_base
from legal_radar.classify import normalize
from legal_radar.models import Assessment, AreaAssessment, AreaStatus
from legal_radar.report import render_report

EXPECTED_AREAS = {"privacy", "consumentenrecht", "productaansprakelijkheid", "voedsel_gezondheidsclaims", "financieel"}


@pytest.fixture(scope="module")
def kb():
    return load_knowledge_base()


def test_yaml_validates_and_has_five_areas(kb):
    assert {a.id for a in kb.areas} == EXPECTED_AREAS


def test_everything_is_unverified(kb):
    for a in kb.areas:
        for item in [*a.laws, *a.common_mistakes, *a.recent_changes]:
            assert item.verified is False


def test_every_fact_has_a_source_url(kb):
    for a in kb.areas:
        for item in [*a.laws, *a.common_mistakes, *a.recent_changes, *a.applies_to]:
            assert item.source_url.startswith("http")
        for t in a.trigger_questions:
            assert all(u.startswith("http") for u in t.based_on)
        for s in a.sources:
            assert s.url.startswith("http") and s.accessed


def test_trigger_counts_between_3_and_5(kb):
    for a in kb.areas:
        assert 3 <= len(a.trigger_questions) <= 5


def test_trigger_ids_unique_across_areas(kb):
    ids = [t.id for a in kb.areas for t in a.trigger_questions]
    assert len(ids) == len(set(ids))


def test_no_invented_article_numbers(kb):
    """Een ontbrekend artikel moet expliciet 'TODO verify' heten, nooit leeg zijn."""
    for a in kb.areas:
        for law in a.laws:
            assert law.article.strip(), law.id


def test_missing_source_url_is_rejected():
    raw = yaml.safe_load(open(DEFAULT_PATH, encoding="utf-8"))
    del raw["areas"][0]["laws"][0]["source_url"]
    from legal_radar.models import KnowledgeBase
    with pytest.raises(ValidationError):
        KnowledgeBase.model_validate(raw)


def test_unknown_area_from_model_is_dropped_and_missing_become_onzeker(kb):
    raw = Assessment(areas=[
        AreaAssessment(area_id="arbeidsrecht", status=AreaStatus.relevant, trigger_id="x", quote="y"),
        AreaAssessment(area_id="privacy", status=AreaStatus.niet_relevant),
    ])
    out = normalize(raw, kb, "iets")
    assert [i.area_id for i in out] == [a.id for a in kb.areas]
    assert out[0].status is AreaStatus.niet_relevant
    assert all(i.status is AreaStatus.onzeker for i in out[1:])


def test_report_takes_law_text_from_yaml_not_model(kb):
    idea = "Een app die cookies plaatst"
    raw = Assessment(areas=[AreaAssessment(area_id="privacy", status=AreaStatus.relevant,
                                           trigger_id="privacy_q4", quote="cookies plaatst")])
    md = render_report(kb, normalize(raw, kb, idea), idea)
    assert "Telecommunicatiewet art. 11.7a" in md
    assert "Disclaimer" in md and "geen juridisch advies" in md
    assert "cookies plaatst" in md
