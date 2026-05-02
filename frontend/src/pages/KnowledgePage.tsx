import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Eye, FileText } from "lucide-react";

interface KnowledgeArticle { id: string; title: string; category: string; view_count: number; is_published: boolean; created_at: string; }
const categoryLabels: Record<string, string> = { technical: "技术支持", refund: "退款政策", billing: "账单相关", general: "通用问题" };
const categoryColors: Record<string, string> = { technical: "var(--accent)", refund: "var(--warning)", billing: "var(--success)", general: "#8B5CF6" };

export function KnowledgePage() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");

  useEffect(() => { loadArticles(); }, [category]);
  async function loadArticles() { try { setLoading(true); const d = await api.getKnowledge(category || undefined); setArticles(d.items); } catch (e) { console.error(e); } finally { setLoading(false); } }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5"><h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>知识库管理</h1><p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>管理常见问题和解决方案</p></div>
      <div className="flex items-center gap-3 mb-4">
        <select value={category} onChange={(e) => setCategory(e.target.value)} className="px-3 py-1.5 rounded-lg text-xs focus:outline-none cursor-pointer" style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-secondary)" }}>
          <option value="">所有分类</option><option value="technical">技术支持</option><option value="refund">退款政策</option><option value="billing">账单相关</option><option value="general">通用问题</option>
        </select>
        <div className="flex-1" /><span className="text-[11px]" style={{ color: "var(--text-muted)" }}>共 {articles.length} 篇文章</span>
      </div>
      <div className="rounded-xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /></div>
        : articles.length === 0 ? <div className="p-10 text-center text-sm" style={{ color: "var(--text-muted)" }}>暂无知识库文章</div> : (
          <table className="w-full">
            <thead><tr style={{ borderBottom: "1px solid var(--border)" }}>{["标题", "分类", "浏览量", "状态", "创建时间"].map((h) => <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{h}</th>)}</tr></thead>
            <tbody>{articles.map((a) => (
              <tr key={a.id} className="transition-colors" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td className="px-4 py-3"><div className="flex items-center gap-2"><FileText className="w-3.5 h-3.5" style={{ color: "var(--text-dim)" }} /><span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{a.title}</span></div></td>
                <td className="px-4 py-3"><span className="text-[11px] font-medium" style={{ color: categoryColors[a.category] }}>{categoryLabels[a.category]}</span></td>
                <td className="px-4 py-3"><div className="flex items-center gap-1 text-xs" style={{ color: "var(--text-secondary)" }}><Eye className="w-3 h-3" />{a.view_count}</div></td>
                <td className="px-4 py-3"><span className="text-[10px] font-medium" style={{ color: a.is_published ? "var(--success)" : "var(--text-muted)" }}>{a.is_published ? "已发布" : "草稿"}</span></td>
                <td className="px-4 py-3 text-[11px]" style={{ color: "var(--text-muted)" }}>{new Date(a.created_at).toLocaleDateString("zh-CN")}</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </div>
    </div>
  );
}
