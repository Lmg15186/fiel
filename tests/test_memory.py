"""Offline tests for tactical memory and historical receipts."""

import json

from fiel.claims import Claim
from fiel.generator import MatchBuilder
from fiel.memory import build_memory, memory_for_match
from fiel.verifier import recompute, verify


def write_match(folder, match_id, home, away, seed):
    match = MatchBuilder(match_id, home, away, seed).build([])
    (folder / f"{match_id}.json").write_text(match.model_dump_json(), encoding="utf-8")
    (folder / f"{match_id}_truth.json").write_text(
        json.dumps({"home_code": home, "away_code": away}), encoding="utf-8")
    return match


def test_memory_aggregates_by_fictional_team_and_excludes_current(tmp_path):
    write_match(tmp_path, "m-101-T1-T2", "T1", "T2", 1)
    current = write_match(tmp_path, "m-102-T1-T3", "T1", "T3", 2)
    write_match(tmp_path, "m-103-T4-T1", "T4", "T1", 3)

    memory = build_memory(tmp_path, exclude_match_id=current.match_id)

    assert memory["T1"]["matches"] == 2
    assert current.match_id not in memory["T1"]["match_ids"]
    assert set(memory["T1"]["metrics"]) == {
        "possession_pct", "pass_accuracy_pct", "recovery_height", "pressure"
    }
    relevant = memory_for_match(current, memory)
    assert relevant["A"]["team_code"] == "T1"
    assert relevant["B"]["team_code"] == "T3"


def test_historical_claim_requires_a_correct_memory_receipt(tmp_path):
    past = write_match(tmp_path, "m-201-T1-T2", "T1", "T2", 4)
    current = write_match(tmp_path, "m-202-T1-T3", "T1", "T3", 5)
    memory = build_memory(tmp_path, exclude_match_id=current.match_id)
    ids = [e.id for e in current.events if e.team == "A" and e.type == "pass"]
    value = recompute("possession_pct", "A", current, 0, 90)
    baseline = memory["T1"]["metrics"]["possession_pct"]
    claim = Claim(
        claim="Team A had more possession than usual.",
        metric="possession_pct", value=round(value, 1), team="A",
        window_start=0, window_end=90, event_ids=ids,
        baseline_value=baseline, baseline_match_ids=[past.match_id],
    )

    assert verify(claim, current, memory).ok
    bad = claim.model_copy(update={"baseline_value": baseline + 20})
    verdict = verify(bad, current, memory)
    assert not verdict.ok and any("baseline mismatch" in reason for reason in verdict.reasons)


def test_historical_receipt_must_list_every_match_used(tmp_path):
    first = write_match(tmp_path, "m-301-T1-T2", "T1", "T2", 6)
    write_match(tmp_path, "m-302-T1-T4", "T1", "T4", 7)
    current = write_match(tmp_path, "m-303-T1-T3", "T1", "T3", 8)
    memory = build_memory(tmp_path, exclude_match_id=current.match_id)
    ids = [e.id for e in current.events if e.type == "recovery" and e.team == "A"]
    claim = Claim(
        claim="Team A recovered the ball higher than usual.",
        metric="recovery_height",
        value=round(recompute("recovery_height", "A", current, 0, 90), 1),
        team="A", window_start=0, window_end=90, event_ids=ids,
        baseline_value=memory["T1"]["metrics"]["recovery_height"],
        baseline_match_ids=[first.match_id],
    )

    verdict = verify(claim, current, memory)
    assert not verdict.ok
    assert any("receipt missing match ids" in reason for reason in verdict.reasons)
