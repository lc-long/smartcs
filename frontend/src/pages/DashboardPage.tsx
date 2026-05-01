import { useEffect, useState } from "react";
import { api } from "../services/api";

interface DashboardStats {
  summary: {
    total_products: number;
    total_customers: number;
    total_orders: number;
    total_revenue: number;
    pending_orders: number;
    pending_refunds: number;
    open_tickets: number;
  };
  recent_orders: Array<{
    order_no: string;
    customer_id: string;
    amount: number;
    status: string;
    created_at: string;
  }>;
  hot_products: Array<{
    name: string;
    count: number;
    total: number;
  }>;
}

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  processing: "bg-blue-100 text-blue-800",
  shipped: "bg-purple-100 text-purple-800",
  delivered: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

const statusLabels: Record<string, string> = {
  pending: "待处理",
  processing: "处理中",
  shipped: "已发货",
  delivered: "已送达",
  cancelled: "已取消",
};

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      const data = await api.getDashboardStats();
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
          title="总商品"
          value={stats.summary.total_products}
          icon="🛍️"
          color="orange"
        />
      </div>

      {/* 待处理事项 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">待处理订单</p>
              <p className="text-3xl font-bold text-yellow-600">
                {stats.summary.pending_orders}
              </p>
            </div>
            <div className="text-4xl">⏳</div>
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
              <p className="text-sm text-gray-600">待处理工单</p>
              <p className="text-3xl font-bold text-blue-600">
                {stats.summary.open_tickets}
              </p>
            </div>
            <div className="text-4xl">🎫</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 最近订单 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">最近订单</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {stats.recent_orders.map((order, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">{order.order_no}</p>
                    <p className="text-sm text-gray-600">{order.customer_id}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">
                      ¥{order.amount.toLocaleString()}
                    </p>
                    <span
                      className={`inline-block px-2 py-1 text-xs rounded-full ${
                        statusColors[order.status] || "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {statusLabels[order.status] || order.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 热门商品 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">热门商品</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {stats.hot_products.map((product, index) => (
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
                      <p className="text-sm text-gray-600">{product.count} 笔订单</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">
                      ¥{product.total.toLocaleString()}
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
