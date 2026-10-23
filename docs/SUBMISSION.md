# Submission copy and judging path

## Title

FIEL — Football Intelligence Engine, Live

## One-line pitch

FIEL turns synthetic football events into multilingual, predictive match
intelligence where every sentence on air comes with a verifiable receipt.

## Short description

Broadcast teams need stories in seconds, but fluent AI can invent numbers or
overstate causality. FIEL combines Microsoft Foundry agents with a deterministic
evidence gate. The Explainer proposes one claim and cites its metric, time
window and event IDs; Python independently recomputes it, rejects unsupported
language and returns precise rewrite feedback. Microsoft Agent Framework then
hands approved claims to a Producer and a Personalizer for analyst/fan voices
in English or Portuguese. Match Memory compares today with each fictional
team's historical baseline, while transparent xG, pressure and win probability
show how the match is changing.

The public replay is judge-safe: it uses a cached real Foundry run, exposes
receipts and failure recovery, and needs no secret. A reproducible 30-match
benchmark detected all 49 planted tactical signals, rejected all 49 unsafe
causal claims and accepted all 49 evidence-safe corrections. These figures
measure synthetic ground truth and guardrails, not subjective LLM quality.

## Microsoft technology actually used

- Microsoft Foundry with a deployed `gpt-5-mini` model
- Microsoft Agent Framework 1.23 workflow orchestration
- Azure Container Apps for the public experience
- GitHub for public source, collaboration and delivery

## Two-minute judging path

1. Open **Match Room**, select `m-003-T4-T3`, and move to minute 69–79.
2. Point to win probability and pressure changing around the substitution/goal sequence.
3. Open **Agent Desk** and show the Agent Framework banner, historical baseline and on-air receipt.
4. Open **Verification Lab** and show unsupported causality rejected, corrected and accepted.
5. Open **Data & Ground Truth** and show planted stories plus the evaluation figures.

## Reproduce locally

```bash
pip install -r requirements.txt
pytest -q
streamlit run dashboard.py
python evaluate.py --matches 30 --seed 2026
```

Model-backed run (requires your own Foundry deployment):

```bash
cp .env.example .env
python run_agents.py data/m-003-T4-T3.json --audience fan --language pt
```

## Final form checklist

- Repository: `https://github.com/Lmg15186/fiel`
- Public demo: add Azure URL after deployment
- Video: add an unlisted public URL, under two minutes
- Representative: team must choose one person before final submission
- Confirm every listed technology is present in the repository or deployment
