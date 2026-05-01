import { Routes, Route, Link, useLocation } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import AdminPage from "./pages/AdminPage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  const location = useLocation();

  const navItems = [
    { path: "/", label: "对话", icon: "💬" },
    { path: "/admin", label: "管理", icon: "⚙️" },
    { path: "/dashboard", label: "看板", icon: "📊" },
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

      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </main>
    </div>
  );
}
