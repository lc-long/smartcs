import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../services/api";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

interface Customer { id: string; name: string; email: string; phone: string; address: string; vip_level: string; orders_count: number; total_spent: number; created_at: string; }
const vipColors: Record<string, string> = { normal: "var(--text-muted)", silver: "var(--text-secondary)", gold: "var(--warning)" };

export function CustomersPage() {
  const { t } = useTranslation();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [vipLevel, setVipLevel] = useState("");
  const [selected, setSelected] = useState<Customer | null>(null);

  useEffect(() => { loadCustomers(); }, [page, vipLevel]);
  async function loadCustomers() { try { setLoading(true); const d = await api.getCustomers({ page, page_size: 20, vip_level: vipLevel || undefined }); setCustomers(d.items); setTotal(d.total); } catch (e) { console.error(e); } finally { setLoading(false); } }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5"><h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{t("customers.title")}</h1><p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{t("customers.subtitle")}</p></div>
      <div className="flex items-center gap-3 mb-4">
        <select value={vipLevel} onChange={(e) => { setVipLevel(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-lg text-xs focus:outline-none cursor-pointer" style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-secondary)" }}>
          <option value="">{t("customers.allLevels")}</option>
          {["normal", "silver", "gold"].map((v) => <option key={v} value={v}>{t(`customers.${v}`)}</option>)}
        </select>
        <div className="flex-1" /><span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{t("customers.totalCustomers", { count: total })}</span>
      </div>
      <div className="rounded-xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /></div> : (
          <table className="w-full">
            <thead><tr style={{ borderBottom: "1px solid var(--border)" }}>{[t("customers.customer"), t("customers.contact"), t("customers.vipLevel"), t("customers.orderCount"), t("customers.totalSpent"), t("customers.registerTime")].map((h) => <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{h}</th>)}</tr></thead>
            <tbody>{customers.map((c) => (
              <tr key={c.id} className="transition-colors" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td className="px-4 py-3"><button onClick={() => setSelected(c)} className="text-xs font-semibold cursor-pointer" style={{ color: "var(--accent)" }}>{c.name}</button><p className="text-[10px] font-mono" style={{ color: "var(--text-dim)" }}>{c.id}</p></td>
                <td className="px-4 py-3"><p className="text-xs" style={{ color: "var(--text-secondary)" }}>{c.email}</p><p className="text-[11px]" style={{ color: "var(--text-muted)" }}>{c.phone}</p></td>
                <td className="px-4 py-3"><span className="text-[11px] font-medium" style={{ color: vipColors[c.vip_level] }}>{t(`customers.${c.vip_level}`)}</span></td>
                <td className="px-4 py-3 text-xs" style={{ color: "var(--text-secondary)" }}>{c.orders_count}</td>
                <td className="px-4 py-3 text-xs font-semibold" style={{ color: "var(--text-primary)" }}>¥{c.total_spent.toLocaleString()}</td>
                <td className="px-4 py-3 text-[11px]" style={{ color: "var(--text-muted)" }}>{new Date(c.created_at).toLocaleDateString("zh-CN")}</td>
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
      {selected && <CustomerDetail customer={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function CustomerDetail({ customer, onClose }: { customer: Customer; onClose: () => void }) {
  const { t } = useTranslation();
  const [details, setDetails] = useState<{ orders: Array<{ order_no: string; amount: number; status: string; created_at: string }>; tickets: Array<{ ticket_no: string; title: string; status: string; created_at: string }> } | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { api.getCustomer(customer.id).then((d) => setDetails({ orders: d.orders, tickets: d.tickets })).catch(console.error).finally(() => setLoading(false)); }, [customer.id]);
  const orderStatusColors: Record<string, string> = { pending: "var(--warning)", processing: "var(--accent)", shipped: "#8B5CF6", delivered: "var(--success)", cancelled: "var(--error)" };

  return (
    <div className="fixed inset-0 flex items-center justify-center p-4 z-50" style={{ background: "rgba(0,0,0,0.6)" }} onClick={onClose}>
      <div className="rounded-xl max-w-lg w-full max-h-[80vh] overflow-y-auto shadow-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }} onClick={(e) => e.stopPropagation()}>
        <div className="px-5 py-3 flex items-center justify-between" style={{ borderBottom: "1px solid var(--border)" }}>
          <h2 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>{t("customers.customerDetail")}</h2>
          <button onClick={onClose} className="p-1 rounded cursor-pointer" style={{ color: "var(--text-muted)" }}><X className="w-4 h-4" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">{[["customers.name", customer.name], ["customers.email", customer.email], ["customers.phone", customer.phone], ["customers.vipLevel", t(`customers.${customer.vip_level}`)]].map(([k, v]) => <div key={k}><p className="text-[10px] mb-0.5" style={{ color: "var(--text-muted)" }}>{t(k)}</p><p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{v}</p></div>)}</div>
          <div><p className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>{t("customers.address")}</p><p className="text-xs p-2.5 rounded-lg" style={{ color: "var(--text-secondary)", background: "var(--bg-elevated)" }}>{customer.address}</p></div>
          <div>
            <h3 className="text-xs font-bold mb-2" style={{ color: "var(--text-primary)" }}>{t("customers.recentOrders")}</h3>
            {loading ? <div className="flex justify-center p-3"><div className="w-5 h-5 border-2 rounded-full animate-spin" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /></div>
            : details?.orders?.length ? <div className="space-y-1.5">{details.orders.map((o, i) => (
              <div key={i} className="flex items-center justify-between p-2.5 rounded-lg" style={{ background: "var(--bg-elevated)" }}>
                <div><p className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>{o.order_no}</p><p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{new Date(o.created_at).toLocaleDateString("zh-CN")}</p></div>
                <div className="text-right"><p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>¥{o.amount.toLocaleString()}</p><span className="text-[10px] font-medium" style={{ color: orderStatusColors[o.status] }}>{t(`orders.status${o.status.charAt(0).toUpperCase() + o.status.slice(1)}`)}</span></div>
              </div>
            ))}</div> : <p className="text-xs" style={{ color: "var(--text-muted)" }}>{t("customers.noOrders")}</p>}
          </div>
          <div>
            <h3 className="text-xs font-bold mb-2" style={{ color: "var(--text-primary)" }}>{t("customers.recentTickets")}</h3>
            {details?.tickets?.length ? <div className="space-y-1.5">{details.tickets.map((tk, i) => (
              <div key={i} className="flex items-center justify-between p-2.5 rounded-lg" style={{ background: "var(--bg-elevated)" }}>
                <div><p className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>{tk.ticket_no}</p><p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{tk.title}</p></div>
                <span className="text-[10px] font-medium" style={{ color: tk.status === "open" ? "var(--warning)" : "var(--success)" }}>{tk.status === "open" ? t("orders.statusPending") : t("orders.statusDelivered")}</span>
              </div>
            ))}</div> : <p className="text-xs" style={{ color: "var(--text-muted)" }}>{t("customers.noTickets")}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
