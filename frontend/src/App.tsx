import { Routes, Route, Link, useLocation, Navigate, Outlet } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { LoginPage } from "./pages/LoginPage";
import ChatPage from "./pages/ChatPage";
import AdminPage from "./pages/AdminPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProductsPage } from "./pages/ProductsPage";
import { OrdersPage } from "./pages/OrdersPage";
import { CustomersPage } from "./pages/CustomersPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { RefundsPage } from "./pages/RefundsPage";

// 路由保护组件
function ProtectedRoute({ requiredRole }: { requiredRole?: string }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    const roleHierarchy = { admin: 3, agent: 2, viewer: 1 };
    const userLevel = roleHierarchy[user.role] || 0;
    const requiredLevel = roleHierarchy[requiredRole as keyof typeof roleHierarchy] || 0;

    if (userLevel < requiredLevel) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <p className="text-4xl mb-4">🚫</p>
            <p className="text-xl font-semibold">权限不足</p>
            <p className="text-gray-600 mt-2">您没有访问此页面的权限</p>
          </div>
        </div>
      );
    }
  }

  return <Outlet />;
}

// 导航布局组件
function AppLayout() {
  const { user, logout, isAgent, canApprove } = useAuth();
  const location = useLocation();

  const navItems = [
    { path: "/", label: "智能客服", icon: "💬", group: "客服", show: true },
    { path: "/dashboard", label: "数据看板", icon: "📊", group: "数据", show: true },
    { path: "/products", label: "商品管理", icon: "🛍️", group: "电商", show: true },
    { path: "/orders", label: "订单管理", icon: "📦", group: "电商", show: true },
    { path: "/customers", label: "客户管理", icon: "👥", group: "电商", show: true },
    { path: "/refunds", label: "退款管理", icon: "💸", group: "电商", show: isAgent },
    { path: "/knowledge", label: "知识库", icon: "📚", group: "系统", show: true },
    { path: "/admin", label: "审批管理", icon: "⚙️", group: "系统", show: canApprove },
  ].filter((item) => item.show);

  const groups = navItems.reduce((acc, item) => {
    if (!acc[item.group]) acc[item.group] = [];
    acc[item.group].push(item);
    return acc;
  }, {} as Record<string, typeof navItems>);

  const roleLabels: Record<string, string> = {
    admin: "管理员",
    agent: "客服",
    viewer: "访客",
  };

  const roleColors: Record<string, string> = {
    admin: "bg-red-100 text-red-800",
    agent: "bg-blue-100 text-blue-800",
    viewer: "bg-gray-100 text-gray-800",
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <nav className="w-24 bg-white border-r flex flex-col items-center py-4 gap-1 overflow-y-auto flex-shrink-0">
        <div className="mb-4 flex-shrink-0">
          <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-lg">
            S
          </div>
        </div>

        {Object.entries(groups).map(([groupName, items]) => (
          <div key={groupName} className="w-full flex-shrink-0">
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
                <span className="truncate max-w-[72px]">{item.label}</span>
              </Link>
            ))}
          </div>
        ))}

        <div className="flex-1"></div>

        {/* 用户信息 */}
        <div className="w-full px-2 py-2 border-t flex-shrink-0">
          <div className="text-center mb-2">
            <span className={`text-xs px-2 py-0.5 rounded-full ${roleColors[user?.role || "viewer"]}`}>
              {roleLabels[user?.role || "viewer"]}
            </span>
          </div>
          <p className="text-xs text-gray-600 text-center truncate mb-2">
            {user?.username}
          </p>
          <button
            onClick={logout}
            className="w-full text-xs text-red-600 hover:text-red-800 py-1"
          >
            退出
          </button>
        </div>
      </nav>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<ChatPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/customers" element={<CustomersPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route element={<ProtectedRoute requiredRole="agent" />}>
              <Route path="/refunds" element={<RefundsPage />} />
            </Route>
            <Route element={<ProtectedRoute requiredRole="admin" />}>
              <Route path="/admin" element={<AdminPage />} />
            </Route>
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  );
}
