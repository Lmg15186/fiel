"""
producer.py - the Producer agent: decides what goes on air, in what order.

Input:  approved claims for a stretch of the match (already verified).
Output: a short rundown: which claims to air, in which order, with a
        one-line "why now" for each. The Producer never changes a claim's
        text, number or event ids; it only selects and orders. That keeps
        the receipt valid without re-verifying.

Usage:
    from fiel.producer import produce
    rundown = produce(approved_claims, max_items=3)
"""

from fiel.claims import Claim
from fiel.llm_json import ask_json

SYSTEM = """You are the Producer of FIEL, a live football intelligence desk.
You receive claims that a verifier has already approved. Each has an index.
Pick the ones worth airing, order them for a broadcast, and say why each one
matters now. Prefer claims that show change (before vs after), surprises,
and anything tied to a substitution or a goal. Avoid repeating the same metric.

Rules:
- Use ONLY the claims given. Refer to them by index. Never rewrite them.
- Pick at most max_items.
- "why_now" is one short sentence, no numbers that are not in the claim.

Output JSON with exactly:
{"rundown": [{"index": int, "why_now": string}]}
"""


def produce(claims: list[Claim], max_items: int = 3) -> list[dict]:
    """Return [{"claim": Claim-as-dict, "why_now": str}] in broadcast order."""
    if not claims:
        return []
    listing = [
        {"index": i, "claim": c.claim, "metric": c.metric, "value": c.value,
         "team": c.team, "window": [c.window_start, c.window_end],
         "events": len(c.event_ids)}
        for i, c in enumerate(claims)
    ]
    user = (f"max_items = {max_items}\n"
            f"Approved claims:\n{listing}\n"
            "Build the rundown.")
    data = ask_json(SYSTEM, user)

    rundown = []
    seen = set()
    for item in data.get("rundown", [])[:max_items]:
        try:
            idx = int(item["index"])
        except (KeyError, ValueError, TypeError):
            continue
        if idx in seen or not 0 <= idx < len(claims):
            continue   # ignore invented or duplicated indexes
        seen.add(idx)
        rundown.append({"claim": claims[idx].model_dump(),
                        "why_now": str(item.get("why_now", "")).strip()})
    return rundown
