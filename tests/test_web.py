from legal_radar.areas import load_knowledge_base
from legal_radar.classify import assess
from legal_radar.web import DemoClient, build_view


def test_demo_quotes_are_literal_and_view_uses_yaml():
    kb = load_knowledge_base()
    idea = "Ik verkoop een shot dat SPIERKRAMP voorkomt via een webshop"
    items = assess(DemoClient(), kb, idea, model="demo")
    assert all(i.quote_ok for i in items)
    view = {v["area"]: v for v in build_view(kb, items)}
    row = view["Voedsel- en gezondheidsclaims"]
    assert row["status"] == "relevant" and row["quote"] == "SPIERKRAMP"
    assert any("Verordening (EG) 1924/2006" in l["text"] for l in row["laws"])
    assert "laws" not in view["Financiële regelgeving (Wft, MiCA, witwassen)"]
