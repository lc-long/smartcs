import { useEffect, useState } from "react";
import { api } from "../services/api";

interface SatisfactionStats {
  review_summary: {
    total_reviews: number;
    avg_rating: number;
    positive_rate: number;
    negative_rate: number;
  };
  rating_distribution: Record<number, number>;
  feedback_distribution: Record<string, number>;
  feedback_status: Record<string, number>;
  ticket_category_distribution: Record<string, number>;
  ticket_priority_distribution: Record<string, number>;
}

const feedbackTypeLabels: Record<string, string> = {
  complaint: "投诉",
  suggestion: "建议",
  praise: "表扬",
  question: "咨询",
};

const feedbackTypeColors: Record<string, string> = {
  complaint: "bg-red-100 text-red-800",
  suggestion: "bg-blue-100 text-blue-800",
  praise: "bg-green-100 text-green-800",
  question: "bg-yellow-100 text-yellow-800",
};

const feedbackStatusLabels: Record<string, string> = {
  pending: "待处理",
  in_review: "审核中",
  resolved: "已解决",
  closed: "已关闭",
};

const feedbackStatusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  in_review: "bg-blue-100 text-blue-800",
  resolved: "bg-green-100 text-green-800",
  closed: "bg-gray-100 text-gray-800",
};

const priorityLabels: Record<string, string> = {
  low: "低",
  medium: "中",
  high: "高",
  critical: "紧急",
};

const priorityColors: Record<string, string> = {
  low: "bg-gray-100 text-gray-800",
  medium: "bg-blue-100 text-blue-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

export function FeedbackPage() {
  const [stats, setStats] = useState<SatisfactionStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      const data = await api.getCustomerSatisfaction();
      setStats(data);
    } catch (error) {
      console.error("Failed to load satisfaction stats:", error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        加载失败
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">客户满意度</h1>
        <p className="text-gray-600">客户评价与反馈分析</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6 border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">总评价数</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.review_summary.total_reviews}
              </p>
            </div>
            <div className="text-4xl">📝</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">平均评分</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.review_summary.avg_rating.toFixed(1)} ⭐
              </p>
            </div>
            <div className="text-4xl">⭐</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">好评率</p>
              <p className="text-2xl font-bold text-purple-600">
                {stats.review_summary.positive_rate}%
              </p>
            </div>
            <div className="text-4xl">😊</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">差评率</p>
              <p className="text-2xl font-bold text-red-600">
                {stats.review_summary.negative_rate}%
              </p>
            </div>
            <div className="text-4xl">😞</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* 评分分布 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">评分分布</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {[5, 4, 3, 2, 1].map((rating) => {
                const count = stats.rating_distribution[rating] || 0;
                const total = stats.review_summary.total_reviews;
                const percentage = total > 0 ? (count / total) * 100 : 0;
                return (
                  <div key={rating} className="flex items-center">
                    <span className="w-12 text-sm text-gray-600">{rating} 星</span>
                    <div className="flex-1 mx-3">
                      <div className="w-full bg-gray-200 rounded-full h-4">
                        <div
                          className="bg-yellow-400 h-4 rounded-full"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                    <span className="w-12 text-right text-sm font-medium">
                      {count}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* 反馈类型分布 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">反馈类型分布</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(stats.feedback_distribution).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      feedbackTypeColors[type] || "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {feedbackTypeLabels[type] || type}
                  </span>
                  <span className="font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 反馈状态 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">反馈状态</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(stats.feedback_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      feedbackStatusColors[status] || "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {feedbackStatusLabels[status] || status}
                  </span>
                  <span className="font-medium text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 工单优先级分布 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">工单优先级分布</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(stats.ticket_priority_distribution).map(
                ([priority, count]) => (
                  <div key={priority} className="flex items-center justify-between">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        priorityColors[priority] || "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {priorityLabels[priority] || priority}
                    </span>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
