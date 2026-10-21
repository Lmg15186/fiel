"""
Tests for the verifier. Run with:  pytest -q
No model call here, so they run offline in under a second.
"""

from fiel.claims import Claim
from fiel.sample_match import build_sample
from fiel.verifier import recompute, verify

match = build_sample()


def ids_in(team, etype, start, end):
    return [e.id for e in match.events_between(start, end)
            if e.team == team and e.type == etype]


def test_true_claim_passes():
    ids = ids_in("B", "recovery", 65, 75)
    value = recompute("recovery_height", "B", match, 65, 75)
    claim = Claim(
        claim="After the substitution at 65', team B recovered the ball higher up the pitch.",
        metric="recovery_height", value=round(value, 1), team="B",
        window_start=65, window_end=75, event_ids=ids,
    )
    verdict = verify(claim, match)
    assert verdict.ok, verdict.reasons


def test_wrong_value_is_rejected():
    ids = ids_in("B", "recovery", 65, 75)
    claim = Claim(
        claim="Team B recovered the ball at an average height of 90.",
        metric="recovery_height", value=90.0, team="B",
        window_start=65, window_end=75, event_ids=ids,
    )
    verdict = verify(claim, match)
    assert not verdict.ok
    assert any("value mismatch" in r for r in verdict.reasons)


def test_unknown_event_is_rejected():
    claim = Claim(
        claim="Team A had two shots.",
        metric="shots", value=2, team="A",
        window_start=0, window_end=20, event_ids=["e9999"],
    )
    verdict = verify(claim, match)
    assert not verdict.ok
    assert any("not in match" in r for r in verdict.reasons)


def test_causal_language_without_evidence_is_rejected():
    ids = ids_in("B", "recovery", 65, 70)[:2]
    value = recompute("recovery_height", "B", match, 65, 70)
    claim = Claim(
        claim="The substitution at 65' won the game for team B.",
        metric="recovery_height", value=round(value, 1), team="B",
        window_start=65, window_end=70, event_ids=ids, causal=True,
    )
    verdict = verify(claim, match)
    assert not verdict.ok
    assert any("causal" in r for r in verdict.reasons)


def test_event_outside_window_is_rejected():
    inside = ids_in("B", "recovery", 65, 75)
    outside = ids_in("B", "recovery", 10, 20)[:1]
    value = recompute("recovery_height", "B", match, 65, 75)
    claim = Claim(
        claim="Team B recovered the ball higher after 65'.",
        metric="recovery_height", value=round(value, 1), team="B",
        window_start=65, window_end=75, event_ids=inside + outside,
    )
    verdict = verify(claim, match)
    assert not verdict.ok
    assert any("outside the window" in r for r in verdict.reasons)
