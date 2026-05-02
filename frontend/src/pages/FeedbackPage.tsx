import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Star, ThumbsUp, ThumbsDown, MessageSquare } from "lucide-react";

interface SatisfactionStats {
  review_summary: { total_reviews: number; avg_rating: number; positive_rate: number; negative_rate: number; };
  rating_distribution: Record<number, number>;
  feedback_distribution: Record<string, number>;
  feedback_status: Record<string, number>;
  ticket_priority_distribution: Record<string, number>;
}

const feedbackTypeLabels: Record<string, string> = { complaint: "投诉", suggestion: "建议", praise: "表扬", question: "咨询" };
const feedbackTypeColors: Record<string, string> = { complaint: "text-red-400", suggestion: "text-sky-400", praise: "text-emerald-400", question: "text-amber-400" };
const feedbackStatusLabels: Record<string, string> = { pending: "待处理", in_review: "审核中", resolved: "已解决", closed: "已关闭" };
const feedbackStatusColors: Record<string, string> = { pending: "text-amber-400", in_review: "text-sky-400", resolved: "text-emerald-400", closed: "text-zinc-400" };
const priorityLabels: Record<string, string> = { low: "低", medium: "中", high: "高", critical: "紧急" };
const priorityColors: Record<string, string> = { low: "text-zinc-400", medium: "text-sky-400", high: "text-amber-400", critical: "text-red-400" };

export function FeedbackPage() {
  const [stats, setStats] = useState<SatisfactionStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.getCustomerSatisfaction().then(setStats).catch(console.error).finally(() => setLoading(false)); }, []);

  if (loading) return <div className="flex items-center justify-center h-full"><div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" /></div>;
  if (!stats) return <div className="flex items-center justify-center h-full text-zinc-500 text-sm">加载失败</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-lg font-bold text-zinc-100">客户满意度</h1>
        <p className="text-xs text-zinc-500 mt-0.5">客户评价与反馈分析</p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        {[
          { label: "总评价数", value: stats.review_summary.total_reviews, icon: MessageSquare },
          { label: "平均评分", value: stats.review_summary.avg_rating.toFixed(1), icon: Star },
          { label: "好评率", value: `${stats.review_summary.positive_rate}%`, icon: ThumbsUp },
          { label: "差评率", value: `${stats.review_summary.negative_rate}%`, icon: ThumbsDown },
        ].map((c) => (
          <div key={c.label} className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
            <div className="flex items-center gap-2 mb-2"><c.icon className="w-3.5 h-3.5 text-zinc-500" /><p className="text-[10px] text-zinc-500">{c.label}</p></div>
            <p className="text-xl font-bold text-zinc-100">{c.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
          <h2 className="text-xs font-bold text-zinc-200 mb-3">评分分布</h2>
          <div className="space-y-2">
            {[5, 4, 3, 2, 1].map((r) => {
              const count = stats.rating_distribution[r] || 0;
              const pct = stats.review_summary.total_reviews > 0 ? (count / stats.review_summary.total_reviews) * 100 : 0;
              return (
                <div key={r} className="flex items-center gap-3">
                  <span className="text-[11px] text-zinc-400 w-6">{r}星</span>
                  <div className="flex-1 bg-zinc-800 rounded-full h-1.5"><div className="h-1.5 rounded-full bg-amber-500" style={{ width: `${pct}%` }} /></div>
                  <span className="text-xs font-semibold text-zinc-300 w-8 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
          <h2 className="text-xs font-bold text-zinc-200 mb-3">反馈类型分布</h2>
          <div className="space-y-2.5">
            {Object.entries(stats.feedback_distribution).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <span className={`text-[11px] font-medium ${feedbackTypeColors[type] || "text-zinc-400"}`}>{feedbackTypeLabels[type] || type}</span>
                <span className="text-xs font-semibold text-zinc-300">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
          <h2 className="text-xs font-bold text-zinc-200 mb-3">反馈状态</h2>
          <div className="space-y-2.5">
            {Object.entries(stats.feedback_status).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <span className={`text-[11px] font-medium ${feedbackStatusColors[status] || "text-zinc-400"}`}>{feedbackStatusLabels[status] || status}</span>
                <span className="text-xs font-semibold text-zinc-300">{count}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
          <h2 className="text-xs font-bold text-zinc-200 mb-3">工单优先级分布</h2>
          <div className="space-y-2.5">
            {Object.entries(stats.ticket_priority_distribution).map(([p, count]) => (
              <div key={p} className="flex items-center justify-between">
                <span className={`text-[11px] font-medium ${priorityColors[p] || "text-zinc-400"}`}>{priorityLabels[p] || p}</span>
                <span className="text-xs font-semibold text-zinc-300">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
