import { useEffect, useState } from "react";
import { api } from "../services/api";

interface LogisticsStats {
  status_distribution: Record<string, number>;
  carrier_distribution: Record<string, number>;
  avg_delivery_days: number;
  in_transit_count: number;
}

const statusLabels: Record<string, string> = {
  pending: "待揽收",
  shipped: "已发货",
  in_transit: "运输中",
  delivered: "已送达",
};

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  shipped: "bg-blue-100 text-blue-800",
  in_transit: "bg-purple-100 text-purple-800",
  delivered: "bg-green-100 text-green-800",
};

export function LogisticsPage() {
  const [stats, setStats] = useState<LogisticsStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      const data = await api.getLogisticsStats();
      setStats(data);
    } catch (error) {
      console.error("Failed to load logistics stats:", error);
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

  const totalShipments = Object.values(stats.status_distribution).reduce(
    (sum, count) => sum + count,
    0
  );

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">物流统计</h1>
        <p className="text-gray-600">物流配送数据分析</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6 border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">总包裹数</p>
              <p className="text-2xl font-bold text-gray-900">{totalShipments}</p>
            </div>
            <div className="text-4xl">📦</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">运输中</p>
              <p className="text-2xl font-bold text-purple-600">
                {stats.in_transit_count}
              </p>
            </div>
            <div className="text-4xl">🚚</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">平均配送天数</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.avg_delivery_days} 天
              </p>
            </div>
            <div className="text-4xl">⏱️</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6 border border-orange-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">快递公司数</p>
              <p className="text-2xl font-bold text-orange-600">
                {Object.keys(stats.carrier_distribution).length}
              </p>
            </div>
            <div className="text-4xl">🏢</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 物流状态分布 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">物流状态分布</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(stats.status_distribution).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        statusColors[status] || "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {statusLabels[status] || status}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(count / totalShipments) * 100}%`,
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

        {/* 快递公司分布 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">快递公司分布</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {Object.entries(stats.carrier_distribution).map(([carrier, count]) => (
                <div key={carrier} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">🏢</span>
                    <span className="font-medium text-gray-900">{carrier}</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{
                          width: `${(count / totalShipments) * 100}%`,
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
      </div>
    </div>
  );
}
