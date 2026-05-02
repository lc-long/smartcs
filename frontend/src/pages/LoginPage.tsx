import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { Zap, Eye, EyeOff, ArrowRight, Globe, Sun, Moon } from "lucide-react";
import i18n from "../i18n";

export function LoginPage() {
  const { login, user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  if (user) { navigate("/", { replace: true }); return null; }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setError(""); setLoading(true);
    try { await login(username, password); navigate("/", { replace: true }); }
    catch (err: any) { setError(err.message || t("auth.loginFailed")); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen flex" style={{ background: "var(--bg-app)" }}>
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden"
        style={{ background: "var(--bg-surface)", borderRight: "1px solid var(--border)" }}>
        <div className="absolute inset-0 opacity-[0.04]" style={{ backgroundImage: "radial-gradient(circle at 25% 25%, var(--text-primary) 1px, transparent 1px), radial-gradient(circle at 75% 75%, var(--text-primary) 1px, transparent 1px)", backgroundSize: "40px 40px" }} />
        <div className="relative z-10 flex flex-col justify-center px-14">
          <div className="flex items-center gap-2.5 mb-10">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: "var(--accent)" }}><Zap className="w-5 h-5 text-white" /></div>
            <div><h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>SmartCS</h1><p className="text-[11px]" style={{ color: "var(--text-dim)" }}>AI Customer Service</p></div>
          </div>
          <h2 className="text-3xl font-bold leading-tight mb-5" style={{ color: "var(--text-primary)" }}>{t("auth.brandTitle")}</h2>
          <p className="text-sm max-w-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>{t("auth.brandDesc")}</p>
          <div className="mt-10 flex items-center gap-6">
            <div><p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>99.5%</p><p className="text-[11px]" style={{ color: "var(--text-dim)" }}>{t("auth.resolutionRate")}</p></div>
            <div className="w-px h-8" style={{ background: "var(--border)" }} />
            <div><p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>&lt;3s</p><p className="text-[11px]" style={{ color: "var(--text-dim)" }}>{t("auth.avgResponse")}</p></div>
            <div className="w-px h-8" style={{ background: "var(--border)" }} />
            <div><p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>24/7</p><p className="text-[11px]" style={{ color: "var(--text-dim)" }}>{t("auth.availability")}</p></div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8" style={{ background: "var(--bg-app)" }}>
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2.5 mb-8">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: "var(--accent)" }}><Zap className="w-4 h-4 text-white" /></div>
            <h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>SmartCS</h1>
          </div>
          <div className="mb-6">
            <h2 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>{t("auth.welcomeBack")}</h2>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{t("auth.signInSubtitle")}</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="px-3 py-2 rounded-lg text-xs" style={{ background: "rgba(239,68,68,0.1)", color: "var(--error)", border: "1px solid rgba(239,68,68,0.2)" }}>{error}</div>}
            <div>
              <label className="block text-xs font-semibold mb-1" style={{ color: "var(--text-secondary)" }}>{t("auth.username")}</label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder={t("auth.usernamePlaceholder")}
                className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 transition-all"
                style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-primary)" }} required />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1" style={{ color: "var(--text-secondary)" }}>{t("auth.password")}</label>
              <div className="relative">
                <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t("auth.passwordPlaceholder")}
                  className="w-full rounded-lg px-3 py-2 pr-9 text-sm focus:outline-none focus:ring-2 transition-all"
                  style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-primary)" }} required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-2.5 top-1/2 -translate-y-1/2 cursor-pointer" style={{ color: "var(--text-muted)" }}>
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-2 rounded-lg font-semibold text-sm text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 cursor-pointer"
              style={{ background: "var(--accent)" }}>
              {loading ? <><div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />{t("auth.signingIn")}</> : <>{t("auth.signIn")}<ArrowRight className="w-3.5 h-3.5" /></>}
            </button>
          </form>
          <div className="mt-6 pt-5" style={{ borderTop: "1px solid var(--border-subtle)" }}>
            <p className="text-[10px] font-semibold mb-2.5 text-center uppercase tracking-widest" style={{ color: "var(--text-dim)" }}>{t("auth.quickAccess")}</p>
            <div className="grid grid-cols-3 gap-2">
              {[["admin", "admin123", t("auth.admin")], ["agent1", "agent123", t("auth.agent")], ["zhangsan", "zhangsan123", t("auth.customer")]].map(([u, p, label]) => (
                <button key={u} type="button" onClick={() => { setUsername(u); setPassword(p); }}
                  className="group flex flex-col items-center p-2 rounded-lg transition-all cursor-pointer"
                  style={{ border: "1px solid var(--border)" }}>
                  <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>{label}</span>
                  <span className="text-[10px] font-mono" style={{ color: "var(--text-dim)" }}>{u}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="mt-4 flex justify-center gap-3">
            <button onClick={() => i18n.changeLanguage(i18n.language === "zh" ? "en" : "zh")}
              className="flex items-center gap-1 text-[11px] cursor-pointer transition-colors"
              style={{ color: "var(--text-dim)" }}>
              <Globe className="w-3 h-3" />{i18n.language === "zh" ? "English" : "中文"}
            </button>
            <button onClick={toggleTheme}
              className="flex items-center gap-1 text-[11px] cursor-pointer transition-colors"
              style={{ color: "var(--text-dim)" }}>
              {theme === "dark" ? <Sun className="w-3 h-3" /> : <Moon className="w-3 h-3" />}
              {theme === "dark" ? "Light" : "Dark"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
