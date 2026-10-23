# Changelog

Dates are Sydney time. Only changes that matter to a reader of the repository
are listed; the full history is in `git log`.

## 2026-10-23 (evening) — live judge experience, MCP server, honest docs

- **Judge experience reads the Azure API.** The public page used to be fully
  static. It now requests score, xG and win probability for every slider
  minute from `GET /matches/{id}/state`, loads the on-air package from
  `GET /matches/{id}/broadcast`, and lets the judge open the real events behind
  the receipt (`GET /matches/{id}/events?ids=`). A badge says whether the
  numbers are coming from Azure or from the stored fallback.
- **MCP server** (`fiel/mcp_server.py`, `docs/MCP.md`): seven deterministic
  tools for external agents, including `verify_claim`. Covered by five tests
  and exercised end to end over stdio.
- **API**: `GET /` redirects to `/docs`; new `GET /matches/{id}/memory`; new
  `POST /matches/{id}/verify` (run the verifier on any claim, no model call);
  `GET /matches/{id}/claims` now returns the receipts of the stored Foundry run
  instead of an empty list; parsed matches and memory are cached in process.
- **Docs made consistent**: `SUBMISSION.md` no longer says there is no Azure
  deployment; `ARCHITECTURE.md` and `api.py` describe App Service (the real
  host) instead of Container Apps; README structure lists every module; the
  tenant ID was removed from the public hand-off note; the 59'→69' swing is
  quoted as 7% → 73%, which is what the seeded engine returns.
- Tests: 38 → 47.

## 2026-10-23 — deployment and submission package

- FastAPI deployed to Azure App Service (F1 Free) with a one-script Cloud
  Shell deploy; public judge experience on GitHub Pages; submission copy,
  video script and team hand-off.

## 2026-10-22 / 23 — pipeline

- Synthetic generator with planted stories, tactics engine, deterministic
  verifier, Foundry Explainer with bounded rewrite, Producer, Personalizer,
  Match Memory, Microsoft Agent Framework workflow, Streamlit Agent Desk,
  reproducible 30-match evaluation.
