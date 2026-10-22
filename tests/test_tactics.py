"""Tests for the tactics engine. Run with:  pytest -q"""

from fiel.claims import Event
from fiel.generator import MatchBuilder
from fiel.tactics import pressure_windows, win_probability, xg, xg_totals


def shot(x, y, outcome="fail"):
    return Event(id="s1", minute=10, type="shot", team="A", player="A9",
                 x=x, y=y, outcome=outcome)


def test_xg_closer_is_higher():
    assert xg(shot(95, 50)) > xg(shot(80, 50)) > xg(shot(60, 50))


def test_xg_central_beats_wide():
    assert xg(shot(90, 50)) > xg(shot(90, 15))


def test_xg_on_target_is_higher():
    assert xg(shot(90, 50, "success")) > xg(shot(90, 50, "fail"))


def test_xg_bounds():
    assert 0.0 < xg(shot(99, 50, "success")) <= 0.95
    assert xg(Event(id="p", minute=1, type="pass", team="A", player="A1", x=50, y=50)) == 0.0


def test_win_probability_sums_to_one_and_moves_with_score():
    match = MatchBuilder("t", "T1", "T2", seed=5).build([])
    p0 = win_probability(match, 0, runs=500)
    assert abs(sum(p0.values()) - 1.0) < 0.01
    goals_a = sum(1 for e in match.events if e.type == "goal" and e.team == "A")
    goals_b = sum(1 for e in match.events if e.type == "goal" and e.team == "B")
    p85 = win_probability(match, 85, runs=500)
    if goals_a > goals_b:
        assert p85["A"] > p85["B"]
    elif goals_b > goals_a:
        assert p85["B"] > p85["A"]
    else:
        assert p85["draw"] > 0.5


def test_pressure_rows_cover_match():
    match = MatchBuilder("t", "T1", "T2", seed=6).build([])
    rows = pressure_windows(match)
    assert rows[0]["start"] == 0 and rows[-1]["end"] >= 90
    assert all(r["press_A"] >= 0 and r["press_B"] >= 0 for r in rows)
    avg_a = sum(r["press_A"] for r in rows) / len(rows)
    avg_b = sum(r["press_B"] for r in rows) / len(rows)
    assert avg_a > avg_b


def test_xg_totals_are_positive():
    match = MatchBuilder("t", "T3", "T4", seed=7).build([])
    totals = xg_totals(match)
    assert totals["A"] > 0 and totals["B"] > 0
