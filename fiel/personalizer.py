"""
personalizer.py - the Personalizer: same fact, different voice.

Takes an approved claim and rewrites the sentence for an audience
(analyst or fan) and a language (en or pt), WITHOUT touching the metric,
the value, the team, the window or the event ids. The verifier runs
again on the result, so a rewrite that drifts from the numbers is caught.

Usage:
    from fiel.personalizer import personalize
    text = personalize(claim, audience="fan", language="pt")
"""

from fiel.claims import Claim, Match
from fiel.llm_json import ask_json
from fiel.verifier import verify

AUDIENCES = {
    "analyst": "a tactical analyst on a broadcast panel: precise, calm, technical terms allowed",
    "fan": "a passionate supporter watching at home: vivid, simple words, no jargon",
}
LANGUAGES = {"en": "English (UK)", "pt": "Portuguese (Brazil)"}

SYSTEM = """You are the Personalizer of FIEL, a live football intelligence desk.
You rewrite ONE approved sentence for a given audience and language.

Rules:
- Keep every fact: the same team, the same number, the same minutes.
- Do not add any number, player name or cause that is not in the sentence.
- Teams are "team A" and "team B" ("time A"/"time B" in Portuguese).
- One sentence, max 30 words.

Output JSON with exactly: {"text": string}
"""


def personalize(claim: Claim, audience: str = "analyst", language: str = "en",
                match: Match | None = None, memory: dict | None = None) -> dict:
    """
    Returns {"text": str, "audience": str, "language": str, "verified": bool}.
    If `match` is given, the rewritten sentence is re-verified with the
    original receipt (metric, value, ids) to make sure nothing drifted.
    """
    if audience not in AUDIENCES or language not in LANGUAGES:
        raise ValueError("audience must be analyst|fan, language en|pt")

    user = (f"Audience: {AUDIENCES[audience]}\n"
            f"Language: {LANGUAGES[language]}\n"
            f"Original sentence: {claim.claim}\n"
            f"Facts you must keep: team {claim.team}, {claim.metric} = {claim.value}, "
            f"minutes {claim.window_start}-{claim.window_end}.")
    if claim.baseline_value is not None:
        user += (f" Historical baseline = {claim.baseline_value} from matches "
                 f"{claim.baseline_match_ids}.")
    data = ask_json(SYSTEM, user)
    text = str(data.get("text", "")).strip() or claim.claim

    verified = True
    if match is not None:
        rewritten = claim.model_copy(update={"claim": text})
        verified = verify(rewritten, match, memory).ok
        if not verified:
            text = claim.claim   # fall back to the approved original

    return {"text": text, "audience": audience, "language": language, "verified": verified}
