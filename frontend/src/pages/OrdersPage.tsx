import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../services/api";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

interface Order { id: string; order_no: string; customer_id: string; status: string; total_amount: number; shipping_address: string; notes: string | null; items: Array<{ product_name: string; quantity: number; unit_price: number; subtotal: number }>; created_at: string; }

const statusStyles: Record<string, string> = {
  pending: "text-amber-400", processing: "text-sky-400", shipped: "text-violet-400", delivered: "text-emerald-400", cancelled: "text-red-400",
};

export function OrdersPage() {
  const { t } = useTranslation();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<Order | null>(null);

  useEffect(() => { loadOrders(); }, [page, status]);

  async function loadOrders() {
    try { setLoading(true); const data = await api.getOrders({ page, page_size: 20, status: status || undefined }); setOrders(data.items); setTotal(data.total); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function handleStatusChange(id: string, s: string) {
    try { await api.updateOrder(id, { status: s }); loadOrders(); } catch (e) { console.error(e); }
  }

  const opts = ["pending", "processing", "shipped", "delivered", "cancelled"];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-zinc-100">{t("orders.title")}</h1>
        <p className="text-xs text-zinc-500 mt-0.5">{t("orders.subtitle")}</p>
      </div>
      <div className="flex items-center gap-3 mb-4">
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="px-3 py-1.5 border border-zinc-800 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600/50 bg-zinc-900 text-zinc-300 cursor-pointer">
          <option value="">{t("orders.allStatus")}</option>
          {opts.map((s) => <option key={s} value={s}>{t(`orders.status${s.charAt(0).toUpperCase() + s.slice(1)}`)}</option>)}
        </select>
        <div className="flex-1" />
        <span className="text-[11px] text-zinc-500">{t("orders.totalOrders", { count: total })}</span>
      </div>
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" /></div> : (
          <table className="w-full">
            <thead><tr className="border-b border-zinc-800">
              {[t("orders.orderNo"), t("orders.customer"), t("orders.products"), t("orders.amount"), t("orders.status"), t("orders.time"), t("orders.actions")].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr></thead>
            <tbody className="divide-y divide-zinc-800/50">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="px-4 py-3"><button onClick={() => setSelected(o)} className="text-xs font-medium text-indigo-400 hover:underline cursor-pointer">{o.order_no}</button></td>
                  <td className="px-4 py-3 text-xs text-zinc-400">{o.customer_id}</td>
                  <td className="px-4 py-3 text-xs text-zinc-400">{o.items.map((i, idx) => <p key={idx}>{i.product_name} x{i.quantity}</p>)}</td>
                  <td className="px-4 py-3 text-xs font-semibold text-zinc-200">¥{o.total_amount.toLocaleString()}</td>
                  <td className="px-4 py-3"><span className={`text-[11px] font-medium ${statusStyles[o.status] || "text-zinc-400"}`}>{t(`orders.status${o.status.charAt(0).toUpperCase() + o.status.slice(1)}`)}</span></td>
                  <td className="px-4 py-3 text-[11px] text-zinc-500">{new Date(o.created_at).toLocaleDateString("zh-CN")}</td>
                  <td className="px-4 py-3">
                    <select value={o.status} onChange={(e) => handleStatusChange(o.id, e.target.value)}
                      className="px-2 py-1 border border-zinc-800 rounded text-[11px] focus:outline-none focus:ring-1 focus:ring-indigo-500/30 bg-zinc-800 text-zinc-300 cursor-pointer">
                      {opts.map((s) => <option key={s} value={s}>{t(`orders.status${s.charAt(0).toUpperCase() + s.slice(1)}`)}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="px-4 py-2.5 bg-zinc-950/50 border-t border-zinc-800 flex items-center justify-between">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
            className="flex items-center gap-1 px-3 py-1 text-xs text-zinc-400 border border-zinc-800 rounded-lg disabled:opacity-30 hover:bg-zinc-800 transition-colors cursor-pointer disabled:cursor-not-allowed"><ChevronLeft className="w-3 h-3" />{t("orders.prevPage")}</button>
          <span className="text-[11px] text-zinc-500">{t("orders.pageInfo", { current: page, total: Math.ceil(total / 20) })}</span>
          <button onClick={() => setPage(page + 1)} disabled={page * 20 >= total}
            className="flex items-center gap-1 px-3 py-1 text-xs text-zinc-400 border border-zinc-800 rounded-lg disabled:opacity-30 hover:bg-zinc-800 transition-colors cursor-pointer disabled:cursor-not-allowed">{t("orders.nextPage")}<ChevronRight className="w-3 h-3" /></button>
        </div>
      </div>
      {selected && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" onClick={() => setSelected(null)}>
          <div className="bg-zinc-900 rounded-xl max-w-lg w-full max-h-[80vh] overflow-y-auto border border-zinc-800 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="px-5 py-3 border-b border-zinc-800 flex items-center justify-between">
              <h2 className="text-sm font-bold text-zinc-100">{t("orders.orderDetail")}</h2>
              <button onClick={() => setSelected(null)} className="p-1 rounded hover:bg-zinc-800 cursor-pointer"><X className="w-4 h-4 text-zinc-500" /></button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {[["orders.orderNo", selected.order_no], ["orders.customer", selected.customer_id], ["orders.amount", `¥${selected.total_amount.toLocaleString()}`]].map(([k, v]) => (
                  <div key={k}><p className="text-[10px] text-zinc-500 mb-0.5">{t(k)}</p><p className="text-sm font-semibold text-zinc-100">{v}</p></div>
                ))}
                <div><p className="text-[10px] text-zinc-500 mb-0.5">{t("orders.status")}</p><span className={`text-[11px] font-medium ${statusStyles[selected.status]}`}>{t(`orders.status${selected.status.charAt(0).toUpperCase() + selected.status.slice(1)}`)}</span></div>
              </div>
              <div><p className="text-[10px] text-zinc-500 mb-1">{t("orders.shippingAddress")}</p><p className="text-xs text-zinc-300 p-2.5 bg-zinc-800/50 rounded-lg">{selected.shipping_address}</p></div>
              <div>
                <p className="text-[10px] text-zinc-500 mb-1.5">{t("orders.productDetail")}</p>
                <table className="w-full text-xs">
                  <thead><tr className="border-b border-zinc-800">{[t("orders.products"), t("orders.amount"), t("orders.quantity"), t("orders.subtotal")].map((h) => <th key={h} className="py-1.5 text-left text-[10px] font-semibold text-zinc-500">{h}</th>)}</tr></thead>
                  <tbody className="divide-y divide-zinc-800/50">{selected.items.map((i, idx) => (
                    <tr key={idx}><td className="py-1.5 text-zinc-300">{i.product_name}</td><td className="py-1.5 text-zinc-400">¥{i.unit_price.toLocaleString()}</td><td className="py-1.5 text-zinc-400">{i.quantity}</td><td className="py-1.5 font-semibold text-zinc-200">¥{i.subtotal.toLocaleString()}</td></tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
