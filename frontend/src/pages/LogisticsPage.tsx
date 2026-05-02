import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Package, Truck, Clock, Building2 } from "lucide-react";

interface LogisticsStats { status_distribution: Record<string, number>; carrier_distribution: Record<string, number>; avg_delivery_days: number; in_transit_count: number; }

const statusLabels: Record<string, string> = { pending: "待揽收", shipped: "已发货", in_transit: "运输中", delivered: "已送达" };
const statusTextColors: Record<string, string> = { pending: "text-amber-400", shipped: "text-sky-400", in_transit: "text-violet-400", delivered: "text-emerald-400" };
const statusBarColors: Record<string, string> = { pending: "bg-amber-500", shipped: "bg-sky-500", in_transit: "bg-violet-500", delivered: "bg-emerald-500" };

export function LogisticsPage() {
  const [stats, setStats] = useState<LogisticsStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.getLogisticsStats().then(setStats).catch(console.error).finally(() => setLoading(false)); }, []);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" /></div>;
  if (!stats) return <div className="flex items-center justify-center h-full text-zinc-500 text-sm">加载失败</div>;

  const total = Object.values(stats.status_distribution).reduce((s, c) => s + c, 0);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-lg font-bold text-zinc-100">物流统计</h1>
        <p className="text-xs text-zinc-500 mt-0.5">物流配送数据分析</p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        {[
          { label: "总包裹数", value: total, icon: Package },
          { label: "运输中", value: stats.in_transit_count, icon: Truck },
          { label: "平均配送天数", value: `${stats.avg_delivery_days} 天`, icon: Clock },
          { label: "快递公司数", value: Object.keys(stats.carrier_distribution).length, icon: Building2 },
        ].map((c) => (
          <div key={c.label} className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
            <div className="flex items-center gap-2 mb-2"><c.icon className="w-3.5 h-3.5 text-zinc-500" /><p className="text-[10px] text-zinc-500">{c.label}</p></div>
            <p className="text-xl font-bold text-zinc-100">{c.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
          <h2 className="text-xs font-bold text-zinc-200 mb-3">物流状态分布</h2>
          <div className="space-y-2.5">
            {Object.entries(stats.status_distribution).map(([status, count]) => (
              <div key={status} className="flex items-center gap-3">
                <span className={`text-[11px] font-medium ${statusTextColors[status] || "text-zinc-400"} min-w-[50px]`}>{statusLabels[status] || status}</span>
                <div className="flex-1 bg-zinc-800 rounded-full h-1.5"><div className={`h-1.5 rounded-full ${statusBarColors[status] || "bg-zinc-500"}`} style={{ width: `${(count / total) * 100}%` }} /></div>
                <span className="text-xs font-semibold text-zinc-300 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
          <h2 className="text-xs font-bold text-zinc-200 mb-3">快递公司分布</h2>
          <div className="space-y-2.5">
            {Object.entries(stats.carrier_distribution).map(([carrier, count]) => (
              <div key={carrier} className="flex items-center gap-3">
                <span className="text-[11px] font-medium text-zinc-300 min-w-[60px]">{carrier}</span>
                <div className="flex-1 bg-zinc-800 rounded-full h-1.5"><div className="h-1.5 rounded-full bg-indigo-500" style={{ width: `${(count / total) * 100}%` }} /></div>
                <span className="text-xs font-semibold text-zinc-300 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
