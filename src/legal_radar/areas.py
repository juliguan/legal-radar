"""Laden en valideren van de kennisbank (data/legal_areas.yaml)."""
from __future__ import annotations

from pathlib import Path

import yaml

from .models import KnowledgeBase

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "legal_areas.yaml"


def load_knowledge_base(path: Path | str = DEFAULT_PATH) -> KnowledgeBase:
    with open(path, encoding="utf-8") as f:
        return KnowledgeBase.model_validate(yaml.safe_load(f))
