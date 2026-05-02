import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../services/api";
import type { ApprovalItem } from "../types";
import { CheckCircle2, XCircle } from "lucide-react";

export default function AdminPage() {
  const { t } = useTranslation();
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchApprovals = async () => { try { const d = await api.getApprovals(); setApprovals(d.items as ApprovalItem[]); } catch {} finally { setLoading(false); } };
  useEffect(() => { fetchApprovals(); const i = setInterval(fetchApprovals, 5000); return () => clearInterval(i); }, []);
  const handleDecision = async (id: string, decision: string) => { try { await api.decideApproval(id, decision, decision === "approve" ? "同意" : "拒绝"); fetchApprovals(); } catch { alert(t("approvals.operationFailed")); } };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-5"><h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{t("approvals.title")}</h1></div>
      <div className="rounded-xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
        <div className="px-5 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
          <h2 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>{t("approvals.pendingList")}</h2>
          <p className="text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>{t("approvals.pendingDesc")}</p>
        </div>
        {loading ? <div className="p-8 text-center"><div className="w-6 h-6 border-2 rounded-full animate-spin mx-auto" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /><p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>{t("approvals.loading")}</p></div>
        : approvals.length === 0 ? <div className="p-10 text-center"><CheckCircle2 className="w-8 h-8 mx-auto mb-2" style={{ color: "var(--success)", opacity: 0.5 }} /><p className="text-sm" style={{ color: "var(--text-muted)" }}>{t("approvals.noPending")}</p></div>
        : <div>{approvals.map((item) => (
          <div key={item.id} className="px-5 py-3.5 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <div className="flex-1 min-w-0 mr-4">
              <div className="flex items-center gap-2 mb-1">
                <span className="px-1.5 py-0.5 text-[10px] font-medium rounded" style={{ background: item.risk_level === "high" ? "rgba(239,68,68,0.1)" : "rgba(245,158,11,0.1)", color: item.risk_level === "high" ? "var(--error)" : "var(--warning)" }}>{item.risk_level === "high" ? t("approvals.highRisk") : t("approvals.mediumRisk")}</span>
                <span className="text-[10px]" style={{ color: "var(--text-dim)" }}>{new Date(item.created_at).toLocaleString("zh-CN")}</span>
              </div>
              <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>{item.action_description}</p>
              <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>{t("approvals.customer")}: {item.customer_id} · {t("approvals.agent")}: {item.agent_name}</p>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <button onClick={() => handleDecision(item.id, "approve")} className="flex items-center gap-1 px-3 py-1.5 text-white text-xs font-medium rounded-lg cursor-pointer transition-colors" style={{ background: "var(--success)" }}><CheckCircle2 className="w-3.5 h-3.5" />{t("approvals.approve")}</button>
              <button onClick={() => handleDecision(item.id, "reject")} className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg cursor-pointer transition-colors" style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}><XCircle className="w-3.5 h-3.5" />{t("approvals.reject")}</button>
            </div>
          </div>
        ))}</div>}
      </div>
    </div>
  );
}
