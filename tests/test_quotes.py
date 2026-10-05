from legal_radar.models import AreaAssessment, AreaStatus
from legal_radar.quotes import check_assessment, quote_in_text

TEXT = "Een app die\nverloren   bitcoin opspoort tegen een “succesfee” van 10%."
IDS = {"financieel_q1", "financieel_q3"}


def test_exact_quote_found():
    assert quote_in_text("verloren bitcoin opspoort", TEXT)


def test_whitespace_case_and_typographic_quotes_ignored():
    assert quote_in_text("App die verloren BITCOIN", TEXT)
    assert quote_in_text('tegen een "succesfee"', TEXT)


def test_changed_words_not_found():
    assert not quote_in_text("verloren bitcoins opsporen", TEXT)


def test_empty_or_none_is_not_a_quote():
    assert not quote_in_text(None, TEXT)
    assert not quote_in_text("   ", TEXT)


def test_valid_relevant_stays_relevant():
    item = AreaAssessment(area_id="financieel", status=AreaStatus.relevant, trigger_id="financieel_q1", quote="verloren bitcoin")
    out = check_assessment(item, TEXT, IDS)
    assert out.status is AreaStatus.relevant and out.quote_ok and out.note is None


def test_fabricated_quote_becomes_onzeker_and_is_reported():
    item = AreaAssessment(area_id="financieel", status=AreaStatus.relevant, trigger_id="financieel_q1", quote="een crypto-exchange")
    out = check_assessment(item, TEXT, IDS)
    assert out.status is AreaStatus.onzeker
    assert out.quote_ok is False and out.quote is None
    assert "citaat" in out.note


def test_relevant_without_quote_becomes_onzeker():
    item = AreaAssessment(area_id="financieel", status=AreaStatus.relevant, trigger_id="financieel_q1")
    assert check_assessment(item, TEXT, IDS).status is AreaStatus.onzeker


def test_unknown_trigger_becomes_onzeker():
    item = AreaAssessment(area_id="financieel", status=AreaStatus.relevant, trigger_id="verzonnen", quote="verloren bitcoin")
    out = check_assessment(item, TEXT, IDS)
    assert out.status is AreaStatus.onzeker and "triggervraag" in out.note


def test_niet_relevant_needs_no_quote():
    item = AreaAssessment(area_id="financieel", status=AreaStatus.niet_relevant)
    out = check_assessment(item, TEXT, IDS)
    assert out.status is AreaStatus.niet_relevant and out.note is None
