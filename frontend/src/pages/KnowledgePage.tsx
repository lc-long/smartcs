import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Eye, FileText } from "lucide-react";

interface KnowledgeArticle { id: string; title: string; category: string; view_count: number; is_published: boolean; created_at: string; }

const categoryLabels: Record<string, string> = { technical: "技术支持", refund: "退款政策", billing: "账单相关", general: "通用问题" };
const categoryColors: Record<string, string> = { technical: "text-sky-400", refund: "text-amber-400", billing: "text-emerald-400", general: "text-violet-400" };

export function KnowledgePage() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");

  useEffect(() => { loadArticles(); }, [category]);

  async function loadArticles() {
    try { setLoading(true); const data = await api.getKnowledge(category || undefined); setArticles(data.items); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-zinc-100">知识库管理</h1>
        <p className="text-xs text-zinc-500 mt-0.5">管理常见问题和解决方案</p>
      </div>

      <div className="flex items-center gap-3 mb-4">
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-1.5 border border-zinc-800 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600/50 bg-zinc-900 text-zinc-300 cursor-pointer">
          <option value="">所有分类</option>
          <option value="technical">技术支持</option>
          <option value="refund">退款政策</option>
          <option value="billing">账单相关</option>
          <option value="general">通用问题</option>
        </select>
        <div className="flex-1" />
        <span className="text-[11px] text-zinc-500">共 {articles.length} 篇文章</span>
      </div>

      <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" /></div>
        : articles.length === 0 ? <div className="p-10 text-center text-zinc-500 text-sm">暂无知识库文章</div> : (
          <table className="w-full">
            <thead><tr className="border-b border-zinc-800">
              {["标题", "分类", "浏览量", "状态", "创建时间"].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr></thead>
            <tbody className="divide-y divide-zinc-800/50">
              {articles.map((a) => (
                <tr key={a.id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-zinc-500" />
                      <span className="text-xs font-semibold text-zinc-200">{a.title}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3"><span className={`text-[11px] font-medium ${categoryColors[a.category] || "text-zinc-400"}`}>{categoryLabels[a.category] || a.category}</span></td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 text-xs text-zinc-400">
                      <Eye className="w-3 h-3" />{a.view_count}
                    </div>
                  </td>
                  <td className="px-4 py-3"><span className={`text-[10px] font-medium ${a.is_published ? "text-emerald-400" : "text-zinc-500"}`}>{a.is_published ? "已发布" : "草稿"}</span></td>
                  <td className="px-4 py-3 text-[11px] text-zinc-500">{new Date(a.created_at).toLocaleDateString("zh-CN")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
