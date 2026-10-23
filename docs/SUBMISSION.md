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
- GitHub for public source, collaboration and automated testing
- GitHub Actions and GitHub Pages for the credential-free judge experience

The public experience does not claim an Azure deployment. It presents a cached
output from a real Foundry run so judges can inspect the complete workflow
without credentials, quota or tenant access. Azure hosting remains an optional
post-submission deployment path.

## Two-minute judging path

1. Open the [public judge experience](https://willian-yudy-f.github.io/fiel-live/).
2. In **Match Room**, move the replay from minute 59 to 69 and show Team A's outlook changing from 7% to 71%.
3. Open **Agent Desk** and show the Agent Framework stages, historical baseline and on-air receipt.
4. Open **Verification Lab** and show unsupported causality rejected, corrected and accepted.
5. Open **Ground Truth** and show the 30-match evaluation figures.

## Ready-to-paste form answers

### What problem does the project solve?

Live football generates more events than a production team can interpret in
real time. Generative AI can summarise those events quickly, but fluent output
can contain wrong numbers, cite the wrong match window or turn correlation into
causation. FIEL gives studio, broadcast and streaming teams timely match
intelligence while making every published sentence independently verifiable.

### What did the team build?

FIEL is an explainable match-intelligence pipeline for synthetic football data.
A deterministic engine computes possession, pressure, expected goals and a
Monte Carlo win outlook. Match Memory compares live values with each fictional
team's historical baseline. A Microsoft Foundry Explainer then proposes one
structured claim with its metric, value, window and event IDs. A deterministic
Python gate recomputes the claim before Microsoft Agent Framework can hand it to
the Producer and Personalizer. Approved facts can be delivered for analyst or
fan audiences in English or Portuguese without changing the evidence.

### What makes FIEL different?

Most AI sports demos optimise for fluent commentary. FIEL optimises for a
broadcast decision: should this sentence be allowed on air? The language model
never verifies itself. Every claim carries a receipt, causal overstatement is
explicitly blocked, and the rewrite loop is visible. Synthetic ground truth
also makes the system measurable instead of relying only on a convincing demo.

### How is Microsoft technology used?

A deployed `gpt-5-mini` model in Microsoft Foundry generated the featured
evidence-bound insight. Microsoft Agent Framework 1.23 orchestrates the
Explainer/Verifier hand-off, Producer and Personalizer. The repository includes
the executable workflow and a cached real Foundry result so judges can reproduce
the deterministic portions without secrets. GitHub Actions runs the complete
test suite and publishes the public judge experience.

### How was the project evaluated?

The generator plants known tactical changes in synthetic matches and saves
separate ground-truth files. Across 30 reproducible evaluation matches, FIEL
detected 49 of 49 planted signals, rejected 49 of 49 unsafe causal claims and
accepted 49 of 49 evidence-safe corrections. The repository currently passes
38 automated tests covering generation, tactics, verification, memory, agents,
API and dashboard behaviour.

### Responsible AI and data statement

All clubs, players, matches and events are fictional. FIEL uses no proprietary
Premier League feed, club crest or personal data. Deterministic code recalculates
every metric, unsupported causal language is rejected, receipts expose the
supporting event IDs, and personalization is re-verified before delivery.

### Links

- Public demo: https://willian-yudy-f.github.io/fiel-live/
- Live Azure API: https://fiel-api-c3839e.azurewebsites.net/docs
- Azure health evidence: https://fiel-api-c3839e.azurewebsites.net/health
- Source repository: https://github.com/Lmg15186/fiel
- Demo deployment source: https://github.com/Willian-Yudy-F/fiel-live

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
- Public demo: `https://willian-yudy-f.github.io/fiel-live/`
- Live API: `https://fiel-api-c3839e.azurewebsites.net/docs`
- Video: add an unlisted public URL, under two minutes
- Representative: team must choose one person before final submission
- Confirm every listed technology is present in the repository or deployment
