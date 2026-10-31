"""tests/test_go_gateway.py — non-OpenRouter gateways (OpenCode Go).

Models with `api: <name>` in models.yaml are called through that gateway
instead of OpenRouter: no provider pinning, no usage.cost request, the gateway
id is recorded as the provider, and cost comes from the pricing.py table (Go's
list prices count against the subscription quota; it does not bill per call).
Three API dialects are wired up: `family: chat` (OpenAI chat completions —
GLM, DeepSeek, Kimi, ...), `family: responses` (OpenAI Responses API — Go
serves GPT Luna, Grok and Muse Spark only at `/v1/responses`), and
`family: messages` (Anthropic messages API — Go's Qwen3.x / MiniMax at
`/v1/messages`). A model-level `family:` override lets one gateway serve a
mixed-dialect pair while keeping a single provider string.

All offline: litellm is replaced by a fake.
"""

from __future__ import annotations

import json
import sys
import types

import pytest

import common
import pricing
import report
import runner
from common import load_config

PAIR = "glm-5.2-vs-5.3"


# --------------------------------------------------------------------------- #
# config                                                                       #
# --------------------------------------------------------------------------- #
GO_YAML = """
pairs:
  - id: g
    current: {id: glm-5.2, name: GLM-5.2, api: opencode-go, params: {reasoning_effort: low}}
    target:  {id: glm-5.3, name: GLM-5.3, api: opencode-go, params: {reasoning_effort: low}}
  - id: o
    current: {id: x/a1, name: A1}
    target:  {id: x/a2, name: A2}
apis:
  opencode-go:
    base_url: https://opencode.ai/inference/go/v1
    api_key_env: OPENCODE_GO_API_KEY
    family: chat
"""


def _cfg(tmp_path, yaml_text=GO_YAML):
    p = tmp_path / "models.yaml"
    p.write_text(yaml_text)
    return load_config(p)


def test_config_parses_apis_and_model_api(tmp_path):
    cfg = _cfg(tmp_path)
    pair = cfg.get_pair("g")
    api = cfg.api_for(pair.target)
    assert api is not None
    assert api.id == "opencode-go"
    assert api.base_url == "https://opencode.ai/inference/go/v1"
    assert api.family == "chat"
    assert pair.target.params == {"reasoning_effort": "low"}
    # models without `api:` stay on the OpenRouter route
    assert cfg.api_for(cfg.get_pair("o").target) is None


def test_dangling_api_reference_fails_loudly(tmp_path):
    cfg = _cfg(tmp_path, GO_YAML.replace("api: opencode-go,", "api: nope,"))
    with pytest.raises(KeyError, match="unknown api 'nope'"):
        cfg.api_for(cfg.get_pair("g").target)


def test_repo_go_pairs_resolve_and_are_priced():
    """Every keyed-gateway (`api:`) model in the repo models.yaml must resolve
    its gateway, and every model billed from the price table (i.e. not on the
    claude-code family, whose cost is the CLI's own estimate —
    tests/test_claude_code_gateway.py) must have a real pricing row, not the
    conservative DEFAULT_PRICE fallback. Cross-gateway pairs legitimately mix
    a claude-code model with an OpenCode Go one (tests/test_cross_gateway.py)."""
    cfg = load_config()
    go_models = [(p, m) for p in cfg.pairs for m in (p.current, p.target)
                 if m.api and cfg.api_for(m).family != "claude-code"]
    assert go_models, "expected at least one OpenCode Go model in models.yaml"
    for pair, m in go_models:
        api = cfg.api_for(m)
        assert api is not None and api.base_url and api.api_key_env, (pair.id, m.id)
        assert pricing.get_price(m.id) is not pricing.DEFAULT_PRICE, m.id


# --------------------------------------------------------------------------- #
# the call                                                                     #
# --------------------------------------------------------------------------- #
class _FakeLitellm(types.SimpleNamespace):
    def __init__(self):
        super().__init__(drop_params=False, calls=[], builder_calls=[])
        # Sentinel chunks: the production code must hand exactly these to
        # stream_chunk_builder (they stand in for litellm's stream chunks).
        self.chunks = ["chunk-1", "chunk-2"]

    def _full_response(self):
        msg = types.SimpleNamespace(content="### FILE: x.sql\n```sql\nSELECT 1;\n```\n")
        usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=msg, finish_reason="stop")],
            usage=usage)

    def completion(self, **kw):
        self.calls.append(kw)
        if kw.get("stream"):
            return iter(self.chunks)
        return self._full_response()

    def stream_chunk_builder(self, chunks, messages=None):
        chunks = list(chunks)
        self.builder_calls.append((chunks, messages))
        if not chunks:
            return None  # the real builder returns None for an empty stream
        return self._full_response()


@pytest.fixture
def fake_litellm(monkeypatch):
    fake = _FakeLitellm()
    monkeypatch.setitem(sys.modules, "litellm", fake)
    monkeypatch.setenv("OPENCODE_GO_API_KEY", "sk-go-test")
    monkeypatch.delenv("OPENROUTER_TOKEN", raising=False)
    return fake


def test_go_call_uses_openai_compatible_route(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261014T000000Z")

    sent = fake_litellm.calls[0]
    assert sent["model"] == "openai/glm-5.3"
    assert sent["api_base"] == "https://opencode.ai/inference/go/v1"
    assert sent["api_key"] == "sk-go-test"
    # Go asks clients to identify themselves and send a stable session id
    assert sent["extra_headers"]["User-Agent"]
    assert sent["extra_headers"]["x-opencode-session"] == "20261014T000000Z"
    # OpenRouter extensions are not sent to other gateways
    assert "extra_body" not in sent
    # per-model params from models.yaml are merged into the call (GLM on Go is
    # thinking-only; reasoning_effort: low keeps it from thinking away the
    # whole output budget)
    assert sent["reasoning_effort"] == "low"

    assert res.ok and res.provider == "opencode-go"
    assert res.provider_requested is None
    assert res.billed_cost_usd is None
    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())
    assert saved["provider"] == "opencode-go" and saved["ok"] is True


def test_go_chat_call_streams_and_reassembles(tmp_path, monkeypatch, fake_litellm):
    """Gateway calls must use streaming transport. Go's non-streaming path can
    accept a request and never send a byte (first seen 2026-10-26: Kimi K3 on
    r1b — big prompt + max_tokens=128000; the same request streams fine, first
    chunk in under 2 s). Streaming also turns the read timeout into a
    between-chunks timeout, so a healthy long call survives while a stalled
    one fails at timeout_s instead of hanging forever."""
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261027T000000Z")

    sent = fake_litellm.calls[0]
    assert sent["stream"] is True
    assert sent["stream_options"] == {"include_usage": True}
    # the chunks are reassembled into one response by litellm's builder
    # (messages are passed so it can count prompt tokens if usage is absent)
    assert fake_litellm.builder_calls
    chunks, messages = fake_litellm.builder_calls[0]
    assert chunks == fake_litellm.chunks
    assert messages[0]["role"] == "system"
    assert res.ok and res.output_tokens == 50


def test_go_stream_records_thinking_time_and_effort(tmp_path, monkeypatch, fake_litellm):
    def chunk(*, reasoning="", content=""):
        delta = types.SimpleNamespace(
            reasoning_content=reasoning or None, content=content or None,
            thinking_blocks=None, reasoning_items=None,
            model_dump=lambda: {"reasoning_content": reasoning or None, "content": content or None})
        return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=delta)])

    fake_litellm.chunks = [
        chunk(reasoning="plan"), chunk(reasoning=" more"),
        chunk(content="answer"), types.SimpleNamespace(choices=[]),
    ]
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    times = iter((1.0, 3.0, 7.0, 8.0, 9.0))
    monkeypatch.setattr(runner.time, "monotonic", lambda: next(times))
    cfg = _cfg(tmp_path, GO_YAML + "\ndefaults:\n  thinking_time: true\n")
    pair = cfg.get_pair("g")
    res = runner.run_case(cfg, "g", "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261030T000000Z")

    assert res.ok and res.thinking_time_s == pytest.approx(6.0)
    assert res.reasoning_requested == {"effort": "low"}
    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())
    assert saved["thinking_time_s"] == pytest.approx(6.0)
    assert saved["reasoning_requested"] == {"effort": "low"}


def test_go_stream_records_execution_time(tmp_path, monkeypatch, fake_litellm):
    """Execution time is the streamed visible-answer phase, measured — never
    derived as latency minus thinking (that difference contains startup and
    network overhead)."""
    def chunk(*, reasoning="", content=""):
        delta = types.SimpleNamespace(reasoning_content=reasoning or None,
                                      content=content or None,
                                      thinking_blocks=None, reasoning_items=None)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=delta)])

    fake_litellm.chunks = [
        chunk(reasoning="plan"), chunk(reasoning=" more"),
        chunk(content="answer"), types.SimpleNamespace(choices=[]),
    ]
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    times = iter((1.0, 3.0, 7.0, 8.0, 9.0))
    monkeypatch.setattr(runner.time, "monotonic", lambda: next(times))
    cfg = _cfg(tmp_path, GO_YAML + "\ndefaults:\n  thinking_time: true\n")
    pair = cfg.get_pair("g")
    res = runner.run_case(cfg, "g", "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261030T000000Z")

    assert res.thinking_time_s == pytest.approx(6.0)
    assert res.execution_time_s == pytest.approx(2.0)
    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())
    assert saved["execution_time_s"] == pytest.approx(2.0)


def _phase_chunk(*, reasoning="", content=""):
    delta = types.SimpleNamespace(reasoning_content=reasoning or None,
                                  content=content or None,
                                  thinking_blocks=None, reasoning_items=None)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=delta)])


def _run_instrumented(tmp_path, monkeypatch, fake_litellm, chunks, times):
    fake_litellm.chunks = chunks
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    clock = iter(times)
    monkeypatch.setattr(runner.time, "monotonic", lambda: next(clock))
    cfg = _cfg(tmp_path, GO_YAML + "\ndefaults:\n  thinking_time: true\n")
    pair = cfg.get_pair("g")
    return runner.run_case(cfg, "g", "r3_oracle_to_postgres", pair.target, "target",
                           run_id="20261030T000000Z")


def test_go_thinking_only_stream_spent_zero_seconds_answering(tmp_path, monkeypatch,
                                                              fake_litellm):
    """Inside an observed stream an absent phase is a measured 0 s."""
    res = _run_instrumented(tmp_path, monkeypatch, fake_litellm,
                            [_phase_chunk(reasoning="plan"), _phase_chunk(reasoning="...")],
                            (1.0, 3.0, 9.0))
    assert res.thinking_time_s == pytest.approx(8.0)
    assert res.execution_time_s == 0.0


def test_go_answer_without_thinking_records_zero_thinking(tmp_path, monkeypatch, fake_litellm):
    """A model that answers straight away (common at low effort) thought for
    0 s — a measurement, not a missing value."""
    res = _run_instrumented(tmp_path, monkeypatch, fake_litellm,
                            [_phase_chunk(content="a"), _phase_chunk(content="b")],
                            (1.0, 2.0, 5.0))
    assert res.thinking_time_s == 0.0
    assert res.execution_time_s == pytest.approx(4.0)


def test_go_stream_without_classified_events_is_unmeasured(tmp_path, monkeypatch,
                                                           fake_litellm):
    """Only usage chunks, no reasoning or content: no measurement at all."""
    res = _run_instrumented(tmp_path, monkeypatch, fake_litellm,
                            [types.SimpleNamespace(choices=[])], (1.0, 2.0))
    assert res.thinking_time_s is None and res.execution_time_s is None


def test_observe_stream_chunk_handles_interleaved_phases():
    """Reasoning resumed after an answer chunk reopens the thinking phase."""
    timer = runner._ThinkingTimer()
    timer.reasoning(1.0)   # think 1→4
    timer.answer(4.0)      # answer 4→6
    timer.reasoning(6.0)   # think 6→7
    timer.answer(7.0)      # answer 7→9
    thinking, execution = timer.finish(9.0)
    assert thinking == pytest.approx(4.0)
    assert execution == pytest.approx(4.0)


def test_observe_stream_chunk_probes_attr_deltas_without_serialization():
    """Pydantic-style deltas are probed with getattr, not a per-token
    model_dump() serialization in the hot streaming loop."""
    class _Delta:
        reasoning_content = "x"
        content = None

        def model_dump(self):
            raise AssertionError("model_dump must not be called per chunk")

    class _Answer:
        reasoning_content = None
        content = "hi"

        def model_dump(self):
            raise AssertionError("model_dump must not be called per chunk")

    timer = runner._ThinkingTimer()
    runner._observe_stream_chunk(
        types.SimpleNamespace(choices=[types.SimpleNamespace(delta=_Delta())]), timer, 1.0)
    runner._observe_stream_chunk(
        types.SimpleNamespace(choices=[types.SimpleNamespace(delta=_Answer())]), timer, 3.0)
    thinking, execution = timer.finish(4.0)
    assert thinking == pytest.approx(2.0)
    assert execution == pytest.approx(1.0)


def test_go_call_sends_no_client_retries(tmp_path, monkeypatch, fake_litellm):
    """litellm's underlying OpenAI client retries timeouts twice by default
    (3 hidden attempts per call, measured 2026-10-26: a 45 s timeout raised
    after 139.8 s). The runner's own retry loop is the only retry authority,
    so every litellm call must pass max_retries=0."""
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runner.run_case(cfg, PAIR, "r3_oracle_to_postgres", pair.target, "target",
                    run_id="20261027T000000Z")
    assert fake_litellm.calls[0]["max_retries"] == 0


def test_go_empty_stream_is_a_clean_error(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    fake_litellm.chunks = []
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261027T000000Z")
    assert not res.ok and "empty stream" in (res.error or "")


def test_openrouter_route_stays_non_streaming_without_client_retries(
        tmp_path, monkeypatch, fake_litellm):
    """OpenRouter billing (usage.cost) rides on the non-streaming response, so
    the OpenRouter route keeps its transport — only the hidden client retries
    are turned off there too."""
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    monkeypatch.setenv("OPENROUTER_TOKEN", "sk-or-v1-test")
    cfg = _cfg(tmp_path)
    pair = cfg.get_pair("o")
    res = runner.run_case(cfg, "o", "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261027T000000Z")
    sent = fake_litellm.calls[0]
    assert "stream" not in sent
    assert sent["max_retries"] == 0
    assert res.ok
    assert not fake_litellm.builder_calls


def test_go_call_without_key_is_clean_infra_error(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    monkeypatch.delenv("OPENCODE_GO_API_KEY")
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261014T000000Z")
    assert not res.ok and "OPENCODE_GO_API_KEY not set" in (res.error or "")
    assert not fake_litellm.calls                       # never hit the network
    assert report.is_infra_error({"ok": res.ok, "error": res.error})


def test_go_dry_run_needs_no_key(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    monkeypatch.delenv("OPENCODE_GO_API_KEY")
    cfg = load_config()
    results = runner.run_pair(cfg, PAIR, dry_run=True, run_id="20261014T000000Z")
    assert results and all(r.ok for r in results)       # payload shapes built fine
    assert not fake_litellm.calls                       # never hit the network
    assert not list(tmp_path.rglob("*.json"))           # a dry run writes nothing


def test_deepseek_style_cache_tokens_are_counted():
    resp = types.SimpleNamespace(usage={
        "prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150,
        "prompt_cache_hit_tokens": 80,
    })
    i, o, cr, cw, tot = runner._extract_usage(resp)
    assert (i, o, cr, cw, tot) == (100, 50, 80, 0, 150)


# --------------------------------------------------------------------------- #
# family: responses (GPT Luna / Grok / Muse Spark on Go)                       #
# --------------------------------------------------------------------------- #
RESPONSES_PAIR = "gpt-5.6-luna-vs-6-luna"


class _FakeResponsesLitellm(types.SimpleNamespace):
    """Fakes litellm's Responses API entry point (litellm.responses)."""

    def __init__(self):
        super().__init__(drop_params=False, calls=[])

    def responses(self, **kw):
        self.calls.append(kw)
        payload = {
            "status": "completed",
            "output": [
                {"type": "reasoning"},   # hidden thinking: never graded
                {"type": "message", "content": [
                    {"type": "output_text",
                     "text": "### FILE: x.sql\n```sql\nSELECT 1;\n```\n"},
                ]},
            ],
            "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150,
                      "input_tokens_details": {"cached_tokens": 40},
                      "output_tokens_details": {"reasoning_tokens": 20}},
        }
        # The real ResponsesAPIResponse exposes .usage as an attribute AND
        # model_dump() for the whole payload; _extract_usage reads the former,
        # _responses_text/_responses_finish_reason use the latter.
        return types.SimpleNamespace(usage=payload["usage"], model_dump=lambda: payload)


@pytest.fixture
def fake_responses_litellm(monkeypatch):
    fake = _FakeResponsesLitellm()
    monkeypatch.setitem(sys.modules, "litellm", fake)
    monkeypatch.setenv("OPENCODE_GO_API_KEY", "sk-go-test")
    monkeypatch.delenv("OPENROUTER_TOKEN", raising=False)
    return fake


def test_repo_responses_gateway_configured():
    cfg = load_config()
    api = cfg.apis["opencode-go-responses"]
    assert api.family == "responses"
    assert api.base_url == "https://opencode.ai/inference/go/v1"
    assert api.api_key_env == "OPENCODE_GO_API_KEY"


def test_go_responses_call_uses_responses_api(tmp_path, monkeypatch, fake_responses_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    pair = cfg.get_pair(RESPONSES_PAIR)
    res = runner.run_case(cfg, RESPONSES_PAIR, "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261015T000000Z")

    sent = fake_responses_litellm.calls[0]
    assert sent["model"] == "openai/gpt-6-luna"
    assert sent["api_base"] == "https://opencode.ai/inference/go/v1"
    assert sent["api_key"] == "sk-go-test"
    # Responses API knobs: max_output_tokens (thinking included), input=
    assert sent["max_output_tokens"] == cfg.max_tokens_for(pair.target.id)
    assert "max_tokens" not in sent
    assert sent["input"][0]["role"] == "system"
    assert sent["extra_headers"]["x-opencode-session"] == "20261015T000000Z"
    # OpenRouter extensions are not sent to other gateways
    assert "extra_body" not in sent

    assert res.ok and res.provider == "opencode-go-responses"
    assert res.finish_reason == "stop"
    assert "### FILE: x.sql" in res.output_text
    assert (res.input_tokens, res.output_tokens) == (100, 50)
    assert res.cache_read_tokens == 40 and res.reasoning_tokens == 20
    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())
    assert saved["provider"] == "opencode-go-responses" and saved["ok"] is True


def test_go_responses_call_sends_no_client_retries(tmp_path, monkeypatch,
                                                   fake_responses_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    pair = cfg.get_pair(RESPONSES_PAIR)
    runner.run_case(cfg, RESPONSES_PAIR, "r3_oracle_to_postgres", pair.target, "target",
                    run_id="20261027T000000Z")
    assert fake_responses_litellm.calls[0]["max_retries"] == 0


def test_responses_usage_and_reasoning_extracted():
    resp = types.SimpleNamespace(usage={
        "input_tokens": 100, "output_tokens": 50, "total_tokens": 150,
        "input_tokens_details": {"cached_tokens": 40},
        "output_tokens_details": {"reasoning_tokens": 20},
    })
    assert runner._extract_usage(resp) == (100, 50, 40, 0, 150)
    assert runner._extract_reasoning_tokens(resp) == 20


def test_responses_text_skips_reasoning_items():
    resp = {"output": [
        {"type": "reasoning", "summary": [{"type": "summary_text", "text": "shh"}]},
        {"type": "message", "content": [{"type": "output_text", "text": "answer"}]},
    ]}
    assert runner._responses_text(resp) == "answer"


def test_responses_finish_reason_maps_incomplete():
    resp = {"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}}
    assert runner._responses_finish_reason(resp) == "max_output_tokens"
    assert runner._responses_finish_reason({"status": "completed"}) == "stop"


# --------------------------------------------------------------------------- #
# family: messages (Qwen3.x / MiniMax on Go — Anthropic messages API)          #
# --------------------------------------------------------------------------- #
MESSAGES_PAIR = "qwen3.8-flash-vs-glm-5.3-flash"


def test_model_family_override_keeps_gateway(tmp_path):
    """A model-level `family:` overrides the gateway dialect but not its id —
    both models of a mixed pair keep the same provider string."""
    yaml_text = """
pairs:
  - id: q
    current: {id: qwen3.8-flash, name: Q, api: opencode-go, family: messages}
    target:  {id: glm-5.3-flash, name: G, api: opencode-go}
apis:
  opencode-go:
    base_url: https://opencode.ai/inference/go/v1
    api_key_env: OPENCODE_GO_API_KEY
    family: chat
"""
    cfg = _cfg(tmp_path, yaml_text)
    pair = cfg.get_pair("q")
    cur, tgt = cfg.api_for(pair.current), cfg.api_for(pair.target)
    assert cur is not None and cur.family == "messages" and cur.id == "opencode-go"
    assert tgt is not None and tgt.family == "chat" and tgt.id == "opencode-go"


def test_go_messages_call_uses_anthropic_route(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    pair = cfg.get_pair(MESSAGES_PAIR)
    res = runner.run_case(cfg, MESSAGES_PAIR, "r3_oracle_to_postgres", pair.current, "current",
                          run_id="20261015T000000Z")

    sent = fake_litellm.calls[0]
    # litellm `anthropic/` posts to {api_base}/messages and normalizes the reply
    assert sent["model"] == "anthropic/qwen3.8-flash"
    # the Anthropic SDK appends /v1/messages itself — the gateway's /v1 is trimmed
    assert sent["api_base"] == "https://opencode.ai/inference/go"
    assert sent["api_key"] == "sk-go-test"
    assert sent["extra_headers"]["x-opencode-session"] == "20261015T000000Z"
    assert "extra_body" not in sent
    # no per-model params for Qwen: Go's messages route ignores thinking
    # controls (probed 2026-10-15), so nothing is merged into the call
    assert "thinking" not in sent and "reasoning_effort" not in sent

    assert res.ok and res.provider == "opencode-go"   # same provider string as GLM
    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())
    assert saved["provider"] == "opencode-go" and saved["ok"] is True


def test_glm_flash_stays_on_chat_route(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    pair = cfg.get_pair(MESSAGES_PAIR)
    res = runner.run_case(cfg, MESSAGES_PAIR, "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261015T000000Z")
    sent = fake_litellm.calls[0]
    assert sent["model"] == "openai/glm-5.3-flash"
    # GLM-5.x is thinking-only on Go: cap hidden thinking so it answers
    assert sent["reasoning_effort"] == "low"
    assert res.ok and res.provider == "opencode-go"


# --------------------------------------------------------------------------- #
# report                                                                       #
# --------------------------------------------------------------------------- #
def _rec(role, slug, ok=True, latency=10.0):
    return {"case_id": "r3_oracle_to_postgres", "role": role, "model_slug": slug,
            "model_name": slug, "ok": ok, "input_tokens": 1000, "output_tokens": 500,
            "cache_read_tokens": 0, "cache_write_tokens": 0, "total_tokens": 1500,
            "latency_s": latency, "output_text": "", "billed_cost_usd": None,
            "provider": "opencode-go", "error": None if ok else "empty completion"}


def test_report_scores_go_pair_like_any_other():
    """Same metrics, same methodology: pass rates, time, cost (price table),
    capped components, overall score — only the cost source line differs."""
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runs = [_rec("current", pair.current.id), _rec("target", pair.target.id, latency=8.0)]
    aggs = report.aggregate(runs, score=False)
    md = report.render_pair(cfg, PAIR, aggs, runs, score=False)

    expected = pricing.cost_usd("glm-5.3", 1000, 500, 0, 0)
    assert aggs[(pair.target.id, "target")].cost_usd == pytest.approx(expected)
    assert "price table (pricing.py)" in md
    assert "opencode-go" in md and "different providers" not in md
    # both models pass -> an overall score is produced with the standard weights
    assert "Overall score (current = 100 baseline)" in md
    ov = report.overall_score(aggs[(pair.current.id, "current")],
                              aggs[(pair.target.id, "target")])
    assert ov is not None and ov.quality == 100.0 and ov.time == pytest.approx(125.0)
