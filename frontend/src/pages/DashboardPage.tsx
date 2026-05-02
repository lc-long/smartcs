import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../services/api";
import { Package, DollarSign, Users, TrendingUp, Clock, RotateCcw, BarChart3, Star, ArrowUpRight, ArrowDownRight } from "lucide-react";

interface DashboardStats {
  summary: { total_customers: number; total_orders: number; total_revenue: number; today_orders: number; pending_tickets: number; pending_refunds: number; avg_order_amount: number; avg_rating: number; };
  order_status_distribution: Record<string, number>;
  top_products: Array<{ name: string; quantity: number; amount: number }>;
}

const statusStyles: Record<string, { text: string; bar: string }> = {
  pending: { text: "text-amber-400", bar: "bg-amber-500" },
  processing: { text: "text-sky-400", bar: "bg-sky-500" },
  shipped: { text: "text-violet-400", bar: "bg-violet-500" },
  delivered: { text: "text-emerald-400", bar: "bg-emerald-500" },
  cancelled: { text: "text-red-400", bar: "bg-red-500" },
};

export function DashboardPage() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.getAnalyticsDashboard().then(setStats).catch(console.error).finally(() => setLoading(false)); }, []);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" /></div>;
  if (!stats) return <div className="flex items-center justify-center h-full text-zinc-500 text-sm">{t("common.loadingFailed")}</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-lg font-bold text-zinc-100">{t("dashboard.title")}</h1>
        <p className="text-xs text-zinc-500 mt-0.5">{t("dashboard.subtitle")}</p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        <StatCard title={t("dashboard.totalOrders")} value={stats.summary.total_orders.toLocaleString()} icon={Package} trend="+12.5%" up />
        <StatCard title={t("dashboard.totalRevenue")} value={`¥${stats.summary.total_revenue.toLocaleString()}`} icon={DollarSign} trend="+8.2%" up />
        <StatCard title={t("dashboard.customers")} value={stats.summary.total_customers.toLocaleString()} icon={Users} trend="+3.1%" up />
        <StatCard title={t("dashboard.todayOrders")} value={stats.summary.today_orders.toString()} icon={TrendingUp} trend="-2.4%" up={false} />
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        <MiniCard title={t("dashboard.pendingTickets")} value={stats.summary.pending_tickets} icon={Clock} />
        <MiniCard title={t("dashboard.pendingRefunds")} value={stats.summary.pending_refunds} icon={RotateCcw} />
        <MiniCard title={t("dashboard.avgOrderAmount")} value={`¥${stats.summary.avg_order_amount.toLocaleString()}`} icon={BarChart3} />
        <MiniCard title={t("dashboard.customerRating")} value={stats.summary.avg_rating.toFixed(1)} icon={Star} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
          <h2 className="text-xs font-bold text-zinc-200 mb-3">{t("dashboard.orderStatus")}</h2>
          <div className="space-y-2.5">
            {Object.entries(stats.order_status_distribution).map(([status, count]) => {
              const s = statusStyles[status] || { text: "text-zinc-400", bar: "bg-zinc-500" };
              const pct = (count / stats.summary.total_orders) * 100;
              return (
                <div key={status} className="flex items-center gap-3">
                  <span className={`text-[11px] font-medium ${s.text} min-w-[60px]`}>{t(`orders.status${status.charAt(0).toUpperCase() + status.slice(1)}`)}</span>
                  <div className="flex-1 bg-zinc-800 rounded-full h-1.5"><div className={`h-1.5 rounded-full ${s.bar}`} style={{ width: `${pct}%` }} /></div>
                  <span className="text-xs font-semibold text-zinc-300 w-8 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
          <h2 className="text-xs font-bold text-zinc-200 mb-3">{t("dashboard.topProducts")}</h2>
          <div className="space-y-2">
            {stats.top_products.map((p, i) => (
              <div key={i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-zinc-800/50 transition-colors">
                <div className={`w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold ${i === 0 ? "bg-amber-900/50 text-amber-400" : "bg-zinc-800 text-zinc-500"}`}>{i + 1}</div>
                <div className="flex-1 min-w-0"><p className="text-xs font-semibold text-zinc-200 truncate">{p.name}</p><p className="text-[10px] text-zinc-600">{p.quantity} units</p></div>
                <span className="text-xs font-bold text-zinc-200">¥{p.amount.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, trend, up }: { title: string; value: string; icon: typeof Package; trend: string; up: boolean }) {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4 hover:border-zinc-700 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center"><Icon className="w-4 h-4 text-zinc-500" /></div>
        <div className={`flex items-center gap-0.5 text-[10px] font-medium ${up ? "text-emerald-400" : "text-red-400"}`}>
          {up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}{trend}
        </div>
      </div>
      <p className="text-xl font-bold text-zinc-100">{value}</p>
      <p className="text-[10px] text-zinc-500 mt-0.5">{title}</p>
    </div>
  );
}

function MiniCard({ title, value, icon: Icon }: { title: string; value: string | number; icon: typeof Clock }) {
  return (
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-3">
      <div className="flex items-center gap-2"><Icon className="w-3.5 h-3.5 text-zinc-600" /><p className="text-[10px] text-zinc-500">{title}</p></div>
      <p className="text-base font-bold text-zinc-100 mt-1">{value}</p>
    </div>
  );
}
