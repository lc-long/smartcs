import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../contexts/AuthContext";
import { Zap, Eye, EyeOff, ArrowRight, Globe } from "lucide-react";
import i18n from "../i18n";

export function LoginPage() {
  const { login, user } = useAuth();
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
    <div className="min-h-screen flex bg-zinc-950">
      {/* Left - Brand */}
      <div className="hidden lg:flex lg:w-[45%] bg-zinc-950 relative overflow-hidden border-r border-zinc-800/50">
        <div className="absolute inset-0 opacity-[0.04]" style={{ backgroundImage: "radial-gradient(circle at 25% 25%, white 1px, transparent 1px), radial-gradient(circle at 75% 75%, white 1px, transparent 1px)", backgroundSize: "40px 40px" }} />
        <div className="relative z-10 flex flex-col justify-center px-14">
          <div className="flex items-center gap-2.5 mb-10">
            <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center"><Zap className="w-5 h-5 text-white" /></div>
            <div><h1 className="text-xl font-bold text-zinc-100">SmartCS</h1><p className="text-[11px] text-zinc-600">AI Customer Service</p></div>
          </div>
          <h2 className="text-3xl font-bold text-zinc-100 leading-tight mb-5">{t("auth.brandTitle")}</h2>
          <p className="text-sm text-zinc-500 max-w-sm leading-relaxed">{t("auth.brandDesc")}</p>
          <div className="mt-10 flex items-center gap-6">
            <div><p className="text-2xl font-bold text-zinc-100">99.5%</p><p className="text-[11px] text-zinc-600">{t("auth.resolutionRate")}</p></div>
            <div className="w-px h-8 bg-zinc-800" />
            <div><p className="text-2xl font-bold text-zinc-100">&lt;3s</p><p className="text-[11px] text-zinc-600">{t("auth.avgResponse")}</p></div>
            <div className="w-px h-8 bg-zinc-800" />
            <div><p className="text-2xl font-bold text-zinc-100">24/7</p><p className="text-[11px] text-zinc-600">{t("auth.availability")}</p></div>
          </div>
        </div>
      </div>

      {/* Right - Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-zinc-950">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2.5 mb-8">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center"><Zap className="w-4 h-4 text-white" /></div>
            <h1 className="text-lg font-bold text-zinc-100">SmartCS</h1>
          </div>
          <div className="mb-6">
            <h2 className="text-xl font-bold text-zinc-100">{t("auth.welcomeBack")}</h2>
            <p className="text-xs text-zinc-500 mt-1">{t("auth.signInSubtitle")}</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && <div className="bg-red-950/50 border border-red-800/50 text-red-400 px-3 py-2 rounded-lg text-xs">{error}</div>}
            <div>
              <label className="block text-xs font-semibold text-zinc-400 mb-1">{t("auth.username")}</label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder={t("auth.usernamePlaceholder")}
                className="w-full border border-zinc-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600/50 transition-all bg-zinc-900 text-zinc-100 placeholder:text-zinc-600" required />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-400 mb-1">{t("auth.password")}</label>
              <div className="relative">
                <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t("auth.passwordPlaceholder")}
                  className="w-full border border-zinc-800 rounded-lg px-3 py-2 pr-9 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600/50 transition-all bg-zinc-900 text-zinc-100 placeholder:text-zinc-600" required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 cursor-pointer">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full bg-indigo-600 text-white py-2 rounded-lg font-semibold text-sm hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 cursor-pointer">
              {loading ? <><div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />{t("auth.signingIn")}</> : <>{t("auth.signIn")}<ArrowRight className="w-3.5 h-3.5" /></>}
            </button>
          </form>
          <div className="mt-6 pt-5 border-t border-zinc-800/50">
            <p className="text-[10px] text-zinc-600 font-semibold mb-2.5 text-center uppercase tracking-widest">{t("auth.quickAccess")}</p>
            <div className="grid grid-cols-3 gap-2">
              {[["admin", "admin123", t("auth.admin")], ["agent1", "agent123", t("auth.agent")], ["zhangsan", "zhangsan123", t("auth.customer")]].map(([u, p, label]) => (
                <button key={u} type="button" onClick={() => { setUsername(u); setPassword(p); }}
                  className="group flex flex-col items-center p-2 rounded-lg border border-zinc-800 hover:border-indigo-600/50 hover:bg-zinc-800/60 transition-all cursor-pointer">
                  <span className="text-xs font-semibold text-zinc-400 group-hover:text-zinc-200">{label}</span>
                  <span className="text-[10px] text-zinc-600 font-mono">{u}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="mt-4 flex justify-center">
            <button onClick={() => i18n.changeLanguage(i18n.language === "zh" ? "en" : "zh")}
              className="flex items-center gap-1 text-[11px] text-zinc-600 hover:text-zinc-400 cursor-pointer transition-colors">
              <Globe className="w-3 h-3" />{i18n.language === "zh" ? "English" : "中文"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
