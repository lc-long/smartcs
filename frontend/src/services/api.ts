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

  // Analytics - 新增分析API
  getAnalyticsDashboard: () =>
    request<{
      summary: {
        total_customers: number;
        total_orders: number;
        total_revenue: number;
        today_orders: number;
        pending_tickets: number;
        pending_refunds: number;
        avg_order_amount: number;
        avg_rating: number;
      };
      order_trend: Array<{
        date: string;
        count: number;
        amount: number;
      }>;
      order_status_distribution: Record<string, number>;
      top_products: Array<{
        name: string;
        quantity: number;
        amount: number;
      }>;
    }>("/analytics/dashboard"),

  getAgentPerformance: (days = 30) =>
    request<{
      period_days: number;
      summary: {
        total_tickets: number;
        resolved_tickets: number;
        resolution_rate: number;
      };
      agent_ticket_stats: Array<{
        agent: string;
        total_tickets: number;
        resolved: number;
        in_progress: number;
        resolution_rate: number;
      }>;
      agent_refund_stats: Array<{
        agent: string;
        total_reviews: number;
        approved: number;
        rejected: number;
      }>;
    }>(`/analytics/agents/performance?days=${days}`),

  getCustomerSatisfaction: (days = 30) =>
    request<{
      period_days: number;
      review_summary: {
        total_reviews: number;
        avg_rating: number;
        positive_rate: number;
        negative_rate: number;
      };
      rating_distribution: Record<number, number>;
      feedback_distribution: Record<string, number>;
      feedback_status: Record<string, number>;
      ticket_category_distribution: Record<string, number>;
      ticket_priority_distribution: Record<string, number>;
    }>(`/analytics/satisfaction?days=${days}`),

  getProductAnalytics: () =>
    request<{
      product_sales_ranking: Array<{
        name: string;
        order_count: number;
        quantity: number;
        amount: number;
      }>;
      product_rating_ranking: Array<{
        name: string;
        rating: number;
        review_count: number;
      }>;
      low_stock_alerts: Array<{
        sku: string;
        name: string;
        stock: number;
        category: string;
      }>;
      category_sales: Array<{
        category: string;
        amount: number;
        quantity: number;
      }>;
    }>("/analytics/products/analytics"),

  getLogisticsStats: () =>
    request<{
      status_distribution: Record<string, number>;
      carrier_distribution: Record<string, number>;
      avg_delivery_days: number;
      in_transit_count: number;
    }>("/analytics/logistics"),

  // Conversations - History Management
  getConversations: (params?: { include_deleted?: boolean; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.include_deleted !== undefined) query.set("include_deleted", String(params.include_deleted));
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    return request<Array<{
      id: string;
      customer_id: string;
      status: string;
      last_message: string | null;
      created_at: string;
      updated_at: string;
      is_deleted: boolean;
    }>>(`/history/conversations?${query.toString()}`);
  },

  getConversationMessages: (conversationId: string, params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    return request<{
      messages: Array<{
        id: string;
        role: string;
        content: string;
        agent_name: string | null;
        tools_called: string[];
        created_at: string;
      }>;
      total: number;
    }>(`/history/conversations/${conversationId}?${query.toString()}`);
  },

  deleteConversation: (conversationId: string) =>
    request(`/history/conversations/${conversationId}`, { method: "DELETE" }),

  restoreConversation: (conversationId: string) =>
    request(`/history/conversations/${conversationId}/restore`, { method: "POST" }),

  // Admin - All Conversations
  getAdminConversations: (params?: {
    include_deleted?: boolean;
    status?: string;
    customer_id?: string;
    limit?: number;
    offset?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.include_deleted !== undefined) query.set("include_deleted", String(params.include_deleted));
    if (params?.status) query.set("status", params.status);
    if (params?.customer_id) query.set("customer_id", params.customer_id);
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    return request<{
      items: Array<{
        id: string;
        customer_id: string;
        status: string;
        last_message: string | null;
        created_at: string;
        updated_at: string;
        is_deleted: boolean;
      }>;
      total: number;
    }>(`/admin/conversations?${query.toString()}`);
  },

  adminRestoreConversation: (conversationId: string) =>
    request(`/admin/conversations/${conversationId}/restore`, { method: "POST" }),

  adminPermanentDeleteConversation: (conversationId: string) =>
    request(`/admin/conversations/${conversationId}/permanent`, { method: "DELETE" }),
};
