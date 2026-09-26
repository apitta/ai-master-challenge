from fastapi.testclient import TestClient
import pytest

from app.api import create_app
from app.config import Settings


@pytest.fixture
def client():
    with TestClient(create_app(Settings(database_url="sqlite://"))) as c:
        yield c


def first(client, **params):
    return client.get("/opportunities", params=params).json()[0]


def test_list_is_prioritized(client):
    rows = client.get("/opportunities").json()
    assert len(rows) == 2089
    order = "ABCDR"
    keys = [(order.index(r["band"]), -r["score"]) for r in rows]
    assert keys == sorted(keys)


def test_filters_combine(client):
    rows = client.get("/opportunities", params={"region": "West", "product": ["GTK 500", "GTX Pro"]}).json()
    assert rows and all(r["region"] == "West" and r["product"] in ("GTK 500", "GTX Pro") for r in rows)
    team = client.get("/filters").json()["team"]
    assert len({t["agent"] for t in team}) == len(team)  # cada vendedor tem um só gerente/regional


def test_summary_matches_spreadsheet(client):
    s = client.get("/summary").json()
    counts = {b["band"]: b["count"] for b in s["bands"]}
    assert counts == {"A": 112, "B": 148, "C": 299, "D": 239, "R": 1291}
    assert s["pipeline_value"] == 4966215


def test_detail_explains_and_recommends(client):
    opp = first(client, band="R")
    d = client.get(f"/opportunities/{opp['id']}").json()
    assert any("138" in line for line in d["explanation"])
    keys = {c["key"] for c in d["commands"]}
    assert {"reengage", "requalify", "close_stalled"} <= keys
    assert sum(c["primary"] for c in d["commands"]) == 1


def test_requalify_moves_out_of_recycle(client):
    opp = first(client, band="R")
    d = client.post(f"/opportunities/{opp['id']}/commands", json={"command": "requalify"}).json()
    assert d["stage"] == "Prospecting" and d["band"] != "R"
    assert d["activities"][0]["band_before"] == "R"


def test_prospecting_advance_then_win(client):
    opp = first(client, stage="Prospecting")
    d = client.post(f"/opportunities/{opp['id']}/commands", json={"command": "advance_to_engaging"}).json()
    assert d["stage"] == "Engaging" and d["days_engaging"] == 0
    d = client.post(f"/opportunities/{opp['id']}/commands", json={"command": "mark_won"}).json()
    assert d["stage"] == "Won" and d["band"] is None and d["close_value"] == d["list_price"]
    assert opp["id"] not in {r["id"] for r in client.get("/opportunities").json()}


def test_invalid_commands_are_rejected(client):
    opp = first(client, band="A")
    assert client.post(f"/opportunities/{opp['id']}/commands", json={"command": "close_stalled"}).status_code == 400
    assert client.post(f"/opportunities/{opp['id']}/commands", json={"command": "mark_lost"}).status_code == 400
    assert client.get("/opportunities/NOPE").status_code == 404


def test_log_activity_sets_next_step(client):
    opp = first(client, band="A")
    d = client.post(f"/opportunities/{opp['id']}/commands",
                    json={"command": "log_activity", "kind": "Ligação", "next_step": "Enviar proposta"}).json()
    assert d["next_step"] == "Enviar proposta"
    assert d["next_step_date"] == "2018-01-02"  # faixa A: referência + 48h


def test_file_database_persists_between_restarts(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path}/app.db")
    with TestClient(create_app(settings)) as c:
        opp = first(c, band="A")
        c.post(f"/opportunities/{opp['id']}/commands", json={"command": "mark_lost", "reason": "Sem orçamento"})
    with TestClient(create_app(settings)) as c:
        d = c.get(f"/opportunities/{opp['id']}").json()
        assert d["stage"] == "Lost" and d["lost_reason"] == "Sem orçamento"
