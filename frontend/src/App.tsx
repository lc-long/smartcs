import { Routes, Route, Link, useLocation } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import AdminPage from "./pages/AdminPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProductsPage } from "./pages/ProductsPage";
import { OrdersPage } from "./pages/OrdersPage";
import { CustomersPage } from "./pages/CustomersPage";

export default function App() {
  const location = useLocation();

  const navItems = [
    { path: "/", label: "对话", icon: "💬" },
    { path: "/dashboard", label: "看板", icon: "📊" },
    { path: "/products", label: "商品", icon: "🛍️" },
    { path: "/orders", label: "订单", icon: "📦" },
    { path: "/customers", label: "客户", icon: "👥" },
    { path: "/admin", label: "管理", icon: "⚙️" },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <nav className="w-16 bg-white border-r flex flex-col items-center py-4 gap-2">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`w-12 h-12 flex items-center justify-center rounded-lg text-xl transition-colors ${
              location.pathname === item.path
                ? "bg-blue-100 text-blue-600"
                : "hover:bg-gray-100"
            }`}
            title={item.label}
          >
            {item.icon}
          </Link>
        ))}
      </nav>

      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </div>
  );
}
