"""Controle dat een citaat letterlijk in de invoer staat."""
from __future__ import annotations

import re
import unicodedata

from .models import AreaStatus, AreaAssessment, CheckedAssessment

_QUOTES = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"}


def _normalize(text: str) -> str:
    """Alleen witruimte, hoofdletters en typografische aanhalingstekens worden genegeerd."""
    text = unicodedata.normalize("NFKC", text)
    for a, b in _QUOTES.items():
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip().casefold()


def quote_in_text(quote: str | None, text: str) -> bool:
    if not quote or not quote.strip():
        return False
    return _normalize(quote) in _normalize(text)


def check_assessment(item: AreaAssessment, text: str, valid_trigger_ids: set[str]) -> CheckedAssessment:
    """Controleert het bewijs van het model. Bij ongeldig bewijs bij 'relevant' wordt de status 'onzeker'.

    'niet_relevant' heeft geen citaat nodig. Een opgegeven citaat dat niet letterlijk
    in de invoer staat wordt altijd verwijderd en gemeld (quote_ok=False).
    """
    checked = CheckedAssessment(**item.model_dump())
    notes: list[str] = []
    if item.quote is not None and item.quote.strip():
        if not quote_in_text(item.quote, text):
            checked.quote_ok = False
            checked.quote = None
            notes.append("het citaat staat niet letterlijk in de invoer")
    if item.status is AreaStatus.relevant:
        if item.trigger_id not in valid_trigger_ids:
            notes.append("de genoemde triggervraag bestaat niet voor dit gebied")
        if checked.quote is None:
            notes.append("er is geen geldig citaat als bewijs")
        if notes:
            checked.status = AreaStatus.onzeker
            checked.note = "Status gewijzigd naar onzeker: " + "; ".join(dict.fromkeys(notes)) + "."
    elif notes:
        checked.note = "Let op: " + "; ".join(notes) + ". Het citaat is genegeerd."
    return checked
