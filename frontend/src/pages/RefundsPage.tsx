import { useEffect, useState } from "react";
import { api } from "../services/api";
import { ChevronLeft, ChevronRight, CheckCircle2, XCircle, Clock } from "lucide-react";

interface Refund { id: string; refund_no: string; order_id: string; customer_id: string; amount: number; reason: string; status: string; approved_by: string | null; created_at: string; }
const statusColors: Record<string, string> = { pending: "var(--warning)", approved: "var(--success)", rejected: "var(--error)" };
const statusLabels: Record<string, string> = { pending: "待审批", approved: "已批准", rejected: "已拒绝" };

export function RefundsPage() {
  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");

  useEffect(() => { loadRefunds(); }, [page, status]);
  async function loadRefunds() { try { setLoading(true); const d = await api.getRefunds({ page, page_size: 20, status: status || undefined }); setRefunds(d.items); setTotal(d.total); } catch (e) { console.error(e); } finally { setLoading(false); } }
  async function handleApprove(id: string) { if (!confirm("确定批准此退款申请？")) return; try { await api.approveRefund(id); loadRefunds(); } catch (e) { console.error(e); } }
  async function handleReject(id: string) { const reason = prompt("请输入拒绝原因："); if (reason === null) return; try { await api.rejectRefund(id, reason); loadRefunds(); } catch (e) { console.error(e); } }

  const pending = refunds.filter((r) => r.status === "pending").length;
  const approved = refunds.filter((r) => r.status === "approved").length;
  const rejected = refunds.filter((r) => r.status === "rejected").length;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5"><h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>退款管理</h1><p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>审批和管理退款申请</p></div>
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[{ l: "待审批", v: pending, i: Clock, c: "var(--warning)" }, { l: "已批准", v: approved, i: CheckCircle2, c: "var(--success)" }, { l: "已拒绝", v: rejected, i: XCircle, c: "var(--error)" }].map((c) => (
          <div key={c.l} className="rounded-xl p-3" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
            <div className="flex items-center gap-2"><c.i className="w-3.5 h-3.5" style={{ color: "var(--text-dim)" }} /><p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{c.l}</p></div>
            <p className="text-lg font-bold mt-1" style={{ color: c.c }}>{c.v}</p>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-3 mb-4">
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-lg text-xs focus:outline-none cursor-pointer" style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-secondary)" }}>
          <option value="">所有状态</option><option value="pending">待审批</option><option value="approved">已批准</option><option value="rejected">已拒绝</option>
        </select>
        <div className="flex-1" /><span className="text-[11px]" style={{ color: "var(--text-muted)" }}>共 {total} 条退款记录</span>
      </div>
      <div className="rounded-xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /></div>
        : refunds.length === 0 ? <div className="p-10 text-center text-sm" style={{ color: "var(--text-muted)" }}>暂无退款记录</div> : (
          <table className="w-full">
            <thead><tr style={{ borderBottom: "1px solid var(--border)" }}>{["退款单号", "订单号", "客户", "金额", "原因", "状态", "时间", "操作"].map((h) => <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{h}</th>)}</tr></thead>
            <tbody>{refunds.map((r) => (
              <tr key={r.id} className="transition-colors" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td className="px-4 py-3 text-xs font-medium" style={{ color: "var(--text-primary)" }}>{r.refund_no}</td>
                <td className="px-4 py-3 text-xs" style={{ color: "var(--text-secondary)" }}>{r.order_id}</td>
                <td className="px-4 py-3 text-xs" style={{ color: "var(--text-secondary)" }}>{r.customer_id}</td>
                <td className="px-4 py-3 text-xs font-semibold" style={{ color: "var(--text-primary)" }}>¥{r.amount.toLocaleString()}</td>
                <td className="px-4 py-3 text-xs truncate max-w-[150px]" style={{ color: "var(--text-secondary)" }}>{r.reason}</td>
                <td className="px-4 py-3"><span className="text-[11px] font-medium" style={{ color: statusColors[r.status] }}>{statusLabels[r.status]}</span></td>
                <td className="px-4 py-3 text-[11px]" style={{ color: "var(--text-muted)" }}>{new Date(r.created_at).toLocaleDateString("zh-CN")}</td>
                <td className="px-4 py-3">{r.status === "pending" ? <div className="flex gap-1.5">
                  <button onClick={() => handleApprove(r.id)} className="px-2 py-1 text-white text-[11px] rounded cursor-pointer transition-colors" style={{ background: "var(--success)" }}>批准</button>
                  <button onClick={() => handleReject(r.id)} className="px-2 py-1 text-[11px] rounded cursor-pointer transition-colors" style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}>拒绝</button>
                </div> : r.approved_by ? <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{r.approved_by}</span> : null}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
        <div className="px-4 py-2.5 flex items-center justify-between" style={{ background: "var(--bg-app)", borderTop: "1px solid var(--border)" }}>
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="flex items-center gap-1 px-3 py-1 text-xs rounded-lg disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed" style={{ color: "var(--text-secondary)", border: "1px solid var(--border)" }}><ChevronLeft className="w-3 h-3" />上一页</button>
          <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>第 {page} 页，共 {Math.ceil(total / 20)} 页</span>
          <button onClick={() => setPage(page + 1)} disabled={page * 20 >= total} className="flex items-center gap-1 px-3 py-1 text-xs rounded-lg disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed" style={{ color: "var(--text-secondary)", border: "1px solid var(--border)" }}>下一页<ChevronRight className="w-3 h-3" /></button>
        </div>
      </div>
    </div>
  );
}
