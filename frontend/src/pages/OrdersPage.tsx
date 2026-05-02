import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../services/api";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

interface Order { id: string; order_no: string; customer_id: string; status: string; total_amount: number; shipping_address: string; notes: string | null; items: Array<{ product_name: string; quantity: number; unit_price: number; subtotal: number }>; created_at: string; }

const statusColors: Record<string, string> = { pending: "var(--warning)", processing: "var(--accent)", shipped: "#8B5CF6", delivered: "var(--success)", cancelled: "var(--error)" };

export function OrdersPage() {
  const { t } = useTranslation();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<Order | null>(null);

  useEffect(() => { loadOrders(); }, [page, status]);
  async function loadOrders() { try { setLoading(true); const d = await api.getOrders({ page, page_size: 20, status: status || undefined }); setOrders(d.items); setTotal(d.total); } catch (e) { console.error(e); } finally { setLoading(false); } }
  async function handleStatusChange(id: string, s: string) { try { await api.updateOrder(id, { status: s }); loadOrders(); } catch (e) { console.error(e); } }

  const opts = ["pending", "processing", "shipped", "delivered", "cancelled"];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5"><h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{t("orders.title")}</h1><p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{t("orders.subtitle")}</p></div>
      <div className="flex items-center gap-3 mb-4">
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-lg text-xs focus:outline-none focus:ring-2 cursor-pointer" style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-secondary)" }}>
          <option value="">{t("orders.allStatus")}</option>
          {opts.map((s) => <option key={s} value={s}>{t(`orders.status${s.charAt(0).toUpperCase() + s.slice(1)}`)}</option>)}
        </select>
        <div className="flex-1" /><span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{t("orders.totalOrders", { count: total })}</span>
      </div>
      <div className="rounded-xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /></div> : (
          <table className="w-full">
            <thead><tr style={{ borderBottom: "1px solid var(--border)" }}>
              {[t("orders.orderNo"), t("orders.customer"), t("orders.products"), t("orders.amount"), t("orders.status"), t("orders.time"), t("orders.actions")].map((h) => <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{h}</th>)}
            </tr></thead>
            <tbody>{orders.map((o) => (
              <tr key={o.id} className="transition-colors" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td className="px-4 py-3"><button onClick={() => setSelected(o)} className="text-xs font-medium cursor-pointer" style={{ color: "var(--accent)" }}>{o.order_no}</button></td>
                <td className="px-4 py-3 text-xs" style={{ color: "var(--text-secondary)" }}>{o.customer_id}</td>
                <td className="px-4 py-3 text-xs" style={{ color: "var(--text-secondary)" }}>{o.items.map((i, idx) => <p key={idx}>{i.product_name} x{i.quantity}</p>)}</td>
                <td className="px-4 py-3 text-xs font-semibold" style={{ color: "var(--text-primary)" }}>¥{o.total_amount.toLocaleString()}</td>
                <td className="px-4 py-3"><span className="text-[11px] font-medium" style={{ color: statusColors[o.status] }}>{t(`orders.status${o.status.charAt(0).toUpperCase() + o.status.slice(1)}`)}</span></td>
                <td className="px-4 py-3 text-[11px]" style={{ color: "var(--text-muted)" }}>{new Date(o.created_at).toLocaleDateString("zh-CN")}</td>
                <td className="px-4 py-3"><select value={o.status} onChange={(e) => handleStatusChange(o.id, e.target.value)} className="px-2 py-1 rounded text-[11px] focus:outline-none cursor-pointer" style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-secondary)" }}>
                  {opts.map((s) => <option key={s} value={s}>{t(`orders.status${s.charAt(0).toUpperCase() + s.slice(1)}`)}</option>)}
                </select></td>
              </tr>
            ))}</tbody>
          </table>
        )}
        <div className="px-4 py-2.5 flex items-center justify-between" style={{ background: "var(--bg-app)", borderTop: "1px solid var(--border)" }}>
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="flex items-center gap-1 px-3 py-1 text-xs rounded-lg disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed" style={{ color: "var(--text-secondary)", border: "1px solid var(--border)" }}><ChevronLeft className="w-3 h-3" />{t("orders.prevPage")}</button>
          <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{t("orders.pageInfo", { current: page, total: Math.ceil(total / 20) })}</span>
          <button onClick={() => setPage(page + 1)} disabled={page * 20 >= total} className="flex items-center gap-1 px-3 py-1 text-xs rounded-lg disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed" style={{ color: "var(--text-secondary)", border: "1px solid var(--border)" }}>{t("orders.nextPage")}<ChevronRight className="w-3 h-3" /></button>
        </div>
      </div>
      {selected && (
        <div className="fixed inset-0 flex items-center justify-center p-4 z-50" style={{ background: "rgba(0,0,0,0.6)" }} onClick={() => setSelected(null)}>
          <div className="rounded-xl max-w-lg w-full max-h-[80vh] overflow-y-auto shadow-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }} onClick={(e) => e.stopPropagation()}>
            <div className="px-5 py-3 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border)" }}>
              <h2 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>{t("orders.orderDetail")}</h2>
              <button onClick={() => setSelected(null)} className="p-1 rounded cursor-pointer" style={{ color: "var(--text-muted)" }}><X className="w-4 h-4" /></button>
            </div>
            <div className="p-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {[["orders.orderNo", selected.order_no], ["orders.customer", selected.customer_id], ["orders.amount", `¥${selected.total_amount.toLocaleString()}`]].map(([k, v]) => <div key={k}><p className="text-[10px] mb-0.5" style={{ color: "var(--text-muted)" }}>{t(k)}</p><p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{v}</p></div>)}
                <div><p className="text-[10px] mb-0.5" style={{ color: "var(--text-muted)" }}>{t("orders.status")}</p><span className="text-[11px] font-medium" style={{ color: statusColors[selected.status] }}>{t(`orders.status${selected.status.charAt(0).toUpperCase() + selected.status.slice(1)}`)}</span></div>
              </div>
              <div><p className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>{t("orders.shippingAddress")}</p><p className="text-xs p-2.5 rounded-lg" style={{ color: "var(--text-secondary)", background: "var(--bg-elevated)" }}>{selected.shipping_address}</p></div>
              <div>
                <p className="text-[10px] mb-1.5" style={{ color: "var(--text-muted)" }}>{t("orders.productDetail")}</p>
                <table className="w-full text-xs"><thead><tr style={{ borderBottom: "1px solid var(--border)" }}>{[t("orders.products"), t("orders.amount"), t("orders.quantity"), t("orders.subtotal")].map((h) => <th key={h} className="py-1.5 text-left text-[10px] font-semibold" style={{ color: "var(--text-muted)" }}>{h}</th>)}</tr></thead>
                  <tbody>{selected.items.map((i, idx) => <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}><td className="py-1.5" style={{ color: "var(--text-secondary)" }}>{i.product_name}</td><td className="py-1.5" style={{ color: "var(--text-muted)" }}>¥{i.unit_price.toLocaleString()}</td><td className="py-1.5" style={{ color: "var(--text-muted)" }}>{i.quantity}</td><td className="py-1.5 font-semibold" style={{ color: "var(--text-primary)" }}>¥{i.subtotal.toLocaleString()}</td></tr>)}</tbody></table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
