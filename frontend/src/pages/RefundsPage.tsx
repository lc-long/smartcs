import { useEffect, useState } from "react";
import { api } from "../services/api";

interface Refund {
  id: string;
  refund_no: string;
  order_id: string;
  customer_id: string;
  amount: number;
  reason: string;
  status: string;
  approved_by: string | null;
  created_at: string;
}

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
};

const statusLabels: Record<string, string> = {
  pending: "待审批",
  approved: "已批准",
  rejected: "已拒绝",
};

export function RefundsPage() {
  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    loadRefunds();
  }, [page, status]);

  async function loadRefunds() {
    try {
      setLoading(true);
      const data = await api.getRefunds({
        page,
        page_size: 20,
        status: status || undefined,
      });
      setRefunds(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to load refunds:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(id: string) {
    if (!confirm("确定批准此退款申请？")) return;
    try {
      await api.approveRefund(id);
      loadRefunds();
    } catch (error) {
      console.error("Failed to approve refund:", error);
    }
  }

  async function handleReject(id: string) {
    const reason = prompt("请输入拒绝原因：");
    if (reason === null) return;
    try {
      await api.rejectRefund(id, reason);
      loadRefunds();
    } catch (error) {
      console.error("Failed to reject refund:", error);
    }
  }

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">退款管理</h1>
        <p className="text-gray-600">审批和管理退款申请</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">待审批</p>
              <p className="text-2xl font-bold text-yellow-600">
                {refunds.filter((r) => r.status === "pending").length}
              </p>
            </div>
            <div className="text-3xl">⏳</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">已批准</p>
              <p className="text-2xl font-bold text-green-600">
                {refunds.filter((r) => r.status === "approved").length}
              </p>
            </div>
            <div className="text-3xl">✅</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">已拒绝</p>
              <p className="text-2xl font-bold text-red-600">
                {refunds.filter((r) => r.status === "rejected").length}
              </p>
            </div>
            <div className="text-3xl">❌</div>
          </div>
        </div>
      </div>

      {/* 筛选栏 */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">所有状态</option>
            <option value="pending">待审批</option>
            <option value="approved">已批准</option>
            <option value="rejected">已拒绝</option>
          </select>
          <div className="flex-1"></div>
          <span className="text-gray-600">共 {total} 条退款记录</span>
        </div>
      </div>

      {/* 退款列表 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center p-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : refunds.length === 0 ? (
          <div className="text-center p-12 text-gray-500">
            <p className="text-4xl mb-4">💸</p>
            <p>暂无退款记录</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  退款单号
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  订单号
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  客户
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  金额
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  原因
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  时间
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {refunds.map((refund) => (
                <tr key={refund.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">
                    {refund.refund_no}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {refund.order_id}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {refund.customer_id}
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-900">
                    ¥{refund.amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-sm text-gray-600 truncate max-w-xs">
                      {refund.reason}
                    </p>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        statusColors[refund.status]
                      }`}
                    >
                      {statusLabels[refund.status]}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(refund.created_at).toLocaleDateString("zh-CN")}
                  </td>
                  <td className="px-6 py-4">
                    {refund.status === "pending" && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApprove(refund.id)}
                          className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600"
                        >
                          批准
                        </button>
                        <button
                          onClick={() => handleReject(refund.id)}
                          className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
                        >
                          拒绝
                        </button>
                      </div>
                    )}
                    {refund.status !== "pending" && refund.approved_by && (
                      <span className="text-sm text-gray-600">
                        {refund.approved_by}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 分页 */}
        <div className="px-6 py-4 bg-gray-50 border-t flex items-center justify-between">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
          >
            上一页
          </button>
          <span className="text-gray-600">
            第 {page} 页，共 {Math.ceil(total / 20)} 页
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page * 20 >= total}
            className="px-4 py-2 border rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
}
