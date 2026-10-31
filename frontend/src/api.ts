const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.status = status;
    this.body = body;
    this.name = "ApiError";
  }

  /** DRF field errors, e.g. { amount: ["Exceeds outstanding balance."] } */
  get fieldErrors(): Record<string, string[]> | null {
    const b = this.body;
    if (this.status === 400 && b && typeof b === "object" && !("detail" in b)) {
      return b as Record<string, string[]>;
    }
    return null;
  }
}

function getCookie(name: string): string | null {
  const m = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return m ? decodeURIComponent(m[1]) : null;
}

const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");

  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (UNSAFE.has(method)) {
    const token = getCookie("csrftoken");
    if (token) {
      headers.set("X-CSRFToken", token);
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: "same-origin", // Same-origin deployment via reverse proxy / Vite proxy
  });

  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      /* not JSON */
    }
    const detail =
      (body as { detail?: string } | null)?.detail ??
      `HTTP ${response.status}: ${response.statusText}`;
    throw new ApiError(response.status, body, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export type Query = Record<string, string | number | boolean | null | undefined>;

export function withQuery(path: string, params: Query = {}): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      qs.set(k, String(v));
    }
  }
  const s = qs.toString();
  return s ? `${path}?${s}` : path;
}

// ==========================================
// Strongly-typed Data Contracts
// ==========================================

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: "CUSTOMER" | "ADMINISTRATOR" | "OPERATIONS" | "FINANCE";
  is_active: boolean;
  customer_id: string | null;
}

export interface CustomerProfile {
  id: string;
  customer_code: string;
  display_name: string;
  contact_person: string;
  email: string;
  phone: string;
  billing_street: string;
  billing_city: string;
  billing_state: string;
  billing_postal_code: string;
  billing_country: string;
  full_billing_address: string;
  payment_terms: string;
  status: string;
}

export interface Subscription {
  id: string;
  subscription_number: string;
  plan_name: string;
  billing_interval: string;
  status: string;
  is_paused: boolean;
  start_date: string;
  expiry_date: string | null;
  next_billing_date: string | null;
  currency: string;
  created_at: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  subscription?: string;
  subscription_number?: string;
  customer_name?: string;
  issue_date: string;
  due_date: string;
  service_period_start?: string | null;
  service_period_end?: string | null;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  total_amount: string;
  outstanding_balance: string;
  currency: string;
  status: "draft" | "confirmed" | "partially_paid" | "paid" | "cancelled";
  created_at: string;
}

export interface Payment {
  id: string;
  invoice: string;
  invoice_number: string;
  customer?: string;
  customer_name?: string;
  recorded_by?: string;
  recorded_by_name?: string;
  amount: string;
  currency: string;
  method: string;
  status: string;
  idempotency_key: string;
  external_reference?: string;
  notes?: string;
  paid_at: string;
  is_reversed?: boolean;
  reversed_at?: string | null;
  reversal_reason?: string;
  created_at?: string;
}

export interface CustomerRequest {
  id: string;
  subscription: string;
  subscription_number: string;
  request_type: "pause" | "resume" | "cancel" | "renew";
  status: "submitted" | "reviewed" | "approved" | "rejected";
  notes?: string;
  staff_response?: string;
  created_at: string;
}

export interface PortalOverviewData {
  customer: CustomerProfile;
  metrics: {
    active_subscriptions: number;
    unpaid_invoices_count: number;
    total_outstanding_balance: string;
    currency: string;
  };
  recent_invoices: Invoice[];
  recent_payments: Payment[];
}

export interface DashboardMetrics {
  active_subscriptions: number;
  running_subscriptions: number;
  billed_amount: string;
  cash_collected: string;
  outstanding_balance: string;
  overdue_balance: string;
  overdue_invoice_count: number;
  currency: string;
  filter_summary: {
    start_date: string | null;
    end_date: string | null;
    customer_id: string | null;
    plan_name: string | null;
    evaluated_at: string;
  };
}

export interface RecordPaymentPayload {
  invoice_id: string;
  amount: string; // Strictly decimal string (e.g. "1500.00"), never a float
  method: string;
  external_reference?: string;
  notes?: string;
}

// ==========================================
// API Client
// ==========================================

export const api = {
  // Authentication & CSRF
  auth: {
    csrf: () => apiRequest<{ detail: string }>("/auth/csrf/"),
    getMe: () => apiRequest<User>("/auth/me/"),
    login: (credentials: { email: string; password: string }) =>
      apiRequest<User>("/auth/login/", {
        method: "POST",
        body: JSON.stringify(credentials),
      }),
    logout: () => apiRequest<{ detail: string }>("/auth/logout/", { method: "POST" }),
  },

  // Customer Portal
  portal: {
    getOverview: () => apiRequest<PortalOverviewData>("/portal/overview/"),
    getSubscriptions: () => apiRequest<Subscription[]>("/portal/subscriptions/"),
    getInvoices: () => apiRequest<Invoice[]>("/portal/invoices/"),
    getInvoice: (id: string) => apiRequest<Invoice>(`/portal/invoices/${id}/`),
    getPayments: () => apiRequest<Payment[]>("/portal/payments/"),
    getRequests: () => apiRequest<CustomerRequest[]>("/portal/requests/"),
    submitRequest: (data: { subscription: string; request_type: string; notes?: string }) =>
      apiRequest<CustomerRequest>("/portal/requests/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    getProfile: () => apiRequest<CustomerProfile>("/portal/profile/"),
    updateProfile: (data: Partial<CustomerProfile>) =>
      apiRequest<CustomerProfile>("/portal/profile/", {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    getInvoiceDownloadUrl: (id: string) => `${API_BASE}/portal/invoices/${id}/download/`,
  },

  // Finance Console & Reporting
  finance: {
    getDashboardMetrics: (params: Query = {}) =>
      apiRequest<DashboardMetrics>(withQuery("/reports/dashboard/", params)),
    getInvoicesReport: (params: Query = {}) =>
      apiRequest<Invoice[]>(withQuery("/reports/invoices/", params)),
    getPaymentsReport: (params: Query = {}) =>
      apiRequest<Payment[]>(withQuery("/reports/payments/", params)),
    recordPayment: (data: RecordPaymentPayload, idempotencyKey: string) =>
      apiRequest<Payment>("/payments/", {
        method: "POST",
        headers: {
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({
          ...data,
          idempotency_key: idempotencyKey,
        }),
      }),
    reversePayment: (paymentId: string, reason: string) =>
      apiRequest<Payment>(`/payments/${paymentId}/reverse/`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
  },
};
