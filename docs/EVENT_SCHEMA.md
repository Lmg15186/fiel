# FIEL event schema (v0)

This is the contract between the generator (Willian) and the agents (Luiza).
Both sides validate against `fiel/claims.py` (`Event` and `Match`). Change it
there first, then here.

## Match file

```json
{
  "match_id": "m-2026-001",
  "home": "A",
  "away": "B",
  "events": [ ...Event ]
}
```

Teams are only ever `"A"` and `"B"`. Real club names, crests or colours never
appear anywhere in the data.

## Event

| Field | Type | Notes |
| --- | --- | --- |
| id | string | unique in the match, e.g. `e0217` |
| minute | int 0-130 | match minute (90 + stoppage/extra time) |
| second | int 0-59 | |
| type | enum | `pass, shot, recovery, loss, foul, substitution, goal, corner, offside, save, clearance` |
| team | `"A"` or `"B"` | |
| player | string | `A1`..`A14`, `B1`..`B14` (fictional) |
| x | float 0-100 | pitch length, 0 = own goal line, 100 = opponent goal line |
| y | float 0-100 | pitch width |
| outcome | enum | `success`, `fail`, `n/a` |
| meta | object | free extras, e.g. `{"off": "B6", "on": "B12"}` on a substitution |

Example:

```json
{"id":"e0217","minute":65,"second":12,"type":"recovery","team":"B","player":"B7","x":61.5,"y":34.0,"outcome":"success","meta":{}}
```

## Metrics the verifier can recompute

| metric | how |
| --- | --- |
| possession_pct | team passes / all passes in the window, x100 |
| recovery_height | mean x of the team's recoveries |
| shots | count of `shot` |
| shots_on_target | count of `shot` with `outcome = success` |
| goals | count of `goal` |
| pass_accuracy_pct | successful passes / passes, x100 |

If the generator wants the Explainer to talk about something else (xG, pressure,
win probability), add the metric to `recompute()` in `fiel/verifier.py` first.

## Planted stories (truth file)

For each match the generator also writes `<match_id>_truth.json`:

```json
{
  "match_id": "m-2026-001",
  "planted_stories": [
    {"id": "story-1", "description": "...", "metric": "recovery_height",
     "team": "B", "before": [55, 65], "after": [65, 75]}
  ]
}
```

The evaluation script counts how many planted stories the Explainer found.
