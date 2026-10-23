from pathlib import Path

from fiel.agent_workflow import run_pipeline
from fiel.claims import Claim, Match


MATCH = Match.model_validate_json(
    Path("data/m-003-T4-T3.json").read_text(encoding="utf-8")
)


def test_agent_framework_runs_all_three_stages(monkeypatch):
    claim = Claim(
        claim="Team A completed 80.0% of its passes from minute 0 to 15.",
        metric="pass_accuracy_pct",
        value=80.0,
        team="A",
        window_start=0,
        window_end=15,
        event_ids=[event.id for event in MATCH.events_between(0, 15)
                   if event.team == "A" and event.type == "pass"],
        causal=False,
        confidence=0.9,
    )

    monkeypatch.setattr(
        "fiel.agent_workflow.explain_and_verify",
        lambda *args, **kwargs: (claim, [{"attempt": 1, "ok": True}]),
    )
    monkeypatch.setattr(
        "fiel.agent_workflow.produce",
        lambda claims, max_items: [{"claim": claims[0].model_dump(), "why_now": "Clear."}],
    )
    monkeypatch.setattr(
        "fiel.agent_workflow.personalize",
        lambda *args, **kwargs: {
            "text": claim.claim,
            "audience": "fan",
            "language": "pt",
            "verified": True,
        },
    )

    result = run_pipeline(MATCH)

    assert result["orchestration"]["framework"] == "Microsoft Agent Framework"
    assert result["windows_analysed"] == 3
    assert result["approved_claims"] == 3
    assert result["on_air"][0]["personalization_verified"] is True
