import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../services/api";
import type { ApprovalItem } from "../types";
import { CheckCircle2, XCircle } from "lucide-react";

export default function AdminPage() {
  const { t } = useTranslation();
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchApprovals = async () => {
    try { const data = await api.getApprovals(); setApprovals(data.items as ApprovalItem[]); }
    catch { /* ignore */ } finally { setLoading(false); }
  };

  useEffect(() => { fetchApprovals(); const interval = setInterval(fetchApprovals, 5000); return () => clearInterval(interval); }, []);

  const handleDecision = async (id: string, decision: string) => {
    try { await api.decideApproval(id, decision, decision === "approve" ? "同意" : "拒绝"); fetchApprovals(); }
    catch { alert(t("approvals.operationFailed")); }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-zinc-100">{t("approvals.title")}</h1>
      </div>
      <div className="bg-zinc-900 rounded-xl border border-zinc-800">
        <div className="px-5 py-3 border-b border-zinc-800">
          <h2 className="text-sm font-bold text-zinc-200">{t("approvals.pendingList")}</h2>
          <p className="text-[11px] text-zinc-500 mt-0.5">{t("approvals.pendingDesc")}</p>
        </div>
        {loading ? (
          <div className="p-8 text-center"><div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin mx-auto" /><p className="text-xs text-zinc-500 mt-2">{t("approvals.loading")}</p></div>
        ) : approvals.length === 0 ? (
          <div className="p-10 text-center"><CheckCircle2 className="w-8 h-8 text-emerald-500/50 mx-auto mb-2" /><p className="text-sm text-zinc-500">{t("approvals.noPending")}</p></div>
        ) : (
          <div className="divide-y divide-zinc-800/50">
            {approvals.map((item) => (
              <div key={item.id} className="px-5 py-3.5 flex items-center justify-between">
                <div className="flex-1 min-w-0 mr-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${item.risk_level === "high" ? "bg-red-950/50 text-red-400" : "bg-amber-950/50 text-amber-400"}`}>
                      {item.risk_level === "high" ? t("approvals.highRisk") : t("approvals.mediumRisk")}
                    </span>
                    <span className="text-[10px] text-zinc-600">{new Date(item.created_at).toLocaleString("zh-CN")}</span>
                  </div>
                  <p className="text-sm font-medium text-zinc-200 truncate">{item.action_description}</p>
                  <p className="text-[11px] text-zinc-500">{t("approvals.customer")}: {item.customer_id} · {t("approvals.agent")}: {item.agent_name}</p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button onClick={() => handleDecision(item.id, "approve")}
                    className="flex items-center gap-1 px-3 py-1.5 bg-emerald-600 text-white text-xs font-medium rounded-lg hover:bg-emerald-500 transition-colors cursor-pointer">
                    <CheckCircle2 className="w-3.5 h-3.5" />{t("approvals.approve")}
                  </button>
                  <button onClick={() => handleDecision(item.id, "reject")}
                    className="flex items-center gap-1 px-3 py-1.5 bg-zinc-800 text-zinc-300 text-xs font-medium rounded-lg border border-zinc-700 hover:bg-zinc-700 transition-colors cursor-pointer">
                    <XCircle className="w-3.5 h-3.5" />{t("approvals.reject")}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
