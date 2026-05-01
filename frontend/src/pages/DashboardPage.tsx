import { useState, useEffect } from "react";
import { api } from "../services/api";

interface MetricCard {
  label: string;
  value: string;
  icon: string;
  color: string;
}

export default function DashboardPage() {
  const [health, setHealth] = useState<string>("checking...");

  useEffect(() => {
    api
      .healthCheck()
      .then((data) => setHealth(data.status))
      .catch(() => setHealth("unavailable"));
  }, []);

  const metrics: MetricCard[] = [
    { label: "系统状态", value: health, icon: "🟢", color: "bg-green-50" },
    { label: "总对话数", value: "—", icon: "💬", color: "bg-blue-50" },
    { label: "AI解决率", value: "—", icon: "🤖", color: "bg-purple-50" },
    { label: "平均响应", value: "—", icon: "⚡", color: "bg-yellow-50" },
    { label: "待审批", value: "—", icon: "⏳", color: "bg-orange-50" },
    { label: "Token用量", value: "—", icon: "📊", color: "bg-gray-50" },
  ];

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">数据看板</h1>

        <div className="grid grid-cols-3 gap-4 mb-8">
          {metrics.map((m) => (
            <div
              key={m.label}
              className={`${m.color} rounded-xl p-6 border flex items-center gap-4`}
            >
              <span className="text-3xl">{m.icon}</span>
              <div>
                <p className="text-sm text-gray-600">{m.label}</p>
                <p className="text-2xl font-bold">{m.value}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h2 className="font-semibold mb-4">Agent 性能概览</h2>
          <div className="space-y-4">
            {["router", "billing", "technical", "refund", "general"].map((name) => (
              <div key={name} className="flex items-center gap-4">
                <span className="w-20 text-sm font-medium capitalize">{name}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-3">
                  <div
                    className="bg-blue-500 rounded-full h-3 transition-all"
                    style={{ width: `${Math.random() * 60 + 20}%` }}
                  />
                </div>
                <span className="text-sm text-gray-500 w-16 text-right">—</span>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 bg-white rounded-lg border shadow-sm p-6">
          <h2 className="font-semibold mb-4">意图分布</h2>
          <div className="grid grid-cols-5 gap-4 text-center">
            {[
              { name: "账单", color: "bg-green-400" },
              { name: "技术", color: "bg-blue-400" },
              { name: "退款", color: "bg-orange-400" },
              { name: "通用", color: "bg-gray-400" },
              { name: "人工", color: "bg-red-400" },
            ].map((item) => (
              <div key={item.name} className="flex flex-col items-center gap-2">
                <div
                  className={`${item.color} w-16 h-16 rounded-full flex items-center justify-center text-white font-bold`}
                >
                  —
                </div>
                <span className="text-sm">{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
