const API_BASE = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getApprovals: () => request<{ items: unknown[]; total: number }>("/admin/approvals"),

  decideApproval: (id: string, decision: string, comment = "") =>
    request(`/admin/approvals/${id}`, {
      method: "POST",
      body: JSON.stringify({ decision, comment }),
    }),

  takeoverConversation: (id: string, agentId: string, reason = "") =>
    request(`/admin/conversations/${id}/takeover`, {
      method: "POST",
      body: JSON.stringify({ agent_id: agentId, reason }),
    }),

  releaseConversation: (id: string) =>
    request(`/admin/conversations/${id}/release`, { method: "POST" }),

  healthCheck: () => request<{ status: string }>("/health"),
};
