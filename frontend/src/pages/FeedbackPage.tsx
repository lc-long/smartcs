import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Star, ThumbsUp, ThumbsDown, MessageSquare } from "lucide-react";

interface SatisfactionStats { review_summary: { total_reviews: number; avg_rating: number; positive_rate: number; negative_rate: number; }; rating_distribution: Record<number, number>; feedback_distribution: Record<string, number>; feedback_status: Record<string, number>; ticket_priority_distribution: Record<string, number>; }
const feedbackTypeLabels: Record<string, string> = { complaint: "投诉", suggestion: "建议", praise: "表扬", question: "咨询" };
const feedbackTypeColors: Record<string, string> = { complaint: "var(--error)", suggestion: "var(--accent)", praise: "var(--success)", question: "var(--warning)" };
const feedbackStatusLabels: Record<string, string> = { pending: "待处理", in_review: "审核中", resolved: "已解决", closed: "已关闭" };
const feedbackStatusColors: Record<string, string> = { pending: "var(--warning)", in_review: "var(--accent)", resolved: "var(--success)", closed: "var(--text-muted)" };
const priorityLabels: Record<string, string> = { low: "低", medium: "中", high: "高", critical: "紧急" };
const priorityColors: Record<string, string> = { low: "var(--text-muted)", medium: "var(--accent)", high: "var(--warning)", critical: "var(--error)" };

export function FeedbackPage() {
  const [stats, setStats] = useState<SatisfactionStats | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { api.getCustomerSatisfaction().then(setStats).catch(console.error).finally(() => setLoading(false)); }, []);
  if (loading) return <div className="flex items-center justify-center h-full"><div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /></div>;
  if (!stats) return <div className="flex items-center justify-center h-full text-sm" style={{ color: "var(--text-muted)" }}>加载失败</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6"><h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>客户满意度</h1><p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>客户评价与反馈分析</p></div>
      <div className="grid grid-cols-4 gap-3 mb-4">
        {[{ l: "总评价数", v: stats.review_summary.total_reviews, i: MessageSquare }, { l: "平均评分", v: stats.review_summary.avg_rating.toFixed(1), i: Star }, { l: "好评率", v: `${stats.review_summary.positive_rate}%`, i: ThumbsUp }, { l: "差评率", v: `${stats.review_summary.negative_rate}%`, i: ThumbsDown }].map((c) => (
          <div key={c.l} className="rounded-xl p-4" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
            <div className="flex items-center gap-2 mb-2"><c.i className="w-3.5 h-3.5" style={{ color: "var(--text-dim)" }} /><p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{c.l}</p></div>
            <p className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>{c.v}</p>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="rounded-xl p-4" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
          <h2 className="text-xs font-bold mb-3" style={{ color: "var(--text-primary)" }}>评分分布</h2>
          <div className="space-y-2">{[5, 4, 3, 2, 1].map((r) => { const count = stats.rating_distribution[r] || 0; const pct = stats.review_summary.total_reviews > 0 ? (count / stats.review_summary.total_reviews) * 100 : 0; return (
            <div key={r} className="flex items-center gap-3"><span className="text-[11px] w-6" style={{ color: "var(--text-muted)" }}>{r}星</span><div className="flex-1 rounded-full h-1.5" style={{ background: "var(--bg-elevated)" }}><div className="h-1.5 rounded-full" style={{ background: "var(--warning)", width: `${pct}%` }} /></div><span className="text-xs font-semibold w-8 text-right" style={{ color: "var(--text-secondary)" }}>{count}</span></div>
          ); })}</div>
        </div>
        <div className="rounded-xl p-4" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
          <h2 className="text-xs font-bold mb-3" style={{ color: "var(--text-primary)" }}>反馈类型分布</h2>
          <div className="space-y-2.5">{Object.entries(stats.feedback_distribution).map(([type, count]) => (
            <div key={type} className="flex items-center justify-between"><span className="text-[11px] font-medium" style={{ color: feedbackTypeColors[type] }}>{feedbackTypeLabels[type] || type}</span><span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>{count}</span></div>
          ))}</div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl p-4" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
          <h2 className="text-xs font-bold mb-3" style={{ color: "var(--text-primary)" }}>反馈状态</h2>
          <div className="space-y-2.5">{Object.entries(stats.feedback_status).map(([status, count]) => (
            <div key={status} className="flex items-center justify-between"><span className="text-[11px] font-medium" style={{ color: feedbackStatusColors[status] }}>{feedbackStatusLabels[status]}</span><span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>{count}</span></div>
          ))}</div>
        </div>
        <div className="rounded-xl p-4" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
          <h2 className="text-xs font-bold mb-3" style={{ color: "var(--text-primary)" }}>工单优先级分布</h2>
          <div className="space-y-2.5">{Object.entries(stats.ticket_priority_distribution).map(([p, count]) => (
            <div key={p} className="flex items-center justify-between"><span className="text-[11px] font-medium" style={{ color: priorityColors[p] }}>{priorityLabels[p]}</span><span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>{count}</span></div>
          ))}</div>
        </div>
      </div>
    </div>
  );
}
