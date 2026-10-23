"""Offline checks for the complete agent orchestration script."""

import run_agents

from fiel import agent_workflow
from fiel.claims import Claim
from fiel.sample_match import build_sample
from fiel.verifier import recompute


def test_pipeline_hands_verified_claim_through_every_role(monkeypatch):
    match = build_sample()
    calls = {"explainer": 0, "producer": 0, "personalizer": 0}

    def fake_explain(current_match, start, end, context, memory=None):
        calls["explainer"] += 1
        ids = [e.id for e in current_match.events_between(start, end)
               if e.team == "A" and e.type == "pass"]
        value = recompute("pass_accuracy_pct", "A", current_match, start, end)
        claim = Claim(
            claim=f"Team A completed {value:.1f}% of its passes.",
            metric="pass_accuracy_pct", value=round(value, 1), team="A",
            window_start=start, window_end=end, event_ids=ids,
        )
        return claim, [{"attempt": 1, "claim": claim.model_dump(),
                        "ok": True, "reasons": []}]

    def fake_produce(claims, max_items):
        calls["producer"] += 1
        assert len(claims) == 3 and max_items == 2
        return [{"claim": claims[1].model_dump(), "why_now": "A tactical change."}]

    def fake_personalize(claim, audience, language, current_match, memory=None):
        calls["personalizer"] += 1
        assert current_match is match
        return {"text": "Versão para o torcedor.", "audience": audience,
                "language": language, "verified": True}

    monkeypatch.setattr(agent_workflow, "explain_and_verify", fake_explain)
    monkeypatch.setattr(agent_workflow, "produce", fake_produce)
    monkeypatch.setattr(agent_workflow, "personalize", fake_personalize)

    result = run_agents.run_pipeline(match, "fan", "pt", max_items=2)

    assert calls == {"explainer": 3, "producer": 1, "personalizer": 1}
    assert result["approved_claims"] == 3
    assert result["on_air"][0]["personalization_verified"] is True
    assert result["on_air"][0]["receipt"]["metric"] == "pass_accuracy_pct"


def test_demo_windows_stay_inside_the_match():
    windows = run_agents.demo_windows(build_sample())
    assert len(windows) == 3
    assert all(0 <= start < end <= 90 for start, end, _ in windows)
