"""FIEL Replay Dashboard — visual demo powered by synthetic match data.

Run from the repository root:

    streamlit run dashboard.py

The dashboard is deliberately offline-first: it visualises match data,
deterministic metrics and verifier decisions without calling Microsoft Foundry.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fiel.claims import Claim, Match
from fiel.tactics import (
    pressure_windows,
    score_at,
    win_probability,
    win_probability_timeline,
    xg_totals,
)
from fiel.verifier import recompute, verify


DATA_DIR = Path(__file__).parent / "data"
TEAM_NAMES = {"A": "Team A", "B": "Team B"}
TEAM_COLOURS = {"A": "#7C5CFF", "B": "#21D4A7"}
EVENT_COLOURS = {
    "goal": "#F6C85F",
    "shot": "#FF6B9D",
    "recovery": "#27C8F3",
    "substitution": "#A78BFA",
    "foul": "#FF8A65",
}


st.set_page_config(
    page_title="FIEL — Replay Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --fiel-bg: #080B12;
            --fiel-panel: #111623;
            --fiel-line: rgba(255,255,255,.09);
            --fiel-text: #F5F7FB;
            --fiel-muted: #98A2B3;
            --fiel-green: #21D4A7;
            --fiel-purple: #7C5CFF;
            --fiel-red: #FF5B6E;
            --fiel-gold: #F6C85F;
        }
        .stApp { background: var(--fiel-bg); color: var(--fiel-text); }
        [data-testid="stSidebar"] { background: #0C1019; border-right: 1px solid var(--fiel-line); }
        [data-testid="stHeader"] { background: rgba(8,11,18,.82); }
        .block-container { max-width: 1480px; padding-top: 1.4rem; padding-bottom: 3rem; }
        h1, h2, h3 { letter-spacing: -.025em; }
        h1 { font-size: clamp(2rem, 4vw, 3.55rem) !important; line-height: 1 !important; }
        .fiel-kicker { color: var(--fiel-green); font-weight: 800; letter-spacing: .16em; font-size: .73rem; }
        .fiel-subtitle { color: var(--fiel-muted); font-size: 1rem; max-width: 760px; margin-top: .75rem; }
        .live-pill { display: inline-flex; align-items: center; gap: .45rem; background: rgba(255,91,110,.12);
            color: #FF8795; border: 1px solid rgba(255,91,110,.3); border-radius: 999px;
            padding: .32rem .7rem; font-size: .72rem; font-weight: 800; letter-spacing: .08em; }
        .live-dot { width: .5rem; height: .5rem; border-radius: 50%; background: var(--fiel-red);
            box-shadow: 0 0 0 .25rem rgba(255,91,110,.13); }
        .hero-row { display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; margin-bottom:1rem; }
        .scoreboard { background: linear-gradient(135deg, rgba(124,92,255,.13), rgba(33,212,167,.08));
            border:1px solid var(--fiel-line); border-radius:18px; padding:1.1rem 1.25rem; margin:.5rem 0 1rem; }
        .score-grid { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:1rem; }
        .team-a { color:#B4A5FF; } .team-b { color:#64E6C5; }
        .team-name { font-size:.78rem; color:var(--fiel-muted); letter-spacing:.09em; font-weight:800; }
        .team-profile { font-size:.78rem; color:var(--fiel-muted); margin-top:.2rem; }
        .score { font-size:2.6rem; font-weight:850; letter-spacing:.08em; text-align:center; }
        .clock { text-align:center; color:var(--fiel-green); font-size:.78rem; font-weight:800; }
        [data-testid="stMetric"] { background: var(--fiel-panel); border: 1px solid var(--fiel-line);
            padding: .8rem 1rem; border-radius: 14px; }
        [data-testid="stMetricLabel"] { color: var(--fiel-muted); }
        .insight-card { background: linear-gradient(145deg, rgba(33,212,167,.09), rgba(124,92,255,.08));
            border:1px solid rgba(33,212,167,.25); border-radius:18px; padding:1.25rem 1.35rem; margin:.35rem 0 1rem; }
        .insight-label { color:var(--fiel-green); font-size:.72rem; font-weight:850; letter-spacing:.13em; }
        .insight-copy { color:var(--fiel-text); font-size:1.28rem; line-height:1.38; font-weight:720; margin:.55rem 0 .8rem; }
        .receipt { color:var(--fiel-muted); font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
            font-size:.75rem; border-top:1px solid var(--fiel-line); padding-top:.7rem; }
        .verdict-card { border-radius:18px; padding:1.15rem 1.25rem; height:100%; }
        .rejected { background:rgba(255,91,110,.075); border:1px solid rgba(255,91,110,.3); }
        .accepted { background:rgba(33,212,167,.075); border:1px solid rgba(33,212,167,.3); }
        .verdict-title { font-size:.72rem; letter-spacing:.13em; font-weight:850; margin-bottom:.7rem; }
        .verdict-copy { font-size:1.05rem; line-height:1.42; font-weight:680; }
        .reason { color:#FF98A4; font-size:.83rem; margin-top:.75rem; }
        .accepted-note { color:#78EACD; font-size:.83rem; margin-top:.75rem; }
        .story-card { background:var(--fiel-panel); border:1px solid var(--fiel-line); border-radius:15px;
            padding:1rem 1.1rem; margin-bottom:.75rem; }
        .story-id { color:var(--fiel-purple); font-size:.7rem; font-weight:850; letter-spacing:.12em; }
        .story-copy { margin-top:.45rem; line-height:1.4; }
        .story-meta { color:var(--fiel-muted); font-size:.75rem; margin-top:.55rem; }
        .event-chip { display:inline-block; padding:.2rem .5rem; border-radius:999px; margin:.12rem;
            background:rgba(255,255,255,.06); border:1px solid var(--fiel-line); color:#C7CEDB; font-size:.72rem; }
        div[data-testid="stTabs"] button { font-weight:750; }
        .stPlotlyChart { border:1px solid var(--fiel-line); border-radius:16px; overflow:hidden; }
        @media (max-width: 760px) {
            .hero-row { display:block; }
            .score { font-size:2rem; }
            .score-grid { gap:.4rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def available_matches() -> list[str]:
    return sorted(
        path.stem
        for path in DATA_DIR.glob("m-*.json")
        if not path.stem.endswith("_truth")
    )


@st.cache_data(show_spinner=False)
def load_match(match_id: str) -> Match:
    return Match.model_validate_json(
        (DATA_DIR / f"{match_id}.json").read_text(encoding="utf-8")
    )


@st.cache_data(show_spinner=False)
def load_truth(match_id: str) -> dict:
    path = DATA_DIR / f"{match_id}_truth.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


@st.cache_data(show_spinner=False)
def cached_win_timeline(match_id: str) -> list[dict]:
    return win_probability_timeline(load_match(match_id), step=5, seed=2026)


def latest_verified_insight(match: Match, minute: int) -> tuple[Claim, object]:
    """Create one deterministic, verifier-compatible insight for the replay."""
    end = min(minute + 1, 91)
    start = max(0, end - 10)
    possession = {
        team: recompute("possession_pct", team, match, start, end)
        for team in ("A", "B")
    }
    team = max(possession, key=lambda key: possession[key] or 0)
    value = possession[team]
    if value is None:
        # Generated matches always have passes, but keep a safe early-window fallback.
        value, team = 0.0, "A"
    event_ids = [
        event.id
        for event in match.events_between(start, end)
        if event.team == team and event.type == "pass"
    ]
    if not event_ids:
        event_ids = [match.events[0].id]

    claim = Claim(
        claim=(
            f"Team {team} held {value:.1f}% of the ball between minutes "
            f"{start} and {end}."
        ),
        metric="possession_pct",
        value=round(value, 1),
        team=team,
        window_start=start,
        window_end=end,
        event_ids=event_ids,
        causal=False,
        confidence=0.94,
    )
    return claim, verify(claim, match)


def verification_scene(match: Match, truth: dict) -> tuple[Claim, object, Claim, object]:
    """Return the staged causal rejection and its evidence-safe correction."""
    recovery_story = next(
        (
            story
            for story in truth.get("planted_stories", [])
            if story.get("kind") == "recover_higher_after_sub"
        ),
        None,
    )
    if recovery_story:
        team = recovery_story["team"]
        start, end = recovery_story["after"]
        sub_minute = start
    else:
        substitution = next(
            (event for event in match.events if event.type == "substitution"), None
        )
        team = substitution.team if substitution else "B"
        sub_minute = substitution.minute if substitution else 65
        start, end = sub_minute, min(sub_minute + 10, 90)

    value = recompute("recovery_height", team, match, start, end)
    evidence = [
        event.id
        for event in match.events_between(start, end)
        if event.team == team and event.type == "recovery"
    ]
    if value is None or not evidence:
        # A safe fallback for a match without recovery events in the story window.
        start, end = 0, 15
        team = "A"
        value = recompute("recovery_height", team, match, start, end) or 0.0
        evidence = [
            event.id
            for event in match.events_between(start, end)
            if event.team == team and event.type == "recovery"
        ]

    bad = Claim(
        claim=f"The substitution at {sub_minute}' won the game for team {team}.",
        metric="recovery_height",
        value=round(value, 1),
        team=team,
        window_start=start,
        window_end=end,
        event_ids=evidence[:2] or [match.events[0].id],
        causal=True,
        confidence=0.88,
    )
    corrected = Claim(
        claim=(
            f"Between minutes {start} and {end}, team {team} recovered the ball "
            f"at an average height of {value:.1f}."
        ),
        metric="recovery_height",
        value=round(value, 1),
        team=team,
        window_start=start,
        window_end=end,
        event_ids=evidence,
        causal=False,
        confidence=0.93,
    )
    return bad, verify(bad, match), corrected, verify(corrected, match)


def chart_layout(title: str) -> dict:
    return {
        "title": {"text": title, "x": 0.03, "font": {"size": 15}},
        "paper_bgcolor": "#111623",
        "plot_bgcolor": "#111623",
        "font": {"color": "#DCE2EC", "family": "Inter, sans-serif"},
        "margin": {"l": 44, "r": 24, "t": 55, "b": 42},
        "legend": {"orientation": "h", "y": 1.12, "x": 0.58},
        "hoverlabel": {"bgcolor": "#171D2B", "font_color": "#F5F7FB"},
    }


def win_probability_chart(match_id: str, minute: int) -> go.Figure:
    rows = cached_win_timeline(match_id)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[row["minute"] for row in rows],
            y=[row["p_A"] for row in rows],
            name="Team A",
            mode="lines",
            line={"color": TEAM_COLOURS["A"], "width": 3},
            fill="tozeroy",
            fillcolor="rgba(124,92,255,.10)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[row["minute"] for row in rows],
            y=[row["p_B"] for row in rows],
            name="Team B",
            mode="lines",
            line={"color": TEAM_COLOURS["B"], "width": 3},
            fill="tozeroy",
            fillcolor="rgba(33,212,167,.08)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[row["minute"] for row in rows],
            y=[row["p_draw"] for row in rows],
            name="Draw",
            mode="lines",
            line={"color": "#7F899B", "width": 2, "dash": "dot"},
        )
    )
    fig.add_vline(x=minute, line_width=1, line_dash="dash", line_color="#F6C85F")
    fig.update_layout(**chart_layout("Win probability timeline"))
    fig.update_xaxes(title="Match minute", gridcolor="rgba(255,255,255,.055)", range=[0, 90])
    fig.update_yaxes(tickformat=".0%", range=[0, 1], gridcolor="rgba(255,255,255,.055)")
    return fig


def pressure_chart(match: Match, minute: int) -> go.Figure:
    rows = pressure_windows(match)
    fig = go.Figure()
    for team in ("A", "B"):
        fig.add_trace(
            go.Bar(
                x=[row["start"] + 2.5 for row in rows],
                y=[row[f"press_{team}"] for row in rows],
                name=f"Team {team}",
                marker_color=TEAM_COLOURS[team],
                opacity=0.82,
            )
        )
    fig.add_vline(x=minute, line_width=1, line_dash="dash", line_color="#F6C85F")
    fig.update_layout(**chart_layout("Pressure index · five-minute windows"), barmode="group")
    fig.update_xaxes(title="Match minute", gridcolor="rgba(255,255,255,.055)", range=[0, 90])
    fig.update_yaxes(title="Index", gridcolor="rgba(255,255,255,.055)")
    return fig


def pitch_chart(match: Match, minute: int) -> go.Figure:
    start = max(0, minute - 9)
    events = [
        event
        for event in match.events_between(start, minute + 1)
        if event.type in EVENT_COLOURS
    ]
    fig = go.Figure()
    for event_type, colour in EVENT_COLOURS.items():
        group = [event for event in events if event.type == event_type]
        if not group:
            continue
        fig.add_trace(
            go.Scatter(
                x=[event.x for event in group],
                y=[event.y for event in group],
                mode="markers",
                name=event_type.title(),
                marker={
                    "size": [13 if event.type == "goal" else 9 for event in group],
                    "color": colour,
                    "line": {"width": 1, "color": "rgba(255,255,255,.45)"},
                },
                text=[
                    f"{event.minute}:{event.second:02d} · Team {event.team} · {event.player}"
                    for event in group
                ],
                hovertemplate="%{text}<extra>%{fullData.name}</extra>",
            )
        )
    shapes = [
        {"type": "rect", "x0": 0, "y0": 0, "x1": 100, "y1": 100, "line": {"color": "rgba(255,255,255,.55)"}},
        {"type": "line", "x0": 50, "y0": 0, "x1": 50, "y1": 100, "line": {"color": "rgba(255,255,255,.45)"}},
        {"type": "circle", "x0": 42, "y0": 34, "x1": 58, "y1": 66, "line": {"color": "rgba(255,255,255,.45)"}},
        {"type": "rect", "x0": 0, "y0": 22, "x1": 16, "y1": 78, "line": {"color": "rgba(255,255,255,.4)"}},
        {"type": "rect", "x0": 84, "y0": 22, "x1": 100, "y1": 78, "line": {"color": "rgba(255,255,255,.4)"}},
    ]
    fig.update_layout(
        **chart_layout(f"Event map · minutes {start}–{minute}"),
        shapes=shapes,
        height=390,
    )
    fig.update_xaxes(range=[-2, 102], visible=False)
    fig.update_yaxes(range=[-3, 103], visible=False, scaleanchor="x", scaleratio=0.68)
    return fig


def render_header(match_id: str) -> None:
    st.markdown(
        f"""
        <div class="hero-row">
          <div>
            <div class="fiel-kicker">FOOTBALL INTELLIGENCE ENGINE, LIVE</div>
            <h1>Match Replay Room</h1>
            <div class="fiel-subtitle">Follow the synthetic match, inspect the tactical signals and open the evidence receipt behind every statement.</div>
          </div>
          <div class="live-pill"><span class="live-dot"></span> SYNTHETIC REPLAY · {escape(match_id)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scoreboard(match: Match, truth: dict, minute: int) -> None:
    score = score_at(match, minute + 1)
    home_profile = truth.get("home_profile", "fictional home team").replace("-", " ")
    away_profile = truth.get("away_profile", "fictional away team").replace("-", " ")
    st.markdown(
        f"""
        <div class="scoreboard">
          <div class="score-grid">
            <div>
              <div class="team-name team-a">TEAM A · HOME</div>
              <div class="team-profile">{escape(home_profile.title())}</div>
            </div>
            <div>
              <div class="score">{score['A']} &nbsp;—&nbsp; {score['B']}</div>
              <div class="clock">{minute:02d}:00 · REPLAY POSITION</div>
            </div>
            <div style="text-align:right">
              <div class="team-name team-b">TEAM B · AWAY</div>
              <div class="team-profile">{escape(away_profile.title())}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_match_room(match: Match, truth: dict, match_id: str, minute: int) -> None:
    score = score_at(match, minute + 1)
    current_xg = xg_totals(match, upto_minute=minute + 1)
    probability = win_probability(match, min(minute, 90), runs=2500, seed=2026)
    relevant_events = [event for event in match.events if event.minute <= minute]

    metrics = st.columns(5)
    metrics[0].metric("Score", f"{score['A']} — {score['B']}")
    metrics[1].metric("xG · Team A", f"{current_xg['A']:.2f}")
    metrics[2].metric("xG · Team B", f"{current_xg['B']:.2f}")
    metrics[3].metric("Team A win", f"{probability['A']:.0%}")
    metrics[4].metric("Events processed", f"{len(relevant_events):,}")

    claim, verdict = latest_verified_insight(match, minute)
    status = "VERIFIED · READY FOR AIR" if verdict.ok else "HELD BY VERIFIER"
    event_chips = "".join(
        f'<span class="event-chip">{escape(event_id)}</span>'
        for event_id in claim.event_ids[:8]
    )
    if len(claim.event_ids) > 8:
        event_chips += f'<span class="event-chip">+{len(claim.event_ids) - 8} more</span>'
    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-label">{status}</div>
          <div class="insight-copy">“{escape(claim.claim)}”</div>
          <div class="receipt"><b>RECEIPT</b> &nbsp; {claim.metric} = {claim.value:.1f} &nbsp;·&nbsp; window {claim.window_start}–{claim.window_end}<br>{event_chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.plotly_chart(
            win_probability_chart(match_id, minute),
            width="stretch",
            config={"displayModeBar": False},
        )
    with right:
        st.plotly_chart(
            pitch_chart(match, minute),
            width="stretch",
            config={"displayModeBar": False},
        )

    st.plotly_chart(
        pressure_chart(match, minute),
        width="stretch",
        config={"displayModeBar": False},
    )

    st.subheader("Recent match events")
    key_events = [
        event
        for event in match.events_between(max(0, minute - 5), minute + 1)
        if event.type in {"goal", "shot", "recovery", "substitution", "foul"}
    ][-12:]
    if key_events:
        frame = pd.DataFrame(
            [
                {
                    "Time": f"{event.minute}:{event.second:02d}",
                    "Event": event.type.title(),
                    "Team": event.team,
                    "Player": event.player,
                    "Position": f"{event.x:.0f}, {event.y:.0f}",
                    "Event ID": event.id,
                }
                for event in reversed(key_events)
            ]
        )
        st.dataframe(frame, hide_index=True, width="stretch")
    else:
        st.info("No key events in the last five minutes. Move the replay control forward.")


def render_verification_lab(match: Match, truth: dict) -> None:
    st.subheader("One sentence. Two independent checks.")
    st.caption(
        "This scene is deterministic and reproducible. The model proposes a strong causal claim; "
        "the verifier recalculates the evidence before anything can go on air."
    )
    bad, bad_verdict, corrected, corrected_verdict = verification_scene(match, truth)

    left, arrow, right = st.columns([1, 0.12, 1], gap="medium")
    with left:
        reasons = "<br>".join(f"• {escape(reason)}" for reason in bad_verdict.reasons)
        st.markdown(
            f"""
            <div class="verdict-card rejected">
              <div class="verdict-title" style="color:#FF8795">✕ REJECTED</div>
              <div class="verdict-copy">“{escape(bad.claim)}”</div>
              <div class="reason">{reasons}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with arrow:
        st.markdown(
            "<div style='font-size:2rem;text-align:center;padding-top:4rem;color:#7C5CFF'>→</div>",
            unsafe_allow_html=True,
        )
    with right:
        status = "✓ ACCEPTED · ON AIR" if corrected_verdict.ok else "✕ HELD"
        st.markdown(
            f"""
            <div class="verdict-card accepted">
              <div class="verdict-title" style="color:#64E6C5">{status}</div>
              <div class="verdict-copy">“{escape(corrected.claim)}”</div>
              <div class="accepted-note">Number recomputed · window valid · evidence IDs found · no unsupported causality</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### The accepted receipt")
    receipt = corrected.model_dump()
    receipt["verifier"] = {
        "ok": corrected_verdict.ok,
        "recomputed_value": corrected_verdict.recomputed_value,
        "reasons": corrected_verdict.reasons,
    }
    st.json(receipt, expanded=True)

    st.markdown("### What the verifier checks")
    checks = st.columns(4)
    checks[0].metric("1 · Evidence", "IDs exist")
    checks[1].metric("2 · Timing", "Inside window")
    checks[2].metric("3 · Value", "Recomputed")
    checks[3].metric("4 · Language", "Causality safe")


def render_ground_truth(match: Match, truth: dict) -> None:
    st.subheader("Synthetic data with measurable ground truth")
    st.caption(
        "Because FIEL creates the match, it knows which tactical stories were planted. "
        "This makes discovery measurable instead of subjective."
    )
    total = len(match.events)
    goals = sum(event.type == "goal" for event in match.events)
    shots = sum(event.type == "shot" for event in match.events)
    recoveries = sum(event.type == "recovery" for event in match.events)
    cols = st.columns(4)
    cols[0].metric("Synthetic events", f"{total:,}")
    cols[1].metric("Goals", goals)
    cols[2].metric("Shots", shots)
    cols[3].metric("Recoveries", recoveries)

    st.markdown("### Planted stories")
    stories = truth.get("planted_stories", [])
    if not stories:
        st.info("No ground-truth file was found for this match.")
    for story in stories:
        before = story.get("before", ["?", "?"])
        after = story.get("after", ["?", "?"])
        st.markdown(
            f"""
            <div class="story-card">
              <div class="story-id">{escape(story.get('id', 'STORY'))} · {escape(story.get('kind', '').upper())}</div>
              <div class="story-copy">{escape(story.get('description', ''))}</div>
              <div class="story-meta">Metric: {escape(story.get('metric', ''))} · Team {escape(story.get('team', ''))} · Before {before[0]}–{before[1]} · After {after[0]}–{after[1]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Why this matters")
    st.write(
        "The evaluation can compare accepted FIEL claims with these hidden truth files to measure "
        "story discovery, verifier rejection and successful correction rates across many matches."
    )


def main() -> None:
    inject_styles()
    matches = available_matches()
    if not matches:
        st.error("No synthetic matches were found in the data directory.")
        st.stop()

    default = matches.index("m-003-T4-T3") if "m-003-T4-T3" in matches else 0
    with st.sidebar:
        st.markdown("## FIEL")
        st.caption("Verifiable match intelligence")
        match_id = st.selectbox("Synthetic match", matches, index=default)
        minute = st.slider("Replay minute", min_value=0, max_value=90, value=75, step=1)
        st.markdown("---")
        st.markdown("**Replay controls**")
        st.caption("Move the minute to update the score, tactical signals, event map and verified insight.")
        st.markdown("---")
        st.caption("No real clubs, players or proprietary match data are used.")

    match = load_match(match_id)
    truth = load_truth(match_id)
    render_header(match_id)
    render_scoreboard(match, truth, minute)

    match_tab, verifier_tab, truth_tab = st.tabs(
        ["⚡ Match Room", "✓ Verification Lab", "◎ Data & Ground Truth"]
    )
    with match_tab:
        render_match_room(match, truth, match_id, minute)
    with verifier_tab:
        render_verification_lab(match, truth)
    with truth_tab:
        render_ground_truth(match, truth)


if __name__ == "__main__":
    main()
