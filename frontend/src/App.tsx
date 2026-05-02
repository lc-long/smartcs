import { Routes, Route, Link, useLocation, Navigate, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";
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
  Users, Wallet, BookOpen, ShieldCheck, LogOut, Zap, Globe, Sun, Moon,
} from "lucide-react";
import { useState } from "react";

function ProtectedRoute({ requiredRole }: { requiredRole?: string }) {
  const { user, isLoading } = useAuth();
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: "var(--bg-app)" }}>
        <div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  if (requiredRole) {
    const h = { admin: 3, agent: 2, viewer: 1 };
    if ((h[user.role] || 0) < (h[requiredRole as keyof typeof h] || 0)) {
      return (
        <div className="flex items-center justify-center h-screen" style={{ background: "var(--bg-app)" }}>
          <div className="text-center">
            <ShieldCheck className="w-8 h-8 mx-auto mb-3" style={{ color: "var(--text-muted)" }} />
            <p className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>{t("auth.accessDenied")}</p>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{t("auth.accessDeniedDesc")}</p>
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
        className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs cursor-pointer w-full transition-colors"
        style={{ color: "var(--text-muted)" }}>
        <Globe className="w-3.5 h-3.5" />
        <span>{current.label}</span>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute bottom-full left-0 mb-1 w-28 rounded-lg shadow-xl z-50 py-1"
            style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)" }}>
            {langs.map((lang) => (
              <button key={lang.code} onClick={() => { i18n.changeLanguage(lang.code); setOpen(false); }}
                className="w-full px-3 py-1.5 text-left text-xs cursor-pointer transition-colors"
                style={{ color: i18n.language === lang.code ? "var(--accent)" : "var(--text-secondary)" }}>
                {lang.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button onClick={toggleTheme}
      className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs cursor-pointer w-full transition-colors"
      style={{ color: "var(--text-muted)" }}>
      {theme === "dark" ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
      <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
    </button>
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
    <div className="flex h-screen overflow-hidden" style={{ background: "var(--bg-app)" }}>
      <aside className="w-[220px] flex flex-col flex-shrink-0"
        style={{ background: "var(--sidebar-bg)", borderRight: "1px solid var(--sidebar-border)" }}>
        <div className="h-14 flex items-center px-4" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: "var(--accent)" }}>
              <Zap className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-sm font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>SmartCS</h1>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-3 px-2">
          {Object.entries(groups).map(([groupName, items]) => (
            <div key={groupName} className="mb-4">
              <p className="px-2 mb-1 text-[10px] font-semibold uppercase tracking-widest" style={{ color: "var(--text-dim)" }}>{groupName}</p>
              {items.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link key={item.path} to={item.path}
                    className="group flex items-center gap-2.5 px-2 py-1.5 rounded-md mb-0.5 text-[13px] font-medium transition-all duration-100 cursor-pointer"
                    style={{
                      background: isActive ? "var(--bg-elevated)" : "transparent",
                      color: isActive ? "var(--text-primary)" : "var(--text-muted)",
                    }}>
                    <Icon className="w-4 h-4 flex-shrink-0" style={{ color: isActive ? "var(--text-secondary)" : "var(--text-dim)" }} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="p-2 space-y-1" style={{ borderTop: "1px solid var(--border-subtle)" }}>
          <ThemeToggle />
          <LanguageSwitcher />
          <div className="flex items-center gap-2.5 px-2 py-1.5">
            <div className="w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold"
              style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)" }}>
              {user?.username?.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate" style={{ color: "var(--text-secondary)" }}>{user?.username}</p>
              <p className="text-[10px]" style={{ color: "var(--text-dim)" }}>{roleLabels[user?.role || "viewer"]}</p>
            </div>
            <button onClick={logout} className="p-1 rounded cursor-pointer transition-colors"
              style={{ color: "var(--text-dim)" }} title="Sign out">
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-auto" style={{ background: "var(--bg-app)" }}>
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
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
    </ThemeProvider>
  );
}
