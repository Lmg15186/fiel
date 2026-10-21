"""
llm_json.py - small wrapper around the Foundry model that always returns JSON.

Every agent in FIEL (Explainer, Producer, Personalizer) talks to the model
through this one function. The agent never gets free text back: it gets a
Python dict parsed from the JSON the model wrote. If the model does not
return valid JSON we retry once with a stricter reminder, and if it still
fails we raise an error so the caller can decide what to do.

Usage:
    from fiel.llm_json import ask_json
    data = ask_json("You write football claims as JSON.", "Describe minute 65.")
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# Load FOUNDRY_* variables from the .env file in the repo root.
load_dotenv()

ENDPOINT = os.getenv("FOUNDRY_ENDPOINT")
API_KEY = os.getenv("FOUNDRY_API_KEY")
DEPLOYMENT = os.getenv("FOUNDRY_DEPLOYMENT", "gpt-5-mini")

if not ENDPOINT or not API_KEY:
    raise RuntimeError(
        "FOUNDRY_ENDPOINT and FOUNDRY_API_KEY must be set in .env "
        "(see .env.example)."
    )

# The Foundry endpoint exposes the OpenAI v1 API, so the standard client works.
client = OpenAI(base_url=ENDPOINT, api_key=API_KEY)

# Added to every system prompt so the model knows the output contract.
JSON_RULE = (
    "Respond with ONLY a single valid JSON object. "
    "No markdown, no code fences, no text before or after the JSON."
)


def _strip_fences(text: str) -> str:
    """Remove ```json ... ``` fences if the model added them anyway."""
    text = text.strip()
    if text.startswith("```"):
        # drop the first line (``` or ```json) and the closing fence
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def ask_json(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> dict:
    """
    Send one request to the model and return the JSON it wrote as a dict.

    system_prompt: who the agent is and what it must produce.
    user_prompt:   the data or question for this call.
    """
    messages = [
        {"role": "system", "content": f"{system_prompt}\n\n{JSON_RULE}"},
        {"role": "user", "content": user_prompt},
    ]

    last_error = None
    for attempt in range(2):
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=messages,
            max_completion_tokens=max_tokens,
            # gpt-5-mini is a reasoning model; "low" keeps calls cheap and fast.
            reasoning_effort="low",
            # Ask the API to enforce a JSON object in the reply.
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or ""
        try:
            return json.loads(_strip_fences(text))
        except json.JSONDecodeError as err:
            last_error = err
            # Second attempt: show the model what it sent and ask again.
            messages.append({"role": "assistant", "content": text})
            messages.append(
                {
                    "role": "user",
                    "content": "That was not valid JSON. Send ONLY the JSON object again.",
                }
            )

    raise ValueError(f"Model did not return valid JSON after 2 attempts: {last_error}")


if __name__ == "__main__":
    # Quick manual check: python -m fiel.llm_json
    demo = ask_json(
        "You are a football analyst. Output a claim about the match situation.",
        'Schema: {"claim": string, "metric": string, "value": number, "event_ids": [string]}. '
        "Team B had 68% possession between minute 65 and 70 after a substitution "
        "(events e101, e102, e103).",
    )
    print(json.dumps(demo, indent=2, ensure_ascii=False))
