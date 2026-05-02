import { Routes, Route, Link, useLocation, Navigate, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
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
import { LogisticsPage } from "./pages/LogisticsPage";
import { FeedbackPage } from "./pages/FeedbackPage";
import {
  MessageSquare, BarChart3, Truck, SmilePlus, ShoppingBag, Package,
  Users, Wallet, BookOpen, ShieldCheck, LogOut, Zap, Globe,
} from "lucide-react";
import { useState } from "react";

function ProtectedRoute({ requiredRole }: { requiredRole?: string }) {
  const { user, isLoading } = useAuth();
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-zinc-950">
        <div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  if (requiredRole) {
    const h = { admin: 3, agent: 2, viewer: 1 };
    if ((h[user.role] || 0) < (h[requiredRole as keyof typeof h] || 0)) {
      return (
        <div className="flex items-center justify-center h-screen bg-zinc-950">
          <div className="text-center">
            <ShieldCheck className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
            <p className="text-sm font-medium text-zinc-300">{t("auth.accessDenied")}</p>
            <p className="text-xs text-zinc-500 mt-1">{t("auth.accessDeniedDesc")}</p>
          </div>
        </div>
      );
    }
  }

  return <Outlet />;
}

function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const langs = [{ code: "zh", label: "中文" }, { code: "en", label: "English" }];
  const current = langs.find((l) => l.code === i18n.language) || langs[0];

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 transition-colors text-xs cursor-pointer w-full">
        <Globe className="w-3.5 h-3.5" />
        <span>{current.label}</span>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute bottom-full left-0 mb-1 w-28 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl z-50 py-1">
            {langs.map((lang) => (
              <button key={lang.code} onClick={() => { i18n.changeLanguage(lang.code); setOpen(false); }}
                className={`w-full px-3 py-1.5 text-left text-xs cursor-pointer transition-colors ${i18n.language === lang.code ? "text-indigo-400" : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700"}`}>
                {lang.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function AppLayout() {
  const { user, logout, isAgent, canApprove } = useAuth();
  const location = useLocation();
  const { t } = useTranslation();

  const navItems = [
    { path: "/", label: t("nav.chat"), icon: MessageSquare, group: t("nav.service"), show: true },
    { path: "/dashboard", label: t("nav.dashboard"), icon: BarChart3, group: t("nav.analytics"), show: true },
    { path: "/logistics", label: t("nav.logistics"), icon: Truck, group: t("nav.analytics"), show: isAgent },
    { path: "/feedback", label: t("nav.feedback"), icon: SmilePlus, group: t("nav.analytics"), show: isAgent },
    { path: "/products", label: t("nav.products"), icon: ShoppingBag, group: t("nav.commerce"), show: true },
    { path: "/orders", label: t("nav.orders"), icon: Package, group: t("nav.commerce"), show: true },
    { path: "/customers", label: t("nav.customers"), icon: Users, group: t("nav.commerce"), show: true },
    { path: "/refunds", label: t("nav.refunds"), icon: Wallet, group: t("nav.commerce"), show: isAgent },
    { path: "/knowledge", label: t("nav.knowledge"), icon: BookOpen, group: t("nav.system"), show: true },
    { path: "/admin", label: t("nav.approvals"), icon: ShieldCheck, group: t("nav.system"), show: canApprove },
  ].filter((i) => i.show);

  const groups = navItems.reduce((acc, item) => {
    if (!acc[item.group]) acc[item.group] = [];
    acc[item.group].push(item);
    return acc;
  }, {} as Record<string, typeof navItems>);

  const roleLabels: Record<string, string> = { admin: "Admin", agent: "Agent", viewer: "Viewer" };

  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-[220px] bg-zinc-950 flex flex-col flex-shrink-0 border-r border-zinc-800/70">
        <div className="h-14 flex items-center px-4 border-b border-zinc-800/50">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-sm font-bold text-zinc-100 tracking-tight">SmartCS</h1>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-3 px-2">
          {Object.entries(groups).map(([groupName, items]) => (
            <div key={groupName} className="mb-4">
              <p className="px-2 mb-1 text-[10px] font-semibold text-zinc-600 uppercase tracking-widest">{groupName}</p>
              {items.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link key={item.path} to={item.path}
                    className={`group flex items-center gap-2.5 px-2 py-1.5 rounded-md mb-0.5 text-[13px] font-medium transition-all duration-100 cursor-pointer ${isActive ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:bg-zinc-800/60 hover:text-zinc-300"}`}>
                    <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? "text-zinc-300" : "text-zinc-600 group-hover:text-zinc-500"}`} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="border-t border-zinc-800/50 p-2 space-y-1">
          <LanguageSwitcher />
          <div className="flex items-center gap-2.5 px-2 py-1.5">
            <div className="w-6 h-6 rounded-full bg-zinc-800 flex items-center justify-center text-[11px] font-bold text-zinc-400">
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-zinc-300 truncate">{user?.username}</p>
              <p className="text-[10px] text-zinc-600">{roleLabels[user?.role || "viewer"]}</p>
            </div>
            <button onClick={logout} className="p-1 rounded text-zinc-600 hover:text-red-400 transition-colors cursor-pointer" title="Sign out">
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-auto bg-zinc-950">
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
              <Route path="/logistics" element={<LogisticsPage />} />
              <Route path="/feedback" element={<FeedbackPage />} />
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
