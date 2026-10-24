# FIEL — team hand-off and final delivery checklist

Last updated: 24 October 2026 (Sydney).

This note is how the two of us (Willian and Luiza) keep the delivery in sync.
It replaces the earlier Portuguese hand-off note so that everything in the
repository is in English.

## Definitive links

- Public demo (GitHub Pages): https://willian-yudy-f.github.io/fiel-live/
- Public API on Azure App Service: https://fiel-api-c3839e.azurewebsites.net/docs
- Health check: https://fiel-api-c3839e.azurewebsites.net/health
- Official repository: https://github.com/Lmg15186/fiel
- Hosting repository for the demo: https://github.com/Willian-Yudy-F/fiel-live
- GitHub Actions: https://github.com/Lmg15186/fiel/actions

## Delivery status

- Complete code on the official repository; 47 automated tests pass locally and on GitHub Actions.
- Microsoft Foundry used with a real `gpt-5-mini` deployment; the featured run is stored in `data/demo_agents.json`.
- Microsoft Agent Framework 1.23 runs the Explainer/Verifier → Producer → Personalizer workflow.
- FastAPI hosted on Azure App Service (F1 Free, Linux, Australia East) with nine OpenAPI routes, including `GET /matches/{id}/memory` and `POST /matches/{id}/verify`. Redeployed on 24 October from Azure Cloud Shell.
- The public demo reads live numbers from the Azure API (score, xG, win outlook per minute, on-air package, and the events behind the receipt). If the free tier is asleep it shows the stored package and says so on screen.
- MCP server (`python -m fiel.mcp_server`) exposes the deterministic engine as tools for external agents; see `docs/MCP.md`.
- 30-match evaluation complete: 49/49 planted signals detected, 49/49 unsafe causal claims rejected, 49/49 safe corrections accepted.
- README, architecture, evaluation, submission copy, changelog and video script are up to date.

## What is left before submitting

1. Choose the official team representative (the Innovation Studio project #126807 is owned by Luiza's account).
2. Record the video (about 1:45) following `docs/VIDEO_SCRIPT.md`, in English, no third-party music or marks.
3. Publish the video as **unlisted** on YouTube.
4. Put the video link in `docs/SUBMISSION.md` and in the submission form.
5. Copy the **Ready-to-paste form answers** from `docs/SUBMISSION.md` into the form.
6. Check the team members' names and submit before the deadline (27 October, 11:59 pm Pacific = 28 October, 5:59 pm Sydney). Internal target: Tuesday 27 October evening, Sydney.

## Recommended demo path

1. Open the public demo and confirm the badge reads **LIVE API · AZURE APP SERVICE**.
2. Move the replay from 59' to 69' and show Team A's outlook going from 7% to 73%.
3. Open **Agent Desk**: framework banner, four stages, historical baseline, receipt. Click **Open the events behind this receipt**.
4. Open **Verification Lab**: the causal sentence rejected and the safe correction accepted.
5. Open **Ground Truth**: the 30-match evaluation.
6. Optional: in the API docs, run `POST /matches/m-003-T4-T3/verify` with an edited value and show the verifier rejecting it.

## Statements we can make

- Foundry and Agent Framework were really used; the demo shows the stored result of a real Foundry run so it works without credentials.
- All clubs, players, matches and events are fictional; no proprietary Premier League data was used.
- The verifier recomputes every metric in Python; the model never grades its own output.
- The interface is hosted on GitHub Pages; the API that feeds it is hosted on Azure App Service.
- The MCP server is our own, built with the official Python SDK.

## Statements we must not make

- That the interface itself is hosted on Azure (only the API is).
- That the predictive model has production-grade sporting accuracy.
- That 49/49 measures subjective LLM quality; it measures synthetic ground truth and guardrails.
- That our MCP server is the "Azure MCP Server" product.
- Any use of real club names, crests, players or footage.

## Azure resources

Resource group `fiel-rg` in Luiza's Azure for Students subscription holds the Microsoft Foundry resource `fiel-foundry` (project `fiel`, deployment `gpt-5-mini`), the F1 App Service plan `fiel-api-free-plan` and the web app `fiel-api-c3839e`. Subscription and tenant identifiers are deliberately kept out of the repository; the deploy script reads the subscription id from the `FIEL_SUBSCRIPTION_ID` environment variable (see `docs/AZURE_DEPLOY.md`).

## Key files

- `README.md` — presentation and main instructions
- `docs/SUBMISSION.md` — ready-to-paste form text
- `docs/VIDEO_SCRIPT.md` — exact video script
- `docs/ARCHITECTURE.md` — technical design
- `docs/EVALUATION.md` — methodology and results
- `docs/MCP.md` — MCP server tools and client configuration
- `docs/SETUP.md` — local execution
- `docs/CHANGELOG.md` — what changed and when
- `data/demo_agents.json` — the real Foundry run used in the demo
