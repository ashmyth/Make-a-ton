const API_BASE = "http://127.0.0.1:8000/api/v1";

export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: "include", // Include Django session cookies
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      // not JSON
    }
    throw new Error(errorDetail);
  }

  // Handle empty or file responses
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return await response.json();
  }
  return response;
}

export const api = {
  // Authentication
  auth: {
    getMe: () => apiRequest("/auth/me/"),
    login: (credentials: { email: string; password: string }) =>
      apiRequest("/auth/login/", { method: "POST", body: JSON.stringify(credentials) }),
    logout: () => apiRequest("/auth/logout/", { method: "POST" }),
  },

  // Customer Portal
  portal: {
    getOverview: () => apiRequest("/portal/overview/"),
    getSubscriptions: () => apiRequest("/portal/subscriptions/"),
    getInvoices: () => apiRequest("/portal/invoices/"),
    getInvoice: (id: string) => apiRequest(`/portal/invoices/${id}/`),
    getPayments: () => apiRequest("/portal/payments/"),
    getRequests: () => apiRequest("/portal/requests/"),
    submitRequest: (data: { subscription: string; request_type: string; notes?: string }) =>
      apiRequest("/portal/requests/", { method: "POST", body: JSON.stringify(data) }),
    getProfile: () => apiRequest("/portal/profile/"),
    updateProfile: (data: Partial<{
      contact_person: string;
      phone: string;
      billing_street: string;
      billing_city: string;
      billing_state: string;
      billing_postal_code: string;
      billing_country: string;
    }>) => apiRequest("/portal/profile/", { method: "PATCH", body: JSON.stringify(data) }),
    getInvoiceDownloadUrl: (id: string) => `${API_BASE}/portal/invoices/${id}/download/`,
  },

  // Finance Console & Reporting
  finance: {
    getDashboardMetrics: (params: Record<string, string> = {}) => {
      const qs = new URLSearchParams(params).toString();
      return apiRequest(`/reports/dashboard/${qs ? `?${qs}` : ""}`);
    },
    getInvoicesReport: (params: Record<string, string> = {}) => {
      const qs = new URLSearchParams(params).toString();
      return apiRequest(`/reports/invoices/${qs ? `?${qs}` : ""}`);
    },
    getPaymentsReport: (params: Record<string, string> = {}) => {
      const qs = new URLSearchParams(params).toString();
      return apiRequest(`/reports/payments/${qs ? `?${qs}` : ""}`);
    },
    recordPayment: (data: {
      invoice_id: string;
      amount: string | number;
      method: string;
      idempotency_key: string;
      external_reference?: string;
      notes?: string;
    }) => apiRequest("/payments/", { method: "POST", body: JSON.stringify(data) }),
    reversePayment: (paymentId: string, reason: string) =>
      apiRequest(`/payments/${paymentId}/reverse/`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
  },
};
