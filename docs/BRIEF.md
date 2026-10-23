# FIEL project brief

## Event fit

FIEL was built for **Inside the Game: Developer Hackathon**, in the Synthetic
Match Insights Engine track. It uses football-realistic synthetic data to
produce explainable match intelligence, narratives and recaps for studio,
broadcast and streaming scenarios.

## Business need

A live production team has seconds to decide what matters. Raw event feeds are
too dense; unconstrained AI can produce plausible but wrong claims. FIEL gives
the producer a ranked story, a concise version for the selected audience and a
receipt that editorial staff can inspect before broadcast.

## Success criteria

- Turn a match window into one useful claim with metric, value and event IDs.
- Reject wrong values, invalid evidence, window mismatch and unsupported causality.
- Recover through a bounded rewrite without silently changing the receipt.
- Compare the current match with verified historical baselines.
- Show predictive outlook, tactical change and multilingual delivery in one demo.
- Keep the public judging path reliable without exposing credentials.
- Publish repeatable tests and ground-truth evaluation with honest scope.

## In scope

- Six fictional source matches and reproducible batch evaluation.
- Pressure, xG, win probability, possession, passing and recovery analytics.
- Foundry Explainer, Producer and Personalizer roles.
- Microsoft Agent Framework orchestration.
- Deterministic verification and Match Memory receipts.
- Streamlit replay, Agent Desk, Verification Lab, FastAPI and Azure hosting.

## Deliberately out of scope

- Betting advice, real Premier League data, club/player identity or licensed media.
- A claimed trained prediction model without a defensible training dataset.
- Kafka, Spark, Hadoop, Snowflake or dbt where the current scale does not need them.
- Fully autonomous publication without human editorial oversight.

## Evaluation

The deterministic benchmark creates 30 matches with known planted stories and
measures signal detection and guardrail behaviour. Language-model quality is
demonstrated separately through a cached real Foundry run and is not inflated
into an automated accuracy claim.
