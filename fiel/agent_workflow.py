"""Microsoft Agent Framework orchestration for the FIEL broadcast desk.

The language-model calls still run through the Microsoft Foundry endpoint in
``llm_json.py``.  Agent Framework owns the hand-offs between the three roles;
the deterministic verifier remains inside the Explainer stage as a safety
gate before any claim can reach the Producer.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Never

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler

from fiel.claims import Claim, Match
from fiel.explainer import explain_and_verify
from fiel.memory import memory_for_match
from fiel.personalizer import personalize
from fiel.producer import produce


@dataclass
class PipelineRequest:
    match: Match
    audience: str = "fan"
    language: str = "pt"
    max_items: int = 3
    memory: dict | None = None
    reporter: Callable[[str], None] | None = None


@dataclass
class ExplainedMatch:
    request: PipelineRequest
    approved: list[Claim]
    verification_history: list[dict]


@dataclass
class ProducedMatch:
    explained: ExplainedMatch
    rundown: list[dict]


def demo_windows(match: Match) -> list[tuple[int, int, str]]:
    """Choose an opening window and the windows around one substitution."""
    windows = [(0, 15, "Opening phase.")]
    substitutions = [event for event in match.events if event.type == "substitution"]
    preferred = next((event for event in substitutions if event.team == "B"), None)
    substitution = preferred or (substitutions[0] if substitutions else None)
    if substitution is not None:
        minute = substitution.minute
        windows.extend([
            (max(0, minute - 10), minute,
             f"Ten minutes before team {substitution.team}'s substitution."),
            (minute, min(minute + 10, 90),
             f"Team {substitution.team} made a substitution at {minute}'. "
             "Compare with the previous window."),
        ])
    return list(dict.fromkeys(window for window in windows if window[1] > window[0]))


class ExplainerVerifierExecutor(Executor):
    """Generate claims and stop unsupported ones at a deterministic gate."""

    @handler
    async def process(
        self, request: PipelineRequest, ctx: WorkflowContext[ExplainedMatch]
    ) -> None:
        approved: list[Claim] = []
        history: list[dict] = []
        for start, end, context in demo_windows(request.match):
            if request.reporter:
                request.reporter(f"Explainer + Verifier: analysing minutes {start}-{end}...")
            claim, attempts = explain_and_verify(
                request.match, start, end, context, memory=request.memory
            )
            history.append({
                "window": [start, end],
                "context": context,
                "attempts": attempts,
                "accepted": claim is not None,
            })
            if claim is not None:
                approved.append(claim)
        await ctx.send_message(ExplainedMatch(request, approved, history))


class ProducerExecutor(Executor):
    """Rank only verifier-approved receipts for the live rundown."""

    @handler
    async def process(
        self, explained: ExplainedMatch, ctx: WorkflowContext[ProducedMatch]
    ) -> None:
        request = explained.request
        if request.reporter:
            request.reporter(
                f"Producer: ranking {len(explained.approved)} approved claim(s)..."
            )
        rundown = produce(explained.approved, max_items=request.max_items)
        await ctx.send_message(ProducedMatch(explained, rundown))


class PersonalizerExecutor(Executor):
    """Adapt voice/language, re-verify, then yield the broadcast package."""

    @handler
    async def process(
        self, produced: ProducedMatch, ctx: WorkflowContext[Never, dict]
    ) -> None:
        explained = produced.explained
        request = explained.request
        on_air = []
        for position, item in enumerate(produced.rundown, start=1):
            claim = Claim.model_validate(item["claim"])
            if request.reporter:
                request.reporter(
                    f"Personalizer: preparing item {position} for "
                    f"{request.audience}/{request.language}..."
                )
            version = personalize(
                claim, request.audience, request.language, request.match, request.memory
            )
            on_air.append({
                "position": position,
                "why_now": item["why_now"],
                "text": version["text"],
                "audience": version["audience"],
                "language": version["language"],
                "personalization_verified": version["verified"],
                "receipt": claim.model_dump(),
            })

        await ctx.yield_output({
            "match_id": request.match.match_id,
            "audience": request.audience,
            "language": request.language,
            "orchestration": {
                "framework": "Microsoft Agent Framework",
                "version": "1.23.0",
                "workflow": "ExplainerVerifier -> Producer -> Personalizer",
            },
            "match_memory": memory_for_match(request.match, request.memory or {}),
            "windows_analysed": len(explained.verification_history),
            "approved_claims": len(explained.approved),
            "verification_history": explained.verification_history,
            "on_air": on_air,
        })


def build_workflow():
    explainer = ExplainerVerifierExecutor(id="explainer_verifier")
    producer = ProducerExecutor(id="producer")
    personalizer = PersonalizerExecutor(id="personalizer")
    return (
        WorkflowBuilder(start_executor=explainer, name="fiel_broadcast_desk")
        .add_edge(explainer, producer)
        .add_edge(producer, personalizer)
        .build()
    )


async def run_pipeline_async(request: PipelineRequest) -> dict:
    result = await build_workflow().run(request)
    outputs = result.get_outputs()
    if len(outputs) != 1 or not isinstance(outputs[0], dict):
        raise RuntimeError("FIEL workflow did not yield one broadcast package")
    return outputs[0]


def run_pipeline(
    match: Match,
    audience: str = "fan",
    language: str = "pt",
    max_items: int = 3,
    reporter: Callable[[str], None] | None = None,
    memory: dict | None = None,
) -> dict:
    """Synchronous entry point used by the CLI, API, and Streamlit dashboard."""
    request = PipelineRequest(match, audience, language, max_items, memory, reporter)
    return asyncio.run(run_pipeline_async(request))
