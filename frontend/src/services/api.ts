const API_BASE = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("token");

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    // Token 过期，清除登录状态
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Health
  healthCheck: () => request<{ status: string }>("/health"),

  // Approvals
  getApprovals: () => request<{ items: unknown[]; total: number }>("/admin/approvals"),

  decideApproval: (id: string, decision: string, comment = "") =>
    request(`/admin/approvals/${id}`, {
      method: "POST",
      body: JSON.stringify({ decision, comment }),
    }),

  takeoverConversation: (id: string, agentId: string, reason = "") =>
    request(`/admin/conversations/${id}/takeover`, {
      method: "POST",
      body: JSON.stringify({ agent_id: agentId, reason }),
    }),

  releaseConversation: (id: string) =>
    request(`/admin/conversations/${id}/release`, { method: "POST" }),

  // Dashboard
  getDashboardStats: () =>
    request<{
      summary: {
        total_products: number;
        total_customers: number;
        total_orders: number;
        total_revenue: number;
        pending_orders: number;
        pending_refunds: number;
        open_tickets: number;
      };
      recent_orders: Array<{
        order_no: string;
        customer_id: string;
        amount: number;
        status: string;
        created_at: string;
      }>;
      hot_products: Array<{
        name: string;
        count: number;
        total: number;
      }>;
    }>("/admin/ecommerce/dashboard/stats"),

  // Products
  getProducts: (params?: {
    category?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set("category", params.category);
    if (params?.is_active !== undefined) query.set("is_active", String(params.is_active));
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    return request<{
      items: Array<{
        id: string;
        sku: string;
        name: string;
        description: string;
        category: string;
        price: number;
        stock: number;
        warranty_months: number;
        is_active: boolean;
        image_url: string | null;
        created_at: string;
      }>;
      total: number;
      page: number;
      page_size: number;
    }>(`/admin/ecommerce/products?${query.toString()}`);
  },

  getProduct: (id: string) =>
    request<{
      id: string;
      sku: string;
      name: string;
      description: string;
      category: string;
      price: number;
      stock: number;
      warranty_months: number;
      is_active: boolean;
      image_url: string | null;
      created_at: string;
      updated_at: string;
    }>(`/admin/ecommerce/products/${id}`),

  createProduct: (data: {
    sku: string;
    name: string;
    description?: string;
    category: string;
    price: number;
    stock?: number;
    warranty_months?: number;
    image_url?: string;
  }) =>
    request<{ id: string; sku: string; name: string }>("/admin/ecommerce/products", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateProduct: (id: string, data: Record<string, unknown>) =>
    request(`/admin/ecommerce/products/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteProduct: (id: string) =>
    request(`/admin/ecommerce/products/${id}`, { method: "DELETE" }),

  // Orders
  getOrders: (params?: {
    status?: string;
    customer_id?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.customer_id) query.set("customer_id", params.customer_id);
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    return request<{
      items: Array<{
        id: string;
        order_no: string;
        customer_id: string;
        status: string;
        total_amount: number;
        shipping_address: string;
        notes: string | null;
        items: Array<{
          product_name: string;
          quantity: number;
          unit_price: number;
          subtotal: number;
        }>;
        created_at: string;
      }>;
      total: number;
      page: number;
      page_size: number;
    }>(`/admin/ecommerce/orders?${query.toString()}`);
  },

  getOrder: (id: string) =>
    request<{
      id: string;
      order_no: string;
      customer_id: string;
      status: string;
      total_amount: number;
      shipping_address: string;
      notes: string | null;
      items: Array<{
        product_name: string;
        quantity: number;
        unit_price: number;
        subtotal: number;
      }>;
      payments: Array<{
        payment_no: string;
        amount: number;
        method: string;
        status: string;
        created_at: string;
      }>;
      refunds: Array<{
        refund_no: string;
        amount: number;
        reason: string;
        status: string;
        created_at: string;
      }>;
      created_at: string;
      updated_at: string;
    }>(`/admin/ecommerce/orders/${id}`),

  updateOrder: (id: string, data: { status?: string; notes?: string }) =>
    request(`/admin/ecommerce/orders/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  // Customers
  getCustomers: (params?: {
    vip_level?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.vip_level) query.set("vip_level", params.vip_level);
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    return request<{
      items: Array<{
        id: string;
        name: string;
        email: string;
        phone: string;
        address: string;
        vip_level: string;
        orders_count: number;
        total_spent: number;
        created_at: string;
      }>;
      total: number;
      page: number;
      page_size: number;
    }>(`/admin/ecommerce/customers?${query.toString()}`);
  },

  getCustomer: (id: string) =>
    request<{
      id: string;
      name: string;
      email: string;
      phone: string;
      address: string;
      vip_level: string;
      orders: Array<{
        order_no: string;
        amount: number;
        status: string;
        created_at: string;
      }>;
      tickets: Array<{
        ticket_no: string;
        title: string;
        status: string;
        created_at: string;
      }>;
      created_at: string;
    }>(`/admin/ecommerce/customers/${id}`),

  // Refunds
  getRefunds: (params?: { status?: string; page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    return request<{
      items: Array<{
        id: string;
        refund_no: string;
        order_id: string;
        customer_id: string;
        amount: number;
        reason: string;
        status: string;
        approved_by: string | null;
        created_at: string;
      }>;
      total: number;
      page: number;
      page_size: number;
    }>(`/admin/ecommerce/refunds?${query.toString()}`);
  },

  approveRefund: (id: string) =>
    request(`/admin/ecommerce/refunds/${id}/approve`, { method: "PUT" }),

  rejectRefund: (id: string, reason = "") =>
    request(`/admin/ecommerce/refunds/${id}/reject?reason=${encodeURIComponent(reason)}`, {
      method: "PUT",
    }),

  // Knowledge
  getKnowledge: (category?: string) => {
    const query = category ? `?category=${category}` : "";
    return request<{
      items: Array<{
        id: string;
        title: string;
        category: string;
        view_count: number;
        is_published: boolean;
        created_at: string;
      }>;
    }>(`/admin/ecommerce/knowledge${query}`);
  },
};
