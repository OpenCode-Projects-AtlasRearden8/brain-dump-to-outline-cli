import json

import pytest

from brainDumpOutline import llm
from brainDumpOutline.config import Config


class FakeHTTPResponse:
    def __init__(self, body: bytes, status: int = 200):
        import io

        self._reader = io.BytesIO(body)
        self.status = status

    def read(self) -> bytes:
        return self._reader.read()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def make_config(**overrides):
    defaults = dict(
        base_url="http://localhost:11434/v1",
        model="llama3.2",
        timeout=5,
    )
    defaults.update(overrides)
    return Config(**defaults)


def fake_endpoint(content: str):
    body = json.dumps(
        {"choices": [{"message": {"role": "assistant", "content": content}}]}
    ).encode("utf-8")

    def handler(request, timeout):
        assert request.method == "POST"
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["model"] == "llama3.2"
        assert payload["messages"][0]["role"] == "system"
        return FakeHTTPResponse(body)

    return handler


def good_content():
    return json.dumps(
        {
            "groups": [
                {"title": "Errands", "items": ["buy printer ink", "refill meds"]},
                {"title": "Writing", "items": ["outline chapter 4"]},
            ],
            "decisions": ["keep or sell the big desk?"],
            "next_actions": ["buy printer ink", "refill meds", "outline chapter 4", "extra ignored"],
        }
    )


def test_draft_outline_parses_mocked_response(monkeypatch):
    monkeypatch.setattr(llm, "chat_completion", lambda text, cfg: good_content())
    outline = llm.draft_outline("dump text", make_config())
    assert [group.title for group in outline.groups] == ["Errands", "Writing"]
    assert outline.next_actions == ["buy printer ink", "refill meds", "outline chapter 4"]
    assert outline.decisions == ["keep or sell the big desk?"]


def test_chat_completion_sends_json_via_mocked_urlopen(monkeypatch):
    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_endpoint(good_content()))
    content = llm.chat_completion("dump text", make_config())
    assert json.loads(content) == json.loads(good_content())


def test_chat_completion_includes_bearer_when_key_configured(monkeypatch):
    seen = {}

    def handler(request, timeout):
        seen["auth"] = request.headers.get("Authorization")
        return fake_endpoint(good_content())(request, timeout)

    monkeypatch.setattr(llm.urllib.request, "urlopen", handler)
    monkeypatch.setenv("FAKE_KEY_ENV", "abc123")
    llm.chat_completion("text", make_config(api_key_env="FAKE_KEY_ENV"))
    assert seen["auth"] == "Bearer abc123"


def test_chat_completion_http_error(monkeypatch):
    import urllib.error

    def boom(request, timeout):
        raise urllib.error.HTTPError("http://x", 500, "nope", {}, None)

    monkeypatch.setattr(llm.urllib.request, "urlopen", boom)
    with pytest.raises(llm.LLMError, match="HTTP 500"):
        llm.chat_completion("text", make_config())


def test_chat_completion_connection_error(monkeypatch):
    import urllib.error

    def boom(request, timeout):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(llm.urllib.request, "urlopen", boom)
    with pytest.raises(llm.LLMError, match="connection refused"):
        llm.chat_completion("text", make_config())


def test_extract_json_tolerates_fences_and_prose():
    content = "Sure! Here is the JSON:\n```json\n" + good_content() + "\n```\n"
    data = llm.extract_json(content)
    assert data["decisions"] == ["keep or sell the big desk?"]


def test_extract_json_rejects_garbage():
    with pytest.raises(llm.LLMError):
        llm.extract_json("no json here at all")


def test_outline_from_json_rejects_empty_payload():
    with pytest.raises(llm.LLMError, match="no usable"):
        llm.outline_from_json({"groups": [], "decisions": [], "next_actions": []})


def test_outline_from_json_skips_malformed_groups():
    data = {"groups": ["not a dict", {"title": "X", "items": ["item"]}]}
    outline = llm.outline_from_json(data)
    assert [group.title for group in outline.groups] == ["X"]
