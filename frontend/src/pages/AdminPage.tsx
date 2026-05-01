import { useState, useEffect } from "react";
import { api } from "../services/api";
import type { ApprovalItem } from "../types";

export default function AdminPage() {
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchApprovals = async () => {
    try {
      const data = await api.getApprovals();
      setApprovals(data.items as ApprovalItem[]);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
    const interval = setInterval(fetchApprovals, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDecision = async (id: string, decision: string) => {
    try {
      await api.decideApproval(id, decision, decision === "approve" ? "同意" : "拒绝");
      fetchApprovals();
    } catch {
      alert("操作失败");
    }
  };

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">审批管理</h1>

        <div className="bg-white rounded-lg border shadow-sm">
          <div className="px-6 py-4 border-b">
            <h2 className="font-semibold">待审批列表</h2>
            <p className="text-sm text-gray-500">需要人工审批的高风险操作</p>
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-400">加载中...</div>
          ) : approvals.length === 0 ? (
            <div className="p-8 text-center text-gray-400">
              <p className="text-3xl mb-2">✅</p>
              <p>暂无待审批事项</p>
            </div>
          ) : (
            <div className="divide-y">
              {approvals.map((item) => (
                <div key={item.id} className="px-6 py-4 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          item.risk_level === "high"
                            ? "bg-red-100 text-red-700"
                            : "bg-yellow-100 text-yellow-700"
                        }`}
                      >
                        {item.risk_level === "high" ? "高风险" : "中风险"}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="font-medium">{item.action_description}</p>
                    <p className="text-sm text-gray-500">
                      客户: {item.customer_id} · Agent: {item.agent_name}
                    </p>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDecision(item.id, "approve")}
                      className="px-4 py-2 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600"
                    >
                      批准
                    </button>
                    <button
                      onClick={() => handleDecision(item.id, "reject")}
                      className="px-4 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600"
                    >
                      拒绝
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
