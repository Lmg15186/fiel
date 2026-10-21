"""
verifier.py - checks a Claim against the match events. No AI involved.

A claim passes only if:
  1. every event id it cites exists in the match;
  2. the window makes sense and the cited events sit inside it;
  3. recomputing the metric from the events gives (about) the same value;
  4. the sentence does not state a cause unless the Explainer marked it
     causal AND the evidence is strong enough (see CAUSAL_MIN_EVENTS).

Every failure comes back with a plain-English reason, so the editor agent
can rewrite the sentence instead of guessing.
"""

import re

from fiel.claims import Claim, Match, Verdict

# Relative tolerance when comparing the model's value with ours.
TOLERANCE = 0.05
# A causal sentence needs at least this many cited events behind it.
CAUSAL_MIN_EVENTS = 6

# Words that turn a description into a cause. Portuguese and English.
CAUSAL_PATTERNS = [
    r"\bbecause\b", r"\bdue to\b", r"\bcaused\b", r"\bwon the game\b",
    r"\bdecided\b", r"\bthanks to\b", r"\bled to\b",
    r"\bpor causa\b", r"\bgraças a\b", r"\bganhou o jogo\b", r"\bdecidiu\b",
    r"\blevou a\b", r"\bprovocou\b",
]


def _has_causal_language(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in CAUSAL_PATTERNS)


# --- metric recomputation ---------------------------------------------------

def recompute(metric: str, team: str, match: Match, start: int, end: int):
    """Compute the metric from raw events. Returns None when undefined."""
    window = match.events_between(start, end)
    mine = [e for e in window if e.team == team]

    if metric == "possession_pct":
        passes_all = [e for e in window if e.type == "pass"]
        passes_mine = [e for e in passes_all if e.team == team]
        if not passes_all:
            return None
        return 100.0 * len(passes_mine) / len(passes_all)

    if metric == "recovery_height":
        recs = [e for e in mine if e.type == "recovery"]
        if not recs:
            return None
        return sum(e.x for e in recs) / len(recs)

    if metric == "shots":
        return float(sum(1 for e in mine if e.type == "shot"))

    if metric == "shots_on_target":
        return float(sum(1 for e in mine if e.type == "shot" and e.outcome == "success"))

    if metric == "goals":
        return float(sum(1 for e in mine if e.type == "goal"))

    if metric == "pass_accuracy_pct":
        passes = [e for e in mine if e.type == "pass"]
        if not passes:
            return None
        good = [e for e in passes if e.outcome == "success"]
        return 100.0 * len(good) / len(passes)

    return None


def _close(a: float, b: float) -> bool:
    """True when a and b agree within TOLERANCE (absolute 0.5 for small numbers)."""
    if abs(a - b) <= 0.5:
        return True
    return abs(a - b) <= TOLERANCE * max(abs(a), abs(b))


# --- the verifier -----------------------------------------------------------

def verify(claim: Claim, match: Match) -> Verdict:
    reasons: list[str] = []

    # 1. cited events must exist
    known = match.event_ids()
    missing = [eid for eid in claim.event_ids if eid not in known]
    if missing:
        reasons.append(f"event ids not in match: {', '.join(missing)}")

    # 2. window sanity and cited events inside the window
    if claim.window_end <= claim.window_start:
        reasons.append("window_end must be after window_start")
    else:
        inside = {e.id for e in match.events_between(claim.window_start, claim.window_end)}
        outside = [eid for eid in claim.event_ids if eid in known and eid not in inside]
        if outside:
            reasons.append(f"cited events outside the window: {', '.join(outside)}")

    # 3. recompute the metric
    recomputed = None
    if not reasons:
        recomputed = recompute(
            claim.metric, claim.team, match, claim.window_start, claim.window_end
        )
        if recomputed is None:
            reasons.append(f"metric {claim.metric} is undefined in this window")
        elif not _close(recomputed, claim.value):
            reasons.append(
                f"value mismatch: claim says {claim.value}, events give {recomputed:.1f}"
            )

    # 4. causal language needs evidence
    if _has_causal_language(claim.claim):
        if not claim.causal:
            reasons.append("causal language in the sentence but claim is not marked causal")
        elif len(claim.event_ids) < CAUSAL_MIN_EVENTS:
            reasons.append(
                f"causal claim needs at least {CAUSAL_MIN_EVENTS} events, has {len(claim.event_ids)}"
            )

    return Verdict(ok=not reasons, reasons=reasons, recomputed_value=recomputed)
