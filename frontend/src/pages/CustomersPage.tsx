import { useEffect, useState } from "react";
import { api } from "../services/api";

interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  vip_level: string;
  orders_count: number;
  total_spent: number;
  created_at: string;
}

const vipColors: Record<string, string> = {
  normal: "bg-gray-100 text-gray-800",
  silver: "bg-gray-200 text-gray-900",
  gold: "bg-yellow-100 text-yellow-800",
};

const vipLabels: Record<string, string> = {
  normal: "普通会员",
  silver: "银卡会员",
  gold: "金卡会员",
};

export function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [vipLevel, setVipLevel] = useState<string>("");
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);

  useEffect(() => {
    loadCustomers();
  }, [page, vipLevel]);

  async function loadCustomers() {
    try {
      setLoading(true);
      const data = await api.getCustomers({
        page,
        page_size: 20,
        vip_level: vipLevel || undefined,
      });
      setCustomers(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error("Failed to load customers:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">客户管理</h1>
        <p className="text-gray-600">查看所有客户信息</p>
      </div>

      {/* 筛选栏 */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <select
            value={vipLevel}
            onChange={(e) => {
              setVipLevel(e.target.value);
              setPage(1);
            }}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">所有会员等级</option>
            <option value="normal">普通会员</option>
            <option value="silver">银卡会员</option>
            <option value="gold">金卡会员</option>
          </select>
          <div className="flex-1"></div>
          <span className="text-gray-600">共 {total} 位客户</span>
        </div>
      </div>

      {/* 客户列表 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center p-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  客户
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  联系方式
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  会员等级
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  订单数
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  消费总额
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  注册时间
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {customers.map((customer) => (
                <tr key={customer.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <button
                        onClick={() => setSelectedCustomer(customer)}
                        className="font-medium text-blue-600 hover:underline"
                      >
                        {customer.name}
                      </button>
                      <p className="text-sm text-gray-600">{customer.id}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm">
                      <p className="text-gray-900">{customer.email}</p>
                      <p className="text-gray-600">{customer.phone}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        vipColors[customer.vip_level] || "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {vipLabels[customer.vip_level] || customer.vip_level}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-900">
                    {customer.orders_count}
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-900">
                    ¥{customer.total_spent.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(customer.created_at).toLocaleDateString("zh-CN")}
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

      {/* 客户详情弹窗 */}
      {selectedCustomer && (
        <CustomerDetailModal
          customer={selectedCustomer}
          onClose={() => setSelectedCustomer(null)}
        />
      )}
    </div>
  );
}

function CustomerDetailModal({
  customer,
  onClose,
}: {
  customer: Customer;
  onClose: () => void;
}) {
  const [details, setDetails] = useState<{
    orders: Array<{
      order_no: string;
      amount: number;
      status: string;
      created_at: string;
    }>;
    tickets: Array<{
      ticket_no: string;
      title: string;
      status: string;
      created_at: string;
    }>;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDetails();
  }, [customer.id]);

  async function loadDetails() {
    try {
      const data = await api.getCustomer(customer.id);
      setDetails({
        orders: data.orders,
        tickets: data.tickets,
      });
    } catch (error) {
      console.error("Failed to load customer details:", error);
    } finally {
      setLoading(false);
    }
  }

  const orderStatusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    processing: "bg-blue-100 text-blue-800",
    shipped: "bg-purple-100 text-purple-800",
    delivered: "bg-green-100 text-green-800",
    cancelled: "bg-red-100 text-red-800",
  };

  const orderStatusLabels: Record<string, string> = {
    pending: "待处理",
    processing: "处理中",
    shipped: "已发货",
    delivered: "已送达",
    cancelled: "已取消",
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold">客户详情</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>
        <div className="p-6">
          {/* 基本信息 */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-600">姓名</p>
              <p className="font-medium">{customer.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">会员等级</p>
              <span
                className={`px-2 py-1 text-xs rounded-full ${
                  vipColors[customer.vip_level]
                }`}
              >
                {vipLabels[customer.vip_level]}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-600">邮箱</p>
              <p className="font-medium">{customer.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">电话</p>
              <p className="font-medium">{customer.phone}</p>
            </div>
          </div>

          <div className="mb-6">
            <p className="text-sm text-gray-600 mb-2">地址</p>
            <p className="p-3 bg-gray-50 rounded">{customer.address}</p>
          </div>

          {/* 最近订单 */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3">最近订单</h3>
            {loading ? (
              <div className="flex items-center justify-center p-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
              </div>
            ) : details?.orders && details.orders.length > 0 ? (
              <div className="space-y-2">
                {details.orders.map((order, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded"
                  >
                    <div>
                      <p className="font-medium text-sm">{order.order_no}</p>
                      <p className="text-xs text-gray-600">
                        {new Date(order.created_at).toLocaleDateString("zh-CN")}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-sm">
                        ¥{order.amount.toLocaleString()}
                      </p>
                      <span
                        className={`px-2 py-0.5 text-xs rounded-full ${
                          orderStatusColors[order.status]
                        }`}
                      >
                        {orderStatusLabels[order.status]}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 text-sm">暂无订单</p>
            )}
          </div>

          {/* 最近工单 */}
          <div>
            <h3 className="font-medium text-gray-900 mb-3">最近工单</h3>
            {details?.tickets && details.tickets.length > 0 ? (
              <div className="space-y-2">
                {details.tickets.map((ticket, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded"
                  >
                    <div>
                      <p className="font-medium text-sm">{ticket.ticket_no}</p>
                      <p className="text-xs text-gray-600">{ticket.title}</p>
                    </div>
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full ${
                        ticket.status === "open"
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-green-100 text-green-800"
                      }`}
                    >
                      {ticket.status === "open" ? "待处理" : "已解决"}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 text-sm">暂无工单</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
