"""
Tests for the generator. Run with:  pytest -q
Checks that the output follows the schema and that each planted story is
really visible in the numbers (otherwise the Explainer could never find it).
"""

import random

from fiel.generator import MatchBuilder, STORY_KINDS
from fiel.verifier import recompute


def build(seed, stories):
    b = MatchBuilder(f"t-{seed}", "T1", "T2", seed=seed)
    return b.build(stories), b.planted


def test_schema_and_size():
    match, _ = build(1, [])
    assert len(match.events) > 500
    assert all(e.team in ("A", "B") for e in match.events)
    ids = [e.id for e in match.events]
    assert len(ids) == len(set(ids)), "event ids must be unique"


def test_recover_higher_story_is_measurable():
    match, planted = build(2, ["recover_higher_after_sub"])
    story = planted[0]
    before = recompute("recovery_height", story["team"], match, *story["before"])
    after = recompute("recovery_height", story["team"], match, *story["after"])
    assert before is not None and after is not None
    assert after - before > 10, (before, after)


def test_possession_drop_story_is_measurable():
    match, planted = build(3, ["possession_drop_after_goal"])
    story = planted[0]
    before = recompute("possession_pct", story["team"], match, *story["before"])
    after = recompute("possession_pct", story["team"], match, *story["after"])
    assert before is not None and after is not None
    assert after - before > 10, (before, after)


def test_all_story_kinds_build():
    rng = random.Random(0)
    for kind in STORY_KINDS:
        match, planted = build(rng.randint(0, 999), [kind])
        assert planted[0]["kind"] == kind
