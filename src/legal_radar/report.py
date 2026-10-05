"""Markdown-rapport. Wetsverwijzingen, uitleg en bronnen komen uitsluitend uit de YAML."""
from __future__ import annotations

from .models import AreaStatus, CheckedAssessment, KnowledgeBase

STATUS_LABEL = {
    AreaStatus.relevant: "Relevant: hier moet u naar kijken",
    AreaStatus.onzeker: "Onzeker: uitzoeken",
    AreaStatus.niet_relevant: "Niet relevant volgens de invoer",
}


def render_report(kb: KnowledgeBase, items: list[CheckedAssessment], idea: str) -> str:
    lines = ["# Legal Radar: oriëntatie op rechtsgebieden", "", "## Uw idee", "", f"> {idea.strip()}", ""]
    for item in items:
        area = kb.area(item.area_id)
        lines += [f"## {area.name}", "", f"**Status:** {STATUS_LABEL[item.status]}", ""]
        if item.status is AreaStatus.niet_relevant:
            lines += ["Op basis van uw omschrijving lijkt dit gebied niet aan de orde. Dit is geen oordeel.", ""]
            if item.note:
                lines += [item.note, ""]
            continue
        trigger = next((t for t in area.trigger_questions if t.id == item.trigger_id), None)
        reason = trigger.text if trigger else "De omschrijving is onvoldoende om te bepalen of dit gebied speelt."
        lines += [f"**Reden (triggervraag):** {reason}", ""]
        lines += [f"**Citaat uit uw omschrijving:** \"{item.quote}\"" if item.quote else "**Citaat uit uw omschrijving:** geen", ""]
        if item.note:
            lines += [f"**Let op:** {item.note}", ""]
        lines += [f"**Waar dit gebied over gaat:** {area.summary_nl.strip()}", "", "**Wetsverwijzingen (uit de kennisbank):**", ""]
        for law in area.laws:
            lines.append(f"- {law.reference}: {law.what_nl} ([bron]({law.source_url}))")
        lines += ["", "**Bronnen:**", ""]
        for s in area.sources:
            lines.append(f"- [{s.title}]({s.url}) (geraadpleegd {s.accessed})")
        if any(not law.verified for law in area.laws):
            lines += ["", "*De inhoud van dit gebied is nog niet door een jurist gecontroleerd (verified: false).*"]
        lines.append("")
    lines += ["---", "", f"**Disclaimer:** {kb.meta.disclaimer_nl}", ""]
    return "\n".join(lines)
