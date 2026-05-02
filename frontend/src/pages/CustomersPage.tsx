import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../services/api";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

interface Customer { id: string; name: string; email: string; phone: string; address: string; vip_level: string; orders_count: number; total_spent: number; created_at: string; }

const vipColors: Record<string, string> = { normal: "text-zinc-400", silver: "text-zinc-300", gold: "text-amber-400" };

export function CustomersPage() {
  const { t } = useTranslation();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [vipLevel, setVipLevel] = useState("");
  const [selected, setSelected] = useState<Customer | null>(null);

  useEffect(() => { loadCustomers(); }, [page, vipLevel]);

  async function loadCustomers() {
    try { setLoading(true); const data = await api.getCustomers({ page, page_size: 20, vip_level: vipLevel || undefined }); setCustomers(data.items); setTotal(data.total); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-zinc-100">{t("customers.title")}</h1>
        <p className="text-xs text-zinc-500 mt-0.5">{t("customers.subtitle")}</p>
      </div>
      <div className="flex items-center gap-3 mb-4">
        <select value={vipLevel} onChange={(e) => { setVipLevel(e.target.value); setPage(1); }}
          className="px-3 py-1.5 border border-zinc-800 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600/50 bg-zinc-900 text-zinc-300 cursor-pointer">
          <option value="">{t("customers.allLevels")}</option>
          {["normal", "silver", "gold"].map((v) => <option key={v} value={v}>{t(`customers.${v}`)}</option>)}
        </select>
        <div className="flex-1" />
        <span className="text-[11px] text-zinc-500">{t("customers.totalCustomers", { count: total })}</span>
      </div>
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" /></div> : (
          <table className="w-full">
            <thead><tr className="border-b border-zinc-800">
              {[t("customers.customer"), t("customers.contact"), t("customers.vipLevel"), t("customers.orderCount"), t("customers.totalSpent"), t("customers.registerTime")].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr></thead>
            <tbody className="divide-y divide-zinc-800/50">
              {customers.map((c) => (
                <tr key={c.id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="px-4 py-3"><button onClick={() => setSelected(c)} className="text-xs font-semibold text-indigo-400 hover:underline cursor-pointer">{c.name}</button><p className="text-[10px] text-zinc-600 font-mono">{c.id}</p></td>
                  <td className="px-4 py-3"><p className="text-xs text-zinc-300">{c.email}</p><p className="text-[11px] text-zinc-500">{c.phone}</p></td>
                  <td className="px-4 py-3"><span className={`text-[11px] font-medium ${vipColors[c.vip_level] || "text-zinc-400"}`}>{t(`customers.${c.vip_level}`)}</span></td>
                  <td className="px-4 py-3 text-xs text-zinc-300">{c.orders_count}</td>
                  <td className="px-4 py-3 text-xs font-semibold text-zinc-200">¥{c.total_spent.toLocaleString()}</td>
                  <td className="px-4 py-3 text-[11px] text-zinc-500">{new Date(c.created_at).toLocaleDateString("zh-CN")}</td>
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
      {selected && <CustomerDetail customer={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function CustomerDetail({ customer, onClose }: { customer: Customer; onClose: () => void }) {
  const { t } = useTranslation();
  const [details, setDetails] = useState<{ orders: Array<{ order_no: string; amount: number; status: string; created_at: string }>; tickets: Array<{ ticket_no: string; title: string; status: string; created_at: string }> } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.getCustomer(customer.id).then((d) => setDetails({ orders: d.orders, tickets: d.tickets })).catch(console.error).finally(() => setLoading(false)); }, [customer.id]);

  const orderStatusColors: Record<string, string> = { pending: "text-amber-400", processing: "text-sky-400", shipped: "text-violet-400", delivered: "text-emerald-400", cancelled: "text-red-400" };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-zinc-900 rounded-xl max-w-lg w-full max-h-[80vh] overflow-y-auto border border-zinc-800 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="px-5 py-3 border-b border-zinc-800 flex items-center justify-between">
          <h2 className="text-sm font-bold text-zinc-100">{t("customers.customerDetail")}</h2>
          <button onClick={onClose} className="p-1 rounded hover:bg-zinc-800 cursor-pointer"><X className="w-4 h-4 text-zinc-500" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {[["customers.name", customer.name], ["customers.email", customer.email], ["customers.phone", customer.phone], ["customers.vipLevel", t(`customers.${customer.vip_level}`)]].map(([k, v]) => (
              <div key={k}><p className="text-[10px] text-zinc-500 mb-0.5">{t(k)}</p><p className="text-sm font-semibold text-zinc-100">{v}</p></div>
            ))}
          </div>
          <div><p className="text-[10px] text-zinc-500 mb-1">{t("customers.address")}</p><p className="text-xs text-zinc-300 p-2.5 bg-zinc-800/50 rounded-lg">{customer.address}</p></div>
          <div>
            <h3 className="text-xs font-bold text-zinc-200 mb-2">{t("customers.recentOrders")}</h3>
            {loading ? <div className="flex justify-center p-3"><div className="w-5 h-5 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" /></div>
            : details?.orders?.length ? <div className="space-y-1.5">{details.orders.map((o, i) => (
              <div key={i} className="flex items-center justify-between p-2.5 bg-zinc-800/50 rounded-lg">
                <div><p className="text-xs font-medium text-zinc-200">{o.order_no}</p><p className="text-[10px] text-zinc-500">{new Date(o.created_at).toLocaleDateString("zh-CN")}</p></div>
                <div className="text-right"><p className="text-xs font-semibold text-zinc-200">¥{o.amount.toLocaleString()}</p><span className={`text-[10px] font-medium ${orderStatusColors[o.status] || "text-zinc-400"}`}>{t(`orders.status${o.status.charAt(0).toUpperCase() + o.status.slice(1)}`)}</span></div>
              </div>
            ))}</div> : <p className="text-xs text-zinc-500">{t("customers.noOrders")}</p>}
          </div>
          <div>
            <h3 className="text-xs font-bold text-zinc-200 mb-2">{t("customers.recentTickets")}</h3>
            {details?.tickets?.length ? <div className="space-y-1.5">{details.tickets.map((tk, i) => (
              <div key={i} className="flex items-center justify-between p-2.5 bg-zinc-800/50 rounded-lg">
                <div><p className="text-xs font-medium text-zinc-200">{tk.ticket_no}</p><p className="text-[10px] text-zinc-500">{tk.title}</p></div>
                <span className={`text-[10px] font-medium ${tk.status === "open" ? "text-amber-400" : "text-emerald-400"}`}>{tk.status === "open" ? t("orders.statusPending") : t("orders.statusDelivered")}</span>
              </div>
            ))}</div> : <p className="text-xs text-zinc-500">{t("customers.noTickets")}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
