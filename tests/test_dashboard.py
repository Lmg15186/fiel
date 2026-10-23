from dashboard import (latest_verified_insight, load_agent_run, load_match,
                       load_truth, verification_scene)


MATCH_ID = "m-003-T4-T3"


def test_dashboard_live_insight_is_verifiable():
    match = load_match(MATCH_ID)
    claim, verdict = latest_verified_insight(match, minute=75)

    assert claim.event_ids
    assert verdict.ok
    assert verdict.recomputed_value is not None


def test_dashboard_staged_scene_rejects_then_accepts():
    match = load_match(MATCH_ID)
    truth = load_truth(MATCH_ID)
    _, rejected, corrected, accepted = verification_scene(match, truth)

    assert not rejected.ok
    assert any("causal claim" in reason for reason in rejected.reasons)
    assert accepted.ok
    assert not corrected.causal


def test_cached_agent_run_has_verified_historical_receipts():
    result = load_agent_run(MATCH_ID)
    assert result["approved_claims"] >= 1
    assert result["on_air"]
    assert all(item["personalization_verified"] for item in result["on_air"])
    assert any(item["receipt"]["baseline_match_ids"] for item in result["on_air"])
