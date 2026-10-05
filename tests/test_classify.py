from types import SimpleNamespace

from legal_radar.areas import load_knowledge_base
from legal_radar.classify import TOOL_NAME, assess, build_area_prompt
from legal_radar.models import AreaStatus

IDEA = "Een app die cookies plaatst en verloren bitcoin opspoort."


class FakeClient:
    def __init__(self, payload):
        self.messages = self
        self.payload = payload
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        block = SimpleNamespace(type="tool_use", name=TOOL_NAME, input=self.payload)
        return SimpleNamespace(content=[block])


def test_prompt_contains_only_ids_names_and_triggers():
    kb = load_knowledge_base()
    prompt = build_area_prompt(kb)
    assert "privacy_q1" in prompt
    assert "art. 11.7a" not in prompt and "http" not in prompt  # geen wetsverwijzingen of bronnen naar het model


def test_assess_end_to_end_with_fake_model():
    kb = load_knowledge_base()
    payload = {"areas": [
        {"area_id": "privacy", "status": "relevant", "trigger_id": "privacy_q4", "quote": "cookies plaatst"},
        {"area_id": "financieel", "status": "relevant", "trigger_id": "financieel_q1", "quote": "gefabriceerd citaat"},
        {"area_id": "verzonnen_gebied", "status": "relevant", "trigger_id": "x", "quote": "x"},
    ]}
    client = FakeClient(payload)
    out = {i.area_id: i for i in assess(client, kb, IDEA, model="test-model")}
    assert out["privacy"].status is AreaStatus.relevant
    assert out["financieel"].status is AreaStatus.onzeker and not out["financieel"].quote_ok
    assert "verzonnen_gebied" not in out and len(out) == 5
    assert client.calls[0]["model"] == "test-model"
