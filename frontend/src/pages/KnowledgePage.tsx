import { useEffect, useState } from "react";
import { api } from "../services/api";

interface KnowledgeArticle {
  id: string;
  title: string;
  category: string;
  view_count: number;
  is_published: boolean;
  created_at: string;
}

const categoryLabels: Record<string, string> = {
  technical: "技术支持",
  refund: "退款政策",
  billing: "账单相关",
  general: "通用问题",
};

const categoryColors: Record<string, string> = {
  technical: "bg-blue-100 text-blue-800",
  refund: "bg-orange-100 text-orange-800",
  billing: "bg-green-100 text-green-800",
  general: "bg-purple-100 text-purple-800",
};

export function KnowledgePage() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<string>("");

  useEffect(() => {
    loadArticles();
  }, [category]);

  async function loadArticles() {
    try {
      setLoading(true);
      const data = await api.getKnowledge(category || undefined);
      setArticles(data.items);
    } catch (error) {
      console.error("Failed to load knowledge articles:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">知识库管理</h1>
        <p className="text-gray-600">管理常见问题和解决方案</p>
      </div>

      {/* 筛选栏 */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">所有分类</option>
            <option value="technical">技术支持</option>
            <option value="refund">退款政策</option>
            <option value="billing">账单相关</option>
            <option value="general">通用问题</option>
          </select>
          <div className="flex-1"></div>
          <span className="text-gray-600">共 {articles.length} 篇文章</span>
        </div>
      </div>

      {/* 文章列表 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center p-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center p-12 text-gray-500">
            <p className="text-4xl mb-4">📚</p>
            <p>暂无知识库文章</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  标题
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  分类
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  浏览量
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  创建时间
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {articles.map((article) => (
                <tr key={article.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <p className="font-medium text-gray-900">{article.title}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        categoryColors[article.category] || "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {categoryLabels[article.category] || article.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    {article.view_count}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        article.is_published
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {article.is_published ? "已发布" : "草稿"}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(article.created_at).toLocaleDateString("zh-CN")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
