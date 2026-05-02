import { useEffect, useState } from "react";
import { api } from "../services/api";

interface DashboardStats {
  summary: {
    total_customers: number;
    total_orders: number;
    total_revenue: number;
    today_orders: number;
    pending_tickets: number;
    pending_refunds: number;
    avg_order_amount: number;
    avg_rating: number;
  };
  order_trend: Array<{
    date: string;
    count: number;
    amount: number;
  }>;
  order_status_distribution: Record<string, number>;
  top_products: Array<{
    name: string;
    quantity: number;
    amount: number;
  }>;
}

const statusLabels: Record<string, string> = {
  pending: "待处理",
  processing: "处理中",
  shipped: "已发货",
  delivered: "已送达",
  cancelled: "已取消",
};

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  processing: "bg-blue-100 text-blue-800",
  shipped: "bg-purple-100 text-purple-800",
  delivered: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      const data = await api.getAnalyticsDashboard();
      setStats(data);
    } catch (error) {
      console.error("Failed to load stats:", error);
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
        <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>
        <p className="text-gray-600">智能客服系统运行概览</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="总订单"
          value={stats.summary.total_orders}
          icon="📦"
          color="blue"
        />
        <StatCard
          title="总收入"
          value={`¥${stats.summary.total_revenue.toLocaleString()}`}
          icon="💰"
          color="green"
        />
        <StatCard
          title="总客户"
          value={stats.summary.total_customers}
          icon="👥"
          color="purple"
        />
        <StatCard
          title="今日订单"
          value={stats.summary.today_orders}
          icon="📈"
          color="orange"
        />
      </div>

      {/* 待处理事项 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">待处理工单</p>
              <p className="text-3xl font-bold text-yellow-600">
                {stats.summary.pending_tickets}
              </p>
            </div>
            <div className="text-4xl">🎫</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">待处理退款</p>
              <p className="text-3xl font-bold text-red-600">
                {stats.summary.pending_refunds}
              </p>
            </div>
            <div className="text-4xl">💸</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">平均订单金额</p>
              <p className="text-3xl font-bold text-blue-600">
                ¥{stats.summary.avg_order_amount.toLocaleString()}
              </p>
            </div>
            <div className="text-4xl">📊</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">客户满意度</p>
              <p className="text-3xl font-bold text-green-600">
                {stats.summary.avg_rating.toFixed(1)} ⭐
              </p>
            </div>
            <div className="text-4xl">😊</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 订单状态分布 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">订单状态分布</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(stats.order_status_distribution).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className={`px-2 py-1 text-xs rounded-full ${statusColors[status] || "bg-gray-100 text-gray-800"}`}>
                      {statusLabels[status] || status}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(count / stats.summary.total_orders) * 100}%`,
                        }}
                      ></div>
                    </div>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 热销商品 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">热销商品 Top 5</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {stats.top_products.map((product, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">
                      {index === 0 ? "🥇" : index === 1 ? "🥈" : index === 2 ? "🥉" : "📦"}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900">{product.name}</p>
                      <p className="text-sm text-gray-600">{product.quantity} 件</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">
                      ¥{product.amount.toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: string;
  color: string;
}) {
  const colorClasses: Record<string, string> = {
    blue: "bg-blue-50 border-blue-200",
    green: "bg-green-50 border-green-200",
    purple: "bg-purple-50 border-purple-200",
    orange: "bg-orange-50 border-orange-200",
  };

  return (
    <div
      className={`rounded-lg shadow p-6 border ${
        colorClasses[color] || "bg-white border-gray-200"
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  );
}
