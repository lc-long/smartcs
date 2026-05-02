import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Package, Truck, Clock, Building2 } from "lucide-react";

interface LogisticsStats { status_distribution: Record<string, number>; carrier_distribution: Record<string, number>; avg_delivery_days: number; in_transit_count: number; }
const statusLabels: Record<string, string> = { pending: "待揽收", shipped: "已发货", in_transit: "运输中", delivered: "已送达" };
const statusColors: Record<string, string> = { pending: "var(--warning)", shipped: "var(--accent)", in_transit: "#8B5CF6", delivered: "var(--success)" };

export function LogisticsPage() {
  const [stats, setStats] = useState<LogisticsStats | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { api.getLogisticsStats().then(setStats).catch(console.error).finally(() => setLoading(false)); }, []);
  if (loading) return <div className="flex items-center justify-center h-full"><div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /></div>;
  if (!stats) return <div className="flex items-center justify-center h-full text-sm" style={{ color: "var(--text-muted)" }}>加载失败</div>;
  const total = Object.values(stats.status_distribution).reduce((s, c) => s + c, 0);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6"><h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>物流统计</h1><p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>物流配送数据分析</p></div>
      <div className="grid grid-cols-4 gap-3 mb-4">
        {[{ l: "总包裹数", v: total, i: Package }, { l: "运输中", v: stats.in_transit_count, i: Truck }, { l: "平均配送天数", v: `${stats.avg_delivery_days} 天`, i: Clock }, { l: "快递公司数", v: Object.keys(stats.carrier_distribution).length, i: Building2 }].map((c) => (
          <div key={c.l} className="rounded-xl p-4" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
            <div className="flex items-center gap-2 mb-2"><c.i className="w-3.5 h-3.5" style={{ color: "var(--text-dim)" }} /><p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{c.l}</p></div>
            <p className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>{c.v}</p>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3">
        {[{ title: "物流状态分布", data: stats.status_distribution, labels: statusLabels, colors: statusColors }, { title: "快递公司分布", data: stats.carrier_distribution, labels: {}, colors: {} }].map((panel) => (
          <div key={panel.title} className="rounded-xl p-4" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
            <h2 className="text-xs font-bold mb-3" style={{ color: "var(--text-primary)" }}>{panel.title}</h2>
            <div className="space-y-2.5">
              {Object.entries(panel.data).map(([key, count]) => (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-[11px] font-medium min-w-[50px]" style={{ color: panel.colors[key] || "var(--text-secondary)" }}>{panel.labels[key] || key}</span>
                  <div className="flex-1 rounded-full h-1.5" style={{ background: "var(--bg-elevated)" }}><div className="h-1.5 rounded-full" style={{ background: panel.colors[key] || "var(--accent)", width: `${(count / total) * 100}%` }} /></div>
                  <span className="text-xs font-semibold w-8 text-right" style={{ color: "var(--text-secondary)" }}>{count}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
