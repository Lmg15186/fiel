"""
claims.py - the two data shapes the whole pipeline agrees on.

Event  = one thing that happened on the pitch (comes from Willian's generator).
Claim  = one sentence the Explainer wants to put on air, plus its receipt.

Both are pydantic models, so a wrong field type or a missing field fails
immediately with a clear message instead of breaking something later.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# --- Event ------------------------------------------------------------------

EventType = Literal[
    "pass", "shot", "recovery", "loss", "foul", "substitution", "goal",
    "corner", "offside", "save", "clearance",
]


class Event(BaseModel):
    """One match event. Pitch coordinates are 0-100 on both axes,
    attacking left to right for the team in possession."""

    id: str = Field(..., description="unique id, e.g. e0217")
    minute: int = Field(..., ge=0, le=130)
    second: int = Field(0, ge=0, le=59)
    type: EventType
    team: Literal["A", "B"]
    player: str
    x: float = Field(..., ge=0, le=100)
    y: float = Field(..., ge=0, le=100)
    outcome: Literal["success", "fail", "n/a"] = "n/a"
    meta: dict = Field(default_factory=dict)


class Match(BaseModel):
    """A whole match as the generator writes it."""

    match_id: str
    home: str  # fictional team code, e.g. "A"
    away: str
    events: list[Event]

    def events_between(self, start_min: int, end_min: int) -> list[Event]:
        """Events with start_min <= minute < end_min."""
        return [e for e in self.events if start_min <= e.minute < end_min]

    def event_ids(self) -> set[str]:
        return {e.id for e in self.events}


# --- Claim ------------------------------------------------------------------

# The metrics the verifier knows how to recompute. Anything else is rejected,
# which forces the Explainer to stay inside what we can check.
MetricName = Literal[
    "possession_pct",        # share of passes by a team in a window
    "recovery_height",       # average x of recoveries by a team in a window
    "shots",                 # count of shots by a team in a window
    "shots_on_target",       # count of shots with outcome success
    "goals",                 # count of goals
    "pass_accuracy_pct",     # successful passes / passes
]


class Claim(BaseModel):
    """One sentence for air, with the receipt that backs it."""

    claim: str = Field(..., min_length=5, max_length=300)
    metric: MetricName
    value: float
    team: Literal["A", "B"]
    window_start: int = Field(..., ge=0, le=130)
    window_end: int = Field(..., ge=0, le=130)
    event_ids: list[str] = Field(..., min_length=1)
    # Set by the Explainer when it believes the claim states a cause.
    # The verifier only allows this when evidence is strong enough.
    causal: bool = False
    confidence: float = Field(0.5, ge=0, le=1)
    # Optional historical receipt when the sentence compares today with usual.
    baseline_value: Optional[float] = None
    baseline_match_ids: list[str] = Field(default_factory=list)


class Verdict(BaseModel):
    """What the verifier says about one claim."""

    ok: bool
    reasons: list[str] = Field(default_factory=list)
    recomputed_value: Optional[float] = None
