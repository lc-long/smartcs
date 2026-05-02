import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../services/api";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface Product { id: string; sku: string; name: string; description: string; category: string; price: number; stock: number; warranty_months: number; is_active: boolean; image_url: string | null; created_at: string; }

export function ProductsPage() {
  const { t } = useTranslation();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState("");
  const categories = ["手表", "手环", "耳机", "配件"];

  useEffect(() => { loadProducts(); }, [page, category]);

  async function loadProducts() {
    try { setLoading(true); const data = await api.getProducts({ page, page_size: 20, category: category || undefined }); setProducts(data.items); setTotal(data.total); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5">
        <h1 className="text-lg font-bold text-zinc-100">{t("products.title")}</h1>
        <p className="text-xs text-zinc-500 mt-0.5">{t("products.subtitle")}</p>
      </div>
      <div className="flex items-center gap-3 mb-4">
        <select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          className="px-3 py-1.5 border border-zinc-800 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600/50 bg-zinc-900 text-zinc-300 cursor-pointer">
          <option value="">{t("products.allCategories")}</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <div className="flex-1" />
        <span className="text-[11px] text-zinc-500">{t("products.totalProducts", { count: total })}</span>
      </div>
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 border-zinc-700 border-t-indigo-500 rounded-full animate-spin" /></div> : (
          <table className="w-full">
            <thead><tr className="border-b border-zinc-800">
              {[t("products.product"), t("products.sku"), t("products.category"), t("products.price"), t("products.stock"), t("products.warranty"), t("products.status")].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr></thead>
            <tbody className="divide-y divide-zinc-800/50">
              {products.map((p) => (
                <tr key={p.id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="px-4 py-3"><p className="text-xs font-semibold text-zinc-200">{p.name}</p><p className="text-[11px] text-zinc-500 truncate max-w-[200px]">{p.description}</p></td>
                  <td className="px-4 py-3 text-[11px] text-zinc-500 font-mono">{p.sku}</td>
                  <td className="px-4 py-3"><span className="text-[10px] font-medium text-indigo-400">{p.category}</span></td>
                  <td className="px-4 py-3 text-xs font-semibold text-zinc-200">¥{p.price.toLocaleString()}</td>
                  <td className="px-4 py-3"><span className={`text-xs font-semibold ${p.stock > 10 ? "text-emerald-400" : p.stock > 0 ? "text-amber-400" : "text-red-400"}`}>{p.stock}</span></td>
                  <td className="px-4 py-3 text-[11px] text-zinc-500">{t("products.warrantyMonths", { months: p.warranty_months })}</td>
                  <td className="px-4 py-3"><span className={`text-[10px] font-medium ${p.is_active ? "text-emerald-400" : "text-red-400"}`}>{p.is_active ? t("products.active") : t("products.inactive")}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="px-4 py-2.5 bg-zinc-950/50 border-t border-zinc-800 flex items-center justify-between">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
            className="flex items-center gap-1 px-3 py-1 text-xs text-zinc-400 border border-zinc-800 rounded-lg disabled:opacity-30 hover:bg-zinc-800 transition-colors cursor-pointer disabled:cursor-not-allowed"><ChevronLeft className="w-3 h-3" />{t("orders.prevPage")}</button>
          <span className="text-[11px] text-zinc-500">{t("orders.pageInfo", { current: page, total: Math.ceil(total / 20) })}</span>
          <button onClick={() => setPage(page + 1)} disabled={page * 20 >= total}
            className="flex items-center gap-1 px-3 py-1 text-xs text-zinc-400 border border-zinc-800 rounded-lg disabled:opacity-30 hover:bg-zinc-800 transition-colors cursor-pointer disabled:cursor-not-allowed">{t("orders.nextPage")}<ChevronRight className="w-3 h-3" /></button>
        </div>
      </div>
    </div>
  );
}
