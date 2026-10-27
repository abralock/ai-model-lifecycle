"""tests/test_reasoning_not_graded.py — hidden thinking is never graded as the answer.

A thinking model that spends its whole output budget thinking returns an empty
`content` and its thinking in a separate field (`reasoning_content` on
OpenCode Go / litellm, `reasoning` on OpenRouter). That run has no answer: it
must be recorded as an empty completion (scored as a FAIL by report.py, not
excluded as an infra error) instead of grading the thinking text. Before this
fix, Qwen3.8 Flash runs that hit the 32k limit were scored on 120k+ characters
of thinking (runs/qwen3.8-flash-vs-glm-5.3-flash, 2026-10-15).

All offline: litellm is replaced by a fake.
"""

from __future__ import annotations

import sys
import types

import pytest

import report
import runner
from common import ApiRef

GO = ApiRef(id="opencode-go", base_url="https://opencode.ai/inference/go/v1",
            api_key_env="OPENCODE_GO_API_KEY", family="chat")
THINKING = "We need answer user's request. Need produce SQL files only, fenced blocks with ### FILE: ..."
ANSWER = "### FILE: x.sql\n```sql\nSELECT 1;\n```\n"


def _fake_litellm(message: types.SimpleNamespace, finish_reason: str) -> types.SimpleNamespace:
    resp = types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=message, finish_reason=finish_reason)],
        usage={"prompt_tokens": 100, "completion_tokens": 32000, "total_tokens": 32100,
               "completion_tokens_details": {"reasoning_tokens": 31000}})

    # Gateway calls stream (tests/test_go_gateway.py); this fake returns the
    # whole response as a single "chunk" and hands it back from the builder.
    def completion(**kw):
        return iter([resp]) if kw.get("stream") else resp

    def stream_chunk_builder(chunks, messages=None):
        chunks = list(chunks)
        return chunks[0] if chunks else None

    return types.SimpleNamespace(drop_params=False, completion=completion,
                                 stream_chunk_builder=stream_chunk_builder)


def _call(monkeypatch, message, finish_reason="length", api=GO):
    monkeypatch.setitem(sys.modules, "litellm", _fake_litellm(message, finish_reason))
    monkeypatch.setenv("OPENCODE_GO_API_KEY", "sk-go-test")
    monkeypatch.setenv("OPENROUTER_TOKEN", "sk-or-test")
    return runner.call_model(
        "qwen3.8-flash", "prompt", temperature=0.0, max_tokens=32000, timeout_s=10,
        max_retries=1, backoff_base_s=0.0, api=api)


# the three places a provider can put hidden thinking
THINKING_MESSAGES = {
    "reasoning_content attr (Go / litellm)":
        lambda: types.SimpleNamespace(content="", reasoning_content=THINKING),
    "reasoning attr (OpenRouter)":
        lambda: types.SimpleNamespace(content=None, reasoning=THINKING),
    "model_extra reasoning_content":
        lambda: types.SimpleNamespace(content="", model_extra={"reasoning_content": THINKING}),
}


@pytest.mark.parametrize("where", THINKING_MESSAGES)
@pytest.mark.parametrize("api", [GO, None], ids=["go", "openrouter"])
def test_thinking_only_reply_is_an_empty_completion(monkeypatch, where, api):
    call = _call(monkeypatch, THINKING_MESSAGES[where](), api=api)
    assert call.text == ""
    assert call.finish_reason == "length"
    assert call.error == "empty completion (finish_reason=length)"
    # report.py scores it as a FAIL, never drops it as an infra error
    assert not report.is_infra_error({"ok": False, "error": call.error})


def test_answer_is_kept_and_thinking_ignored(monkeypatch):
    msg = types.SimpleNamespace(content=ANSWER, reasoning_content=THINKING)
    call = _call(monkeypatch, msg, finish_reason="stop")
    assert call.text == ANSWER and call.error is None


def test_truncated_answer_is_still_graded(monkeypatch):
    # an answer cut off by the limit is the model's (partial) answer: keep it
    partial = "### FILE: x.sql\n```sql\nSELECT"
    call = _call(monkeypatch, types.SimpleNamespace(content=partial, reasoning_content=THINKING))
    assert call.text == partial and call.finish_reason == "length" and call.error is None
