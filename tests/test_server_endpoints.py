from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import server

@pytest.fixture(autouse=True)
def stub_dependencies(monkeypatch: pytest.MonkeyPatch):
    async def fake_chat_stream(messages, metadata=None):
        yield "o"
        yield "k"

    monkeypatch.setattr(server, "astream_chat_response", fake_chat_stream)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(server.app)


def test_streaming_endpoint_returns_tokens(client: TestClient):
    payload = {
        "messages": [{"role": "user", "content": "hello"}],
        "session_id": "test-session"
    }
    with client.stream("POST", "/conversation/send/stream", json=payload) as stream:
        body = "".join(list(stream.iter_text()))
    
    assert "event: started" in body
    assert "event: token" in body
    assert "chunk\": \"o\"" in body
    assert "chunk\": \"k\"" in body
    assert "event: complete" in body
    assert "test-session" in body
