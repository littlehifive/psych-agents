from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from theory_council import server
from theory_council import conversation

FAKE_RESULT_TEMPLATE: Dict[str, Any] = {
    "raw_problem": "Base problem",
    "framed_problem": "Framed problem",
    "im_summary": "IM summary",
    "theory_outputs": {},
    "debate_summary": "debate",
    "theory_ranking": "ranking",
    "final_synthesis": "1. Problem Framing\n\n2. Theory Council Debate\n\n3. Intervention Mapping Guide\n\n4. Recommended Intervention Concept(s)",
    "sections": {
        "problem_framing": "PF",
        "theory_council_debate": "Debate",
        "intervention_mapping_guide": "Guide",
        "recommended_intervention_concepts": "Concepts",
    },
    "agent_traces": [
        {
            "agent_key": "problem_framer",
            "agent_label": "Problem Framer",
            "output": "Framed",
            "started_at": "2025-01-01T00:00:00Z",
            "completed_at": "2025-01-01T00:00:01Z",
            "duration_ms": 1000.0,
        },
        {
            "agent_key": "integrator",
            "agent_label": "Integrator",
            "output": "Final",
            "started_at": "2025-01-01T00:00:02Z",
            "completed_at": "2025-01-01T00:00:03Z",
            "duration_ms": 1000.0,
        },
    ],
}


@pytest.fixture(autouse=True)
def stub_dependencies(monkeypatch: pytest.MonkeyPatch):
    server.RUN_LOG.clear()
    server.SESSION_STORE = server.InMemorySessionStore()

    def fake_run(problem: str, *_, **__) -> Dict[str, Any]:
        result = deepcopy(FAKE_RESULT_TEMPLATE)
        result["raw_problem"] = problem
        return result

    def fake_chat(messages, metadata=None):
        return {
            "response": "ok",
            "messages": [*messages, {"role": "assistant", "content": "ok"}],
            "model": "stub",
        }

    monkeypatch.setattr(server, "run_council_pipeline", fake_run)
    monkeypatch.setattr(conversation, "run_council_pipeline", fake_run)
    monkeypatch.setattr(conversation, "generate_chat_response", fake_chat)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(server.app)


def test_council_run_returns_structured_payload(client: TestClient):
    response = client.post("/council/run", json={"problem": "Test issue"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["result"]["raw_problem"] == "Test issue"
    assert "agent_traces" in data["result"]


def test_conversation_endpoint_runs_agent_mode(client: TestClient):
    payload = {
        "messages": [{"role": "user", "content": "Need agent help"}],
        "agent_enabled": True,
    }
    response = client.post("/conversation/send", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "agent"
    assert data["agent_result"]["sections"]["problem_framing"] == "PF"
    assert data["auto_disable_agent"] is True


def test_conversation_endpoint_runs_chat_mode(client: TestClient):
    payload = {"messages": [{"role": "user", "content": "hello there"}], "agent_enabled": False}
    response = client.post("/conversation/send", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "chat"
    assert data["assistant_message"]["content"] == "ok"


def test_streaming_endpoint_replays_agent_updates(client: TestClient):
    with client.stream("POST", "/council/run/stream", json={"problem": "Stream me"}) as stream:
        body = "".join(list(stream.iter_text()))
    assert "event: trace" in body
    assert "event: complete" in body

