import { Routes, Route, Link, useLocation } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import AdminPage from "./pages/AdminPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProductsPage } from "./pages/ProductsPage";
import { OrdersPage } from "./pages/OrdersPage";
import { CustomersPage } from "./pages/CustomersPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { RefundsPage } from "./pages/RefundsPage";

const navItems = [
  { path: "/", label: "智能客服", icon: "💬", group: "客服" },
  { path: "/dashboard", label: "数据看板", icon: "📊", group: "数据" },
  { path: "/products", label: "商品管理", icon: "🛍️", group: "电商" },
  { path: "/orders", label: "订单管理", icon: "📦", group: "电商" },
  { path: "/customers", label: "客户管理", icon: "👥", group: "电商" },
  { path: "/refunds", label: "退款管理", icon: "💸", group: "电商" },
  { path: "/knowledge", label: "知识库", icon: "📚", group: "系统" },
  { path: "/admin", label: "审批管理", icon: "⚙️", group: "系统" },
];

export default function App() {
  const location = useLocation();

  // 按分组组织导航项
  const groups = navItems.reduce((acc, item) => {
    if (!acc[item.group]) acc[item.group] = [];
    acc[item.group].push(item);
    return acc;
  }, {} as Record<string, typeof navItems>);

  return (
    <div className="flex h-screen bg-gray-50">
      <nav className="w-20 bg-white border-r flex flex-col items-center py-4 gap-1">
        <div className="mb-4">
          <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-lg">
            S
          </div>
        </div>

        {Object.entries(groups).map(([groupName, items]) => (
          <div key={groupName} className="w-full">
            <div className="px-2 py-1">
              <p className="text-[10px] text-gray-400 text-center uppercase">
                {groupName}
              </p>
            </div>
            {items.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`w-full flex flex-col items-center py-2 text-xs transition-colors ${
                  location.pathname === item.path
                    ? "text-blue-600 bg-blue-50"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
                title={item.label}
              >
                <span className="text-xl mb-0.5">{item.icon}</span>
                <span className="truncate max-w-[60px]">{item.label}</span>
              </Link>
            ))}
          </div>
        ))}
      </nav>

      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="/refunds" element={<RefundsPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </div>
  );
}
