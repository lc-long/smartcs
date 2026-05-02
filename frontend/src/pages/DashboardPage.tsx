import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../services/api";
import { Package, DollarSign, Users, TrendingUp, Clock, RotateCcw, BarChart3, Star, ArrowUpRight, ArrowDownRight } from "lucide-react";

interface DashboardStats {
  summary: { total_customers: number; total_orders: number; total_revenue: number; today_orders: number; pending_tickets: number; pending_refunds: number; avg_order_amount: number; avg_rating: number; };
  order_status_distribution: Record<string, number>;
  top_products: Array<{ name: string; quantity: number; amount: number }>;
}

const statusColors: Record<string, string> = { pending: "var(--warning)", processing: "var(--accent)", shipped: "#8B5CF6", delivered: "var(--success)", cancelled: "var(--error)" };

export function DashboardPage() {
  const { t } = useTranslation();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.getAnalyticsDashboard().then(setStats).catch(console.error).finally(() => setLoading(false)); }, []);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /></div>;
  if (!stats) return <div className="flex items-center justify-center h-full text-sm" style={{ color: "var(--text-muted)" }}>{t("common.loadingFailed")}</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{t("dashboard.title")}</h1>
        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{t("dashboard.subtitle")}</p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        <StatCard title={t("dashboard.totalOrders")} value={stats.summary.total_orders.toLocaleString()} icon={Package} trend="+12.5%" up />
        <StatCard title={t("dashboard.totalRevenue")} value={`¥${stats.summary.total_revenue.toLocaleString()}`} icon={DollarSign} trend="+8.2%" up />
        <StatCard title={t("dashboard.customers")} value={stats.summary.total_customers.toLocaleString()} icon={Users} trend="+3.1%" up />
        <StatCard title={t("dashboard.todayOrders")} value={stats.summary.today_orders.toString()} icon={TrendingUp} trend="-2.4%" up={false} />
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        {[{ t: t("dashboard.pendingTickets"), v: stats.summary.pending_tickets, i: Clock }, { t: t("dashboard.pendingRefunds"), v: stats.summary.pending_refunds, i: RotateCcw }, { t: t("dashboard.avgOrderAmount"), v: `¥${stats.summary.avg_order_amount.toLocaleString()}`, i: BarChart3 }, { t: t("dashboard.customerRating"), v: stats.summary.avg_rating.toFixed(1), i: Star }].map((c) => (
          <div key={c.t} className="rounded-xl p-3" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
            <div className="flex items-center gap-2"><c.i className="w-3.5 h-3.5" style={{ color: "var(--text-dim)" }} /><p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{c.t}</p></div>
            <p className="text-base font-bold mt-1" style={{ color: "var(--text-primary)" }}>{c.v}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl p-4" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
          <h2 className="text-xs font-bold mb-3" style={{ color: "var(--text-primary)" }}>{t("dashboard.orderStatus")}</h2>
          <div className="space-y-2.5">
            {Object.entries(stats.order_status_distribution).map(([status, count]) => {
              const pct = (count / stats.summary.total_orders) * 100;
              return (
                <div key={status} className="flex items-center gap-3">
                  <span className="text-[11px] font-medium min-w-[60px]" style={{ color: statusColors[status] || "var(--text-muted)" }}>{t(`orders.status${status.charAt(0).toUpperCase() + status.slice(1)}`)}</span>
                  <div className="flex-1 rounded-full h-1.5" style={{ background: "var(--bg-elevated)" }}><div className="h-1.5 rounded-full" style={{ background: statusColors[status] || "var(--text-muted)", width: `${pct}%` }} /></div>
                  <span className="text-xs font-semibold w-8 text-right" style={{ color: "var(--text-secondary)" }}>{count}</span>
                </div>
              );
            })}
          </div>
        </div>
        <div className="rounded-xl p-4" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
          <h2 className="text-xs font-bold mb-3" style={{ color: "var(--text-primary)" }}>{t("dashboard.topProducts")}</h2>
          <div className="space-y-2">
            {stats.top_products.map((p, i) => (
              <div key={i} className="flex items-center gap-3 p-2 rounded-lg transition-colors">
                <div className="w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold" style={{ background: i === 0 ? "rgba(245,158,11,0.15)" : "var(--badge-bg)", color: i === 0 ? "var(--warning)" : "var(--text-muted)" }}>{i + 1}</div>
                <div className="flex-1 min-w-0"><p className="text-xs font-semibold truncate" style={{ color: "var(--text-primary)" }}>{p.name}</p><p className="text-[10px]" style={{ color: "var(--text-dim)" }}>{p.quantity} units</p></div>
                <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>¥{p.amount.toLocaleString()}</span>
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
    <div className="rounded-xl p-4 transition-colors" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
      <div className="flex items-start justify-between mb-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "var(--bg-elevated)" }}><Icon className="w-4 h-4" style={{ color: "var(--text-muted)" }} /></div>
        <div className="flex items-center gap-0.5 text-[10px] font-medium" style={{ color: up ? "var(--success)" : "var(--error)" }}>
          {up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}{trend}
        </div>
      </div>
      <p className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>{value}</p>
      <p className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>{title}</p>
    </div>
  );
}
