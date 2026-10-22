"""
Offline tests for producer and personalizer: the model call is faked, so
these check the guard rails around it (bad indexes, drift) without a key.
Run with:  pytest -q
"""

from fiel import personalizer, producer
from fiel.claims import Claim
from fiel.sample_match import build_sample
from fiel.verifier import recompute

match = build_sample()


def good_claim():
    ids = [e.id for e in match.events_between(65, 75) if e.team == "B" and e.type == "recovery"]
    value = recompute("recovery_height", "B", match, 65, 75)
    return Claim(claim="After the substitution at 65', team B recovered the ball higher.",
                 metric="recovery_height", value=round(value, 1), team="B",
                 window_start=65, window_end=75, event_ids=ids)


def test_producer_ignores_invented_indexes(monkeypatch):
    claims = [good_claim(), good_claim()]
    monkeypatch.setattr(producer, "ask_json",
                        lambda s, u: {"rundown": [{"index": 1, "why_now": "x"},
                                                  {"index": 7, "why_now": "bad"},
                                                  {"index": 1, "why_now": "dup"}]})
    out = producer.produce(claims, max_items=3)
    assert len(out) == 1 and out[0]["why_now"] == "x"


def test_producer_empty_input():
    assert producer.produce([]) == []


def test_personalizer_keeps_text_when_rewrite_passes(monkeypatch):
    monkeypatch.setattr(personalizer, "ask_json",
                        lambda s, u: {"text": "Depois da substituição aos 65', o time B recuperou a bola mais alto."})
    out = personalizer.personalize(good_claim(), "fan", "pt", match)
    assert out["verified"] and out["text"].startswith("Depois")


def test_personalizer_falls_back_on_causal_drift(monkeypatch):
    monkeypatch.setattr(personalizer, "ask_json",
                        lambda s, u: {"text": "The substitution won the game for team B."})
    claim = good_claim()
    out = personalizer.personalize(claim, "fan", "en", match)
    assert not out["verified"] and out["text"] == claim.claim


def test_personalizer_rejects_bad_options():
    try:
        personalizer.personalize(good_claim(), "coach", "en")
        assert False, "should raise"
    except ValueError:
        pass
