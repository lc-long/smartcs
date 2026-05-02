import { useEffect, useState } from "react";
import { api } from "../services/api";
import { ChevronLeft, ChevronRight, CheckCircle2, XCircle, Clock } from "lucide-react";

interface Refund { id: string; refund_no: string; order_id: string; customer_id: string; amount: number; reason: string; status: string; approved_by: string | null; created_at: string; }

const statusColors: Record<string, string> = { pending: "text-amber-400", approved: "text-emerald-400", rejected: "text-red-400" };
const statusLabels: Record<string, string> = { pending: "待审批", approved: "已批准", rejected: "已拒绝" };

export function RefundsPage() {
  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");

  useEffect(() => { loadRefunds(); }, [page, status]);

  async function loadRefunds() {
    try { setLoading(true); const data = await api.getRefunds({ page, page_size: 20, status: status || undefined }); setRefunds(data.items); setTotal(data.total); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function handleApprove(id: string) {
    if (!confirm("确定批准此退款申请？")) return;
    try { await api.approveRefund(id); loadRefunds(); } catch (e) { console.error(e); }
  }

  async function handleReject(id: string) {
    const reason = prompt("请输入拒绝原因：");
    if (reason === null) return;
    try { await api.rejectRefund(id, reason); loadRefunds(); } catch (e) { console.error(e); }
  }

  const pending = refunds.filter((r) => r.status === "pending").length;
  const approved = refunds.filter((r) => r.status === "approved").length;
  const rejected = refunds.filter((r) => r.status === "rejected").length;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-zinc-100">退款管理</h1>
        <p className="text-xs text-zinc-500 mt-0.5">审批和管理退款申请</p>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { label: "待审批", value: pending, icon: Clock, color: "text-amber-400" },
          { label: "已批准", value: approved, icon: CheckCircle2, color: "text-emerald-400" },
          { label: "已拒绝", value: rejected, icon: XCircle, color: "text-red-400" },
        ].map((c) => (
          <div key={c.label} className="bg-zinc-900 rounded-xl border border-zinc-800 p-3">
            <div className="flex items-center gap-2"><c.icon className="w-3.5 h-3.5 text-zinc-500" /><p className="text-[10px] text-zinc-500">{c.label}</p></div>
            <p className={`text-lg font-bold mt-1 ${c.color}`}>{c.value}</p>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3 mb-4">
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="px-3 py-1.5 border border-zinc-800 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600/50 bg-zinc-900 text-zinc-300 cursor-pointer">
          <option value="">所有状态</option>
          <option value="pending">待审批</option>
          <option value="approved">已批准</option>
          <option value="rejected">已拒绝</option>
        </select>
        <div className="flex-1" />
        <span className="text-[11px] text-zinc-500">共 {total} 条退款记录</span>
      </div>

      <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" /></div>
        : refunds.length === 0 ? <div className="p-10 text-center text-zinc-500 text-sm">暂无退款记录</div> : (
          <table className="w-full">
            <thead><tr className="border-b border-zinc-800">
              {["退款单号", "订单号", "客户", "金额", "原因", "状态", "时间", "操作"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr></thead>
            <tbody className="divide-y divide-zinc-800/50">
              {refunds.map((r) => (
                <tr key={r.id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="px-4 py-3 text-xs font-medium text-zinc-200">{r.refund_no}</td>
                  <td className="px-4 py-3 text-xs text-zinc-400">{r.order_id}</td>
                  <td className="px-4 py-3 text-xs text-zinc-400">{r.customer_id}</td>
                  <td className="px-4 py-3 text-xs font-semibold text-zinc-200">¥{r.amount.toLocaleString()}</td>
                  <td className="px-4 py-3 text-xs text-zinc-400 truncate max-w-[150px]">{r.reason}</td>
                  <td className="px-4 py-3"><span className={`text-[11px] font-medium ${statusColors[r.status]}`}>{statusLabels[r.status]}</span></td>
                  <td className="px-4 py-3 text-[11px] text-zinc-500">{new Date(r.created_at).toLocaleDateString("zh-CN")}</td>
                  <td className="px-4 py-3">
                    {r.status === "pending" ? (
                      <div className="flex gap-1.5">
                        <button onClick={() => handleApprove(r.id)} className="px-2 py-1 bg-emerald-600 text-white text-[11px] rounded hover:bg-emerald-500 cursor-pointer transition-colors">批准</button>
                        <button onClick={() => handleReject(r.id)} className="px-2 py-1 bg-zinc-800 text-zinc-300 text-[11px] rounded border border-zinc-700 hover:bg-zinc-700 cursor-pointer transition-colors">拒绝</button>
                      </div>
                    ) : r.approved_by ? <span className="text-[11px] text-zinc-500">{r.approved_by}</span> : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="px-4 py-2.5 bg-zinc-950/50 border-t border-zinc-800 flex items-center justify-between">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
            className="flex items-center gap-1 px-3 py-1 text-xs text-zinc-400 border border-zinc-800 rounded-lg disabled:opacity-30 hover:bg-zinc-800 transition-colors cursor-pointer disabled:cursor-not-allowed"><ChevronLeft className="w-3 h-3" />上一页</button>
          <span className="text-[11px] text-zinc-500">第 {page} 页，共 {Math.ceil(total / 20)} 页</span>
          <button onClick={() => setPage(page + 1)} disabled={page * 20 >= total}
            className="flex items-center gap-1 px-3 py-1 text-xs text-zinc-400 border border-zinc-800 rounded-lg disabled:opacity-30 hover:bg-zinc-800 transition-colors cursor-pointer disabled:cursor-not-allowed">下一页<ChevronRight className="w-3 h-3" /></button>
        </div>
      </div>
    </div>
  );
}
