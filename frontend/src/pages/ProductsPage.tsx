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
  async function loadProducts() { try { setLoading(true); const d = await api.getProducts({ page, page_size: 20, category: category || undefined }); setProducts(d.items); setTotal(d.total); } catch (e) { console.error(e); } finally { setLoading(false); } }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-5"><h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{t("products.title")}</h1><p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{t("products.subtitle")}</p></div>
      <div className="flex items-center gap-3 mb-4">
        <select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1); }} className="px-3 py-1.5 rounded-lg text-xs focus:outline-none cursor-pointer" style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-secondary)" }}>
          <option value="">{t("products.allCategories")}</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <div className="flex-1" /><span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{t("products.totalProducts", { count: total })}</span>
      </div>
      <div className="rounded-xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border)" }}>
        {loading ? <div className="flex items-center justify-center p-12"><div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: "var(--border)", borderTopColor: "var(--accent)" }} /></div> : (
          <table className="w-full">
            <thead><tr style={{ borderBottom: "1px solid var(--border)" }}>{[t("products.product"), t("products.sku"), t("products.category"), t("products.price"), t("products.stock"), t("products.warranty"), t("products.status")].map((h) => <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{h}</th>)}</tr></thead>
            <tbody>{products.map((p) => (
              <tr key={p.id} className="transition-colors" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td className="px-4 py-3"><p className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{p.name}</p><p className="text-[11px] truncate max-w-[200px]" style={{ color: "var(--text-muted)" }}>{p.description}</p></td>
                <td className="px-4 py-3 text-[11px] font-mono" style={{ color: "var(--text-muted)" }}>{p.sku}</td>
                <td className="px-4 py-3"><span className="text-[10px] font-medium" style={{ color: "var(--accent)" }}>{p.category}</span></td>
                <td className="px-4 py-3 text-xs font-semibold" style={{ color: "var(--text-primary)" }}>¥{p.price.toLocaleString()}</td>
                <td className="px-4 py-3"><span className="text-xs font-semibold" style={{ color: p.stock > 10 ? "var(--success)" : p.stock > 0 ? "var(--warning)" : "var(--error)" }}>{p.stock}</span></td>
                <td className="px-4 py-3 text-[11px]" style={{ color: "var(--text-muted)" }}>{t("products.warrantyMonths", { months: p.warranty_months })}</td>
                <td className="px-4 py-3"><span className="text-[10px] font-medium" style={{ color: p.is_active ? "var(--success)" : "var(--error)" }}>{p.is_active ? t("products.active") : t("products.inactive")}</span></td>
              </tr>
            ))}</tbody>
          </table>
        )}
        <div className="px-4 py-2.5 flex items-center justify-between" style={{ background: "var(--bg-app)", borderTop: "1px solid var(--border)" }}>
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="flex items-center gap-1 px-3 py-1 text-xs rounded-lg disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed" style={{ color: "var(--text-secondary)", border: "1px solid var(--border)" }}><ChevronLeft className="w-3 h-3" />{t("orders.prevPage")}</button>
          <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>{t("orders.pageInfo", { current: page, total: Math.ceil(total / 20) })}</span>
          <button onClick={() => setPage(page + 1)} disabled={page * 20 >= total} className="flex items-center gap-1 px-3 py-1 text-xs rounded-lg disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed" style={{ color: "var(--text-secondary)", border: "1px solid var(--border)" }}>{t("orders.nextPage")}<ChevronRight className="w-3 h-3" /></button>
        </div>
      </div>
    </div>
  );
}
