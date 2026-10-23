// api.ts - small client for the FIEL API hosted on Azure App Service.
//
// The judge experience is "live-first, cached-fallback": every number is
// requested from the API, and if the free-tier app is cold or unreachable the
// page keeps working with the package captured from the same real Foundry run.
// The UI never invents a value: it is either from the API or from the cache,
// and it says which one.

export const API_BASE =
  (import.meta.env.VITE_FIEL_API as string | undefined)?.replace(/\/$/, "") ??
  "https://fiel-api-c3839e.azurewebsites.net";

export const FEATURED_MATCH = "m-003-T4-T3";

export type WinProbability = { A: number; draw: number; B: number };

export type MatchState = {
  match_id: string;
  minute: number;
  score: { A: number; B: number };
  xg: { A: number; B: number };
  win_probability: WinProbability;
};

export type Receipt = {
  claim: string;
  metric: string;
  value: number;
  team: "A" | "B";
  window_start: number;
  window_end: number;
  event_ids: string[];
  causal: boolean;
  confidence: number;
  baseline_value: number | null;
  baseline_match_ids: string[];
};

export type OnAirItem = {
  position: number;
  why_now: string;
  text: string;
  audience: string;
  language: string;
  personalization_verified: boolean;
  receipt: Receipt;
};

export type Broadcast = {
  match_id: string;
  audience: string;
  language: string;
  orchestration?: { framework: string; version: string; workflow: string };
  match_memory?: Record<"A" | "B", { team_code: string; matches: number; match_ids: string[]; metrics: Record<string, number> }>;
  on_air: OnAirItem[];
};

export type MatchEvent = {
  id: string;
  minute: number;
  second: number;
  type: string;
  team: "A" | "B";
  player: string;
  x: number;
  y: number;
  outcome: string;
};

async function getJson<T>(path: string, timeoutMs = 8000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE}${path}`, { signal: controller.signal });
    if (!response.ok) throw new Error(`${path} -> HTTP ${response.status}`);
    return (await response.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  health: () => getJson<{ status: string; matches: number }>("/health", 15000),
  state: (matchId: string, minute: number) =>
    getJson<MatchState>(`/matches/${matchId}/state?minute=${minute}`),
  broadcast: (matchId: string) => getJson<Broadcast>(`/matches/${matchId}/broadcast`),
  events: (matchId: string, ids: string[]) =>
    getJson<MatchEvent[]>(`/matches/${matchId}/events?ids=${ids.join(",")}`),
};

export const pct = (value: number) => Math.round(value * 100);
