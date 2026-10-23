import { useEffect, useMemo, useState } from "react";
import { api, API_BASE, FEATURED_MATCH, pct, type Broadcast, type MatchEvent, type MatchState } from "./api";

type Source = "connecting" | "live" | "cached";

// Fallback values = the same seeded engine (GET /state, 2,000 runs), copied on 23 Oct.
const checkpoints = [
  { minute: 15, a: 40, draw: 29, b: 32, score: "0 — 0", note: "Opening phase: balanced territory, no verified swing yet." },
  { minute: 30, a: 32, draw: 27, b: 41, score: "0 — 0", note: "Team B is beginning to control the match." },
  { minute: 45, a: 10, draw: 20, b: 70, score: "0 — 1", note: "Team B reaches half-time with a decisive predictive edge." },
  { minute: 59, a: 7, draw: 21, b: 72, score: "0 — 1", note: "Before the swing, Team B remains the clear favourite." },
  { minute: 69, a: 73, draw: 22, b: 6, score: "2 — 1", note: "Two goals flip the outlook: Team A moves from 7% to 73%." },
  { minute: 79, a: 84, draw: 14, b: 2, score: "2 — 1", note: "Team B holds 78% possession, but Team A protects the lead." },
  { minute: 90, a: 100, draw: 0, b: 0, score: "3 — 1", note: "Full time. The final package remains linked to every event receipt." },
];

const tabs = ["Match Room", "Agent Desk", "Verification Lab", "Ground Truth"] as const;
type Tab = (typeof tabs)[number];

function Pipeline() {
  const stages = [
    ["01", "Explainer", "Foundry proposes one evidence-bound claim"],
    ["02", "Verifier", "Python recomputes value, window and event IDs"],
    ["03", "Producer", "Only approved claims enter the rundown"],
    ["04", "Personalizer", "Analyst/fan · English/Portuguese"],
  ];
  return (
    <div className="pipeline" aria-label="Agent pipeline">
      {stages.map(([number, name, copy], index) => (
        <div className="pipeline-step" key={name}>
          <div className="step-top"><span>{number}</span><i>{index === 1 ? "RULES" : "AGENT"}</i></div>
          <strong>{name}</strong>
          <p>{copy}</p>
        </div>
      ))}
    </div>
  );
}

// The cached package is the real Foundry run saved in data/demo_agents.json.
// It is what the page shows when the free-tier API has not answered yet.
const cachedOnAir = {
  text: "Entre 69' e 79' o time B teve 78.0% de posse, muito acima dos habituais 61.63%.",
  why_now: "Shows a sustained possession surge above the team's usual level, signalling a clear shift in control.",
  metric: "possession_pct", value: "78.0%", window: "69'—79'", evidence: "85 event IDs",
  baseline: "61.63%", history: "2 match IDs", memoryMatches: "m-004-T4-T3 and m-006-T1-T3",
};

export default function Home() {
  const [minute, setMinute] = useState(69);
  const [tab, setTab] = useState<Tab>("Match Room");
  const [source, setSource] = useState<Source>("connecting");
  const [state, setState] = useState<MatchState | null>(null);
  const [finalState, setFinalState] = useState<MatchState | null>(null);
  const [broadcast, setBroadcast] = useState<Broadcast | null>(null);
  const [receiptEvents, setReceiptEvents] = useState<MatchEvent[] | null>(null);
  const [receiptOpen, setReceiptOpen] = useState(false);

  // Narrative note for the nearest checkpoint; numbers come from the API when live.
  const point = useMemo(
    () => checkpoints.reduce((best, current) => current.minute <= minute ? current : best, checkpoints[0]),
    [minute],
  );

  // 1. Connect once: health, full-time state and the cached Foundry package.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await api.health();
        const [full, pack] = await Promise.all([api.state(FEATURED_MATCH, 90), api.broadcast(FEATURED_MATCH)]);
        if (cancelled) return;
        setFinalState(full);
        setBroadcast(pack.on_air?.length ? pack : null);
        setSource("live");
      } catch {
        if (!cancelled) setSource("cached");
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // 2. Every slider move asks the engine for that minute (debounced).
  useEffect(() => {
    if (source !== "live") return;
    const timer = setTimeout(() => {
      api.state(FEATURED_MATCH, minute).then(setState).catch(() => setSource("cached"));
    }, 180);
    return () => clearTimeout(timer);
  }, [minute, source]);

  const live = source === "live" && state !== null && state.minute === minute;
  const probA = live ? pct(state.win_probability.A) : point.a;
  const probDraw = live ? pct(state.win_probability.draw) : point.draw;
  const probB = live ? pct(state.win_probability.B) : point.b;
  const score = live ? `${state.score.A} — ${state.score.B}` : point.score;
  const finalXg = finalState ? `${finalState.xg.A.toFixed(2)} — ${finalState.xg.B.toFixed(2)}` : "2.82 — 1.89";
  const finalScore = finalState ? `${finalState.score.A} — ${finalState.score.B}` : "3 — 1";
  const onAir = broadcast?.on_air[0] ?? null;
  const memoryB = broadcast?.match_memory?.B ?? null;

  // 3. The receipt is clickable: fetch the exact events behind the claim.
  async function toggleReceipt() {
    if (!onAir) return;
    if (receiptOpen) { setReceiptOpen(false); return; }
    setReceiptOpen(true);
    if (receiptEvents === null) {
      try { setReceiptEvents(await api.events(FEATURED_MATCH, onAir.receipt.event_ids)); }
      catch { setReceiptEvents([]); }
    }
  }

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="FIEL home">
          <span className="brand-mark">F</span>
          <span>FIEL</span>
          <small>FOOTBALL INTELLIGENCE ENGINE, LIVE</small>
        </a>
        <nav aria-label="Main navigation">
          <a href="#experience">Experience</a>
          <a href="#architecture">Architecture</a>
          <a href="#evidence">Evidence</a>
          <a href="https://fiel-api-c3839e.azurewebsites.net/docs" target="_blank" rel="noreferrer">Live API</a>
        </nav>
        <a className="source-link" href="https://github.com/Lmg15186/fiel" target="_blank" rel="noreferrer">View source ↗</a>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <div className="eyebrow"><span className="live-dot" /> SYNTHETIC MATCH · LIVE INTELLIGENCE</div>
          <h1>Every sentence on air comes with a <em>receipt.</em></h1>
          <p className="hero-lede">FIEL turns thousands of synthetic football events into predictive, multilingual match stories — then independently verifies every number before broadcast.</p>
          <div className="hero-actions">
            <a className="primary-cta" href="#experience">Enter the Match Room <span>↓</span></a>
            <div className="built-with"><span>BUILT WITH</span><b>Microsoft Foundry</b><b>Agent Framework</b></div>
          </div>
        </div>

        <div className="broadcast-shell" aria-label="Interactive match console">
          <div className="console-head">
            <span><i className="live-dot" /> LIVE REPLAY</span>
            <span className={`source-pill ${source}`} title={`${API_BASE}`}>
              {source === "live" ? "LIVE API · AZURE APP SERVICE" : source === "connecting" ? "CONNECTING TO AZURE API…" : "CACHED PACKAGE · API ASLEEP"}
            </span>
            <code>{FEATURED_MATCH}</code>
          </div>
          <div className="score-row">
            <div className="team"><span>A</span><strong>TEAM A</strong><small>DIRECT PLAY</small></div>
            <div className="score"><b>{score}</b><span>{minute}&apos;</span></div>
            <div className="team team-right"><span>B</span><strong>TEAM B</strong><small>POSSESSION</small></div>
          </div>
          <div className="timeline-wrap">
            <div className="timeline-label"><span>MATCH MINUTE</span><b>{minute}&apos;</b></div>
            <input aria-label="Match minute" type="range" min="15" max="90" value={minute} onChange={(event) => setMinute(Number(event.target.value))} />
            <div className="timeline-ticks"><span>15&apos;</span><span>45&apos;</span><span>59&apos;</span><span>69&apos;</span><span>90&apos;</span></div>
          </div>
          <div className="probability-card">
            <div className="panel-label">PREDICTIVE MATCH OUTLOOK</div>
            <div className="probability-values"><b>{probA}% <small>TEAM A</small></b><span>{probDraw}% DRAW</span><b><small>TEAM B</small> {probB}%</b></div>
            <div className="probability-bar" aria-label={`Team A ${probA}%, draw ${probDraw}%, Team B ${probB}%`}>
              <i style={{ width: `${probA}%` }} /><i style={{ width: `${probDraw}%` }} /><i style={{ width: `${probB}%` }} />
            </div>
            <p>{point.note}</p>
          </div>
          <div className="verified-ribbon"><span>✓ VERIFIED</span><p>{source === "live" ? `Computed on request by GET /matches/${FEATURED_MATCH}/state?minute=${minute} — seeded Monte Carlo, reproducible from the synthetic event stream.` : "All probabilities are reproducible from the synthetic event stream."}</p></div>
        </div>
      </section>

      <section className="proof-strip" aria-label="Project proof points">
        <div><b>1,078</b><span>events in featured match</span></div>
        <div><b>4</b><span>specialised workflow stages</span></div>
        <div><b>47 / 47</b><span>automated tests passing</span></div>
        <div><b>0</b><span>real clubs or proprietary feeds</span></div>
      </section>

      <section className="experience" id="experience">
        <div className="section-intro">
          <span className="kicker">THE PRODUCT</span>
          <h2>From raw events to a story a producer can trust.</h2>
          <p>Numbers come straight from the FIEL API on Azure; the on-air package is the stored result of a real Microsoft Foundry run. No credentials or new model calls are required here.</p>
        </div>
        <div className="tab-list" role="tablist" aria-label="FIEL product views">
          {tabs.map((item, index) => <button key={item} role="tab" aria-selected={tab === item} onClick={() => setTab(item)}><span>0{index + 1}</span>{item}</button>)}
        </div>

        <div className="tab-panel" role="tabpanel">
          {tab === "Match Room" && (
            <div className="match-grid">
              <div className="match-story">
                <div className="panel-label">THE MOMENT THAT CHANGED THE MATCH</div>
                <h3>From 7% to 73% in ten minutes.</h3>
                <p>Move the match control above between 59&apos; and 69&apos;. Two goals reverse the predictive outlook while the evidence trail stays intact.</p>
                <div className="swing">
                  <div><span>59&apos;</span><b>07%</b><small>Team A win</small></div>
                  <i>→</i>
                  <div className="swing-after"><span>69&apos;</span><b>73%</b><small>Team A win</small></div>
                </div>
              </div>
              <div className="metric-stack">
                <div className="metric"><span>FINAL xG</span><b>{finalXg}</b><small>transparent shot model{finalState ? " · from API" : ""}</small></div>
                <div className="metric"><span>FINAL SCORE</span><b>{finalScore}</b><small>Team A comeback</small></div>
                <div className="metric accent"><span>MODEL</span><b>Monte Carlo</b><small>Poisson outlook · 2,000 seeded runs</small></div>
              </div>
            </div>
          )}

          {tab === "Agent Desk" && (
            <div>
              <div className="framework-banner"><span>MICROSOFT AGENT FRAMEWORK 1.23</span><b>ExplainerVerifier → Producer → Personalizer</b><i>REAL CACHED RUN</i></div>
              <Pipeline />
              <div className="agent-output">
                <div className="on-air">
                  <span className="on-air-label"><i className="live-dot" /> ON AIR · {(onAir?.audience ?? "fan").toUpperCase()} / {(onAir?.language ?? "pt").toUpperCase()}</span>
                  <blockquote>“{onAir ? onAir.text : cachedOnAir.text}”</blockquote>
                  <p>{onAir ? onAir.why_now : cachedOnAir.why_now}</p>
                  <p className="source-note">{onAir ? `Served by GET /matches/${FEATURED_MATCH}/broadcast — the real Foundry run, stored, not regenerated.` : "Cached copy of the real Foundry run (data/demo_agents.json)."}</p>
                </div>
                <div className="receipt">
                  <div className="receipt-head"><span>VERIFIABLE RECEIPT</span><b>{onAir && !onAir.personalization_verified ? "✕ NOT VERIFIED" : "✓ RE-VERIFIED"}</b></div>
                  <dl>
                    <div><dt>METRIC</dt><dd>{onAir ? onAir.receipt.metric : cachedOnAir.metric}</dd></div>
                    <div><dt>VALUE</dt><dd>{onAir ? `${onAir.receipt.value}%` : cachedOnAir.value}</dd></div>
                    <div><dt>WINDOW</dt><dd>{onAir ? `${onAir.receipt.window_start}'—${onAir.receipt.window_end}'` : cachedOnAir.window}</dd></div>
                    <div><dt>EVIDENCE</dt><dd>{onAir ? `${onAir.receipt.event_ids.length} event IDs` : cachedOnAir.evidence}</dd></div>
                    <div><dt>BASELINE</dt><dd>{onAir ? `${onAir.receipt.baseline_value ?? "—"}%` : cachedOnAir.baseline}</dd></div>
                    <div><dt>HISTORY</dt><dd>{onAir ? `${onAir.receipt.baseline_match_ids.length} match IDs` : cachedOnAir.history}</dd></div>
                  </dl>
                  <button className="receipt-button" type="button" onClick={toggleReceipt} disabled={!onAir}>
                    {!onAir ? "Open the events (needs the live API)" : receiptOpen ? "Hide the events" : "Open the events behind this receipt ↓"}
                  </button>
                  {receiptOpen && (
                    <ol className="receipt-events" aria-label="Events cited by the receipt">
                      {receiptEvents === null && <li className="muted">Loading events from the API…</li>}
                      {receiptEvents?.length === 0 && <li className="muted">The API did not return the events.</li>}
                      {receiptEvents?.slice(0, 12).map((event) => (
                        <li key={event.id}><code>{event.id}</code> {event.minute}&apos;{String(event.second).padStart(2, "0")} · Team {event.team} · {event.type} · {event.outcome}</li>
                      ))}
                      {receiptEvents && receiptEvents.length > 12 && <li className="muted">… and {receiptEvents.length - 12} more, all inside {onAir?.receipt.window_start}&apos;—{onAir?.receipt.window_end}&apos;.</li>}
                    </ol>
                  )}
                </div>
              </div>
              <div className="memory-row"><span>MATCH MEMORY</span><p><b>Team B · {memoryB?.team_code ?? "T3"}</b> usual possession from {memoryB ? memoryB.match_ids.join(" and ") : cachedOnAir.memoryMatches} (current match excluded)</p><strong>{memoryB?.metrics?.possession_pct !== undefined ? `${memoryB.metrics.possession_pct}%` : cachedOnAir.baseline}</strong></div>
            </div>
          )}

          {tab === "Verification Lab" && (
            <div className="verification-grid">
              <div className="claim rejected"><span>01 · CANDIDATE CLAIM</span><h3>“The substitution at 69&apos; won the game for team B.”</h3><div>✕ REJECTED</div><p>Unsupported causal language. The receipt contains only two events and cannot establish that the substitution caused the result.</p></div>
              <div className="rewrite-arrow"><span>PRECISE REASONS</span><b>→</b><span>BOUNDED REWRITE</span></div>
              <div className="claim accepted"><span>02 · EVIDENCE-SAFE CLAIM</span><h3>“Between 69&apos; and 79&apos;, team B&apos;s recovery height was 59.5.”</h3><div>✓ ON AIR</div><p>Value recomputed · window valid · evidence IDs found · language is causally safe.</p></div>
            </div>
          )}

          {tab === "Ground Truth" && (
            <div className="evaluation" id="evidence">
              <div className="eval-copy"><span className="kicker">REPRODUCIBLE EVALUATION</span><h3>We generate the match, so we know which stories were planted.</h3><p>Thirty seeded matches test deterministic story signals and verifier guardrails. The scope is deliberately honest: these numbers do not claim to measure subjective language-model quality.</p></div>
              <div className="eval-numbers"><div><b>49 / 49</b><span>planted signals detected</span></div><div><b>49 / 49</b><span>unsafe causal claims rejected</span></div><div><b>49 / 49</b><span>safe corrections accepted</span></div><div><b>3.95 ms</b><span>mean processing / match</span></div></div>
            </div>
          )}
        </div>
      </section>

      <section className="architecture" id="architecture">
        <div className="section-intro compact"><span className="kicker">WHY THIS ARCHITECTURE</span><h2>AI chooses the story. Code decides whether it is true.</h2></div>
        <div className="architecture-grid">
          <div className="lane live-lane"><span>LIVE / REPLAY LANE</span><h3>Seconds matter.</h3><p>Event stream → tactics engine → Agent Framework → deterministic gate → broadcast package.</p><div className="lane-flow"><b>EVENTS</b><i>›</i><b>TACTICS</b><i>›</i><b>AGENTS</b><i>›</i><b>VERIFY</b></div></div>
          <div className="lane batch-lane"><span>BATCH EVIDENCE LANE</span><h3>History can wait.</h3><p>Match Memory and evaluation run in batch. No Kafka or Spark where the workload does not need them.</p><div className="lane-flow"><b>HISTORY</b><i>›</i><b>MEMORY</b><i>›</i><b>GROUND TRUTH</b></div></div>
        </div>
        <div className="tech-row"><span>MICROSOFT FOUNDRY</span><span>AGENT FRAMEWORK</span><span>MCP SERVER</span><span>AZURE APP SERVICE</span><span>FASTAPI</span><span>PYDANTIC</span><span>GITHUB</span></div>
      </section>

      <section className="closing">
        <div><span className="kicker">FIEL</span><h2>Trust is not a disclaimer.<br />It is the product.</h2></div>
        <div><p>Built for Microsoft × Premier League<br />Inside the Game: Developer Hackathon</p><a href="https://github.com/Lmg15186/fiel" target="_blank" rel="noreferrer">Explore the repository ↗</a></div>
      </section>

      <footer><span>FIEL · FICTIONAL TEAMS · SYNTHETIC DATA</span><span>NO CLUB MARKS · NO PROPRIETARY FEEDS</span><span>SYDNEY · 2026</span></footer>
    </main>
  );
}
