const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Goal submission ───────────────────────────────────────────────────────────

export async function submitGoal(goal: string, token: string) {
  const res = await fetch(`${API_URL}/api/tasks/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ goal }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Failed to submit goal (${res.status})`);
  }
  return res.json();
}

// ── Session ───────────────────────────────────────────────────────────────────

export async function getSessionStatus(sessionId: string, token: string) {
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Session not found (${res.status})`);
  return res.json();
}

export async function getSessionOutput(sessionId: string, token: string) {
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}/output`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Output not ready (${res.status})`);
  return res.json();
}

export async function deleteSession(sessionId: string, token: string) {
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Delete failed (${res.status})`);
  return res.json();
}

// ── Agent registry ────────────────────────────────────────────────────────────

export async function listAgents(token: string) {
  const res = await fetch(`${API_URL}/api/agents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Could not fetch agents (${res.status})`);
  return res.json();
}

// ── SSE stream URL builder ────────────────────────────────────────────────────
// The backend stream endpoint reads auth from ?token= because browsers
// cannot set custom headers on native EventSource connections.

export function buildStreamUrl(sessionId: string, token: string): string {
  return `${API_URL}/api/stream/${sessionId}?token=${encodeURIComponent(token)}`;
}
