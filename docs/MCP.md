# FIEL MCP server

FIEL exposes its deterministic match-intelligence engine as a
[Model Context Protocol](https://modelcontextprotocol.io/) server, built with
the official `mcp` Python SDK (`FastMCP`). Inside FIEL the agents coordinate
through Microsoft Agent Framework; MCP is the door for agents **outside** FIEL
(GitHub Copilot in VS Code, a Foundry agent, Claude Desktop) to use the same
verified numbers as tools.

Nothing in this server calls a language model. Every tool runs the same Python
functions the FastAPI service and the dashboard use, so an external agent gets
exactly the numbers a judge sees on screen.

> Naming note: this is FIEL's own MCP server. It is not the *Azure MCP Server*
> product, and the README does not claim otherwise.

## Tools

| Tool | Arguments | Returns |
| --- | --- | --- |
| `list_matches` | — | the six synthetic matches with final scores |
| `get_match_state` | `match_id`, `minute` | score, xG and seeded Monte Carlo win probability at that minute |
| `get_timeline` | `match_id` | win probability every 5 minutes and the pressure index per window |
| `get_events` | `match_id`, `start`, `end`, `ids` | raw events for a window, or the exact events behind a receipt |
| `get_team_memory` | `match_id` | usual possession, pass accuracy, recovery height and pressure for both sides, built from the *other* matches |
| `get_broadcast` | `match_id` | the stored on-air package from the real Microsoft Foundry run |
| `verify_claim` | `match_id`, `claim` (JSON) | FIEL's deterministic verdict: `ok` plus the exact reasons |

`verify_claim` is the interesting one for an agent: it can draft a sentence,
ask FIEL whether the numbers hold, and only publish when `ok` is true.

## Run it

```bash
pip install -r requirements.txt   # includes mcp>=1.10,<2
python -m fiel.mcp_server         # stdio transport
```

## Connect a client

VS Code / GitHub Copilot (`.vscode/mcp.json`):

```json
{
  "servers": {
    "fiel": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "fiel.mcp_server"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fiel": {
      "command": "python",
      "args": ["-m", "fiel.mcp_server"],
      "cwd": "/absolute/path/to/fiel"
    }
  }
}
```

Then ask the agent, for example: *"Using FIEL, what was the win probability
of match m-003-T4-T3 at minute 69, and does the claim 'team B held 78%
possession between 69 and 79' verify?"*

## Tests

`tests/test_mcp_server.py` checks that all seven tools are registered with
descriptions, that the tool functions agree with the engine, that memory
excludes the current match, and that `verify_claim` accepts a true claim and
rejects a wrong value with a `value mismatch` reason. The server was also
exercised end to end over stdio with the SDK's own client.
