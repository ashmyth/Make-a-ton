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
// Teammate 2: Commercial & Catalog Types
// ==========================================

export interface ProductVariant {
  id: string;
  product: string;
  attribute_name: string;
  value: string;
  price_adjustment: string;
  status: "active" | "archived";
  total_unit_price: string;
  created_at?: string;
  updated_at?: string;
}

export interface Product {
  id: string;
  name: string;
  type: string | null;
  sales_price: string;
  cost_price?: string; // Strictly absent in customer view
  notes: string | null;
  status: "active" | "archived";
  variants: ProductVariant[];
  created_at?: string;
  updated_at?: string;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  billing_interval: "daily" | "weekly" | "monthly" | "yearly";
  min_quantity: number;
  availability_start_date: string | null;
  availability_end_date: string | null;
  allow_pause: boolean;
  allow_early_closure: boolean;
  allow_renewal: boolean;
  auto_close_at_expiry: boolean;
  default_payment_terms: string;
  primary_product: string | null;
  primary_product_name?: string | null;
  default_primary_unit_price: string | null;
  status: "active" | "archived";
  is_currently_available: boolean;
}

export interface PricingCalculationResult {
  plan_id: string;
  plan_name: string;
  billing_interval: string;
  default_payment_terms: string;
  quote_date: string;
  min_quantity_required: number;
  min_quantity_met: boolean;
  min_quantity_error: string | null;
  lines: Array<{
    line_number: number;
    product_id: string;
    product_name: string;
    product_type: string | null;
    variant_id: string | null;
    variant_name: string | null;
    is_primary: boolean;
    base_price: string;
    base_price_source: string;
    variant_adjustment: string;
    unit_price: string;
    quantity: number;
    line_subtotal: string;
  }>;
  recurring_subtotal: string;
  pricing_policy: {
    rule: string;
    plan_price_applied: boolean;
    separate_plan_charge: string;
  };
}

export interface QuotationTemplateLine {
  id: string;
  product: string;
  product_name: string;
  variant: string | null;
  variant_value: string | null;
  default_quantity: number;
  is_primary: boolean;
  sort_order: number;
}

export interface QuotationTemplate {
  id: string;
  name: string;
  plan: string;
  plan_name: string;
  validity_days: number;
  notes: string | null;
  status: "active" | "archived";
  lines: QuotationTemplateLine[];
  created_at?: string;
  updated_at?: string;
}

export interface QuotationLine {
  id: string;
  product: string;
  product_name: string;
  variant: string | null;
  variant_value: string | null;
  description: string;
  quantity: number;
  unit_price: string;
  line_total: string;
  is_primary: boolean;
  sort_order: number;
}

export interface Quotation {
  id: string;
  quotation_number: string;
  customer_id: string;
  template: string | null;
  plan: string;
  plan_name: string;
  status: "draft" | "sent" | "reviewed" | "confirmed" | "expired" | "cancelled";
  issue_date: string;
  expiry_date: string;
  is_expired: boolean;
  total_amount: string;
  payment_terms: string;
  notes: string | null;
  confirmed_by: string | null;
  confirmed_at: string | null;
  lines: QuotationLine[];
  created_at: string;
  updated_at: string;
}

export interface SubscriptionLine {
  id: string;
  product: string;
  product_name: string;
  variant: string | null;
  variant_value: string | null;
  description: string;
  quantity: number;
  unit_price: string;
  line_total: string;
  is_primary: boolean;
  sort_order: number;
}

export interface SubscriptionDetail {
  id: string;
  subscription_number: string;
  customer_id: string;
  quotation?: string | null;
  plan: string;
  plan_name: string;
  billing_interval: string;
  status: "draft" | "quotation" | "confirmed" | "active" | "paused" | "closed";
  operational_status: "running" | "paused";
  start_date: string;
  expiry_date: string | null;
  billing_anchor_date: string | null;
  next_billing_date: string | null;
  last_billed_period_end: string | null;
  payment_terms: string;
  pause_date: string | null;
  pause_reason: string | null;
  resume_date: string | null;
  closure_date: string | null;
  closure_reason: string | null;
  action_required: boolean;
  action_required_reason: string | null;
  predecessor: string | null;
  predecessor_number: string | null;
  successor: string | null;
  successor_number: string | null;
  total_recurring_amount: string;
  lines: SubscriptionLine[];
  created_at: string;
  updated_at: string;
}

export interface BillingExportLine {
  subscription_line_id: string;
  product_id: string;
  variant_id: string | null;
  description: string;
  quantity: number;
  unit_price: string;
  is_primary: boolean;
}

export interface SubscriptionBillingExport {
  subscription_id: string;
  subscription_number: string;
  customer_id: string;
  plan_id: string;
  status: string;
  operational_status: string;
  billing_anchor_date: string;
  next_billing_date: string;
  billing_interval: string;
  start_date: string;
  expiry_date: string | null;
  payment_terms: string;
  lines: BillingExportLine[];
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
    register: (data: { email: string; password: string; full_name?: string; company_name?: string; phone?: string }) =>
      apiRequest<User>("/auth/register/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    forgotPassword: (email: string) =>
      apiRequest<{ detail: string }>("/auth/password-reset/", {
        method: "POST",
        body: JSON.stringify({ email }),
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

  // Commercial Console (Teammate 2: Catalog, Quotations & Subscriptions)
  commercial: {
    // Products & Variants
    getProducts: (params: Query = {}) =>
      apiRequest<Product[]>(withQuery("/catalog/products/", params)),
    getProduct: (id: string, params: Query = {}) =>
      apiRequest<Product>(withQuery(`/catalog/products/${id}/`, params)),
    createProduct: (data: Partial<Product>) =>
      apiRequest<Product>("/catalog/products/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    updateProduct: (id: string, data: Partial<Product>) =>
      apiRequest<Product>(`/catalog/products/${id}/`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    archiveProduct: (id: string) =>
      apiRequest<Product>(`/catalog/products/${id}/archive/`, { method: "POST" }),
    createVariant: (data: { product: string; attribute_name: string; value: string; price_adjustment: string }) =>
      apiRequest<ProductVariant>("/catalog/variants/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    archiveVariant: (id: string) =>
      apiRequest<ProductVariant>(`/catalog/variants/${id}/archive/`, { method: "POST" }),

    // Subscription Plans
    getPlans: (params: Query = {}) =>
      apiRequest<SubscriptionPlan[]>(withQuery("/catalog/plans/", params)),
    createPlan: (data: Partial<SubscriptionPlan>) =>
      apiRequest<SubscriptionPlan>("/catalog/plans/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    archivePlan: (id: string) =>
      apiRequest<SubscriptionPlan>(`/catalog/plans/${id}/archive/`, { method: "POST" }),
    calculatePricing: (planId: string, payload: { lines: Array<{ product_id: string; variant_id?: string | null; quantity: number; is_primary?: boolean }>; quote_date?: string; validate_minimums?: boolean }) =>
      apiRequest<PricingCalculationResult>(`/catalog/plans/${planId}/calculate_pricing/`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    // Quotation Templates
    getTemplates: (params: Query = {}) =>
      apiRequest<QuotationTemplate[]>(withQuery("/subscriptions/templates/", params)),
    createTemplate: (data: any) =>
      apiRequest<QuotationTemplate>("/subscriptions/templates/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    duplicateTemplate: (id: string, name?: string) =>
      apiRequest<QuotationTemplate>(`/subscriptions/templates/${id}/duplicate/`, {
        method: "POST",
        body: JSON.stringify({ name }),
      }),
    archiveTemplate: (id: string) =>
      apiRequest<QuotationTemplate>(`/subscriptions/templates/${id}/archive/`, { method: "POST" }),
    createQuotationFromTemplate: (templateId: string, payload: { customer_id: string; issue_date?: string; notes?: string }) =>
      apiRequest<Quotation>(`/subscriptions/templates/${templateId}/create-quotation/`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    // Quotations Workflow
    getQuotations: (params: Query = {}) =>
      apiRequest<Quotation[]>(withQuery("/subscriptions/quotations/", params)),
    getQuotation: (id: string) =>
      apiRequest<Quotation>(`/subscriptions/quotations/${id}/`),
    createQuotation: (data: any) =>
      apiRequest<Quotation>("/subscriptions/quotations/", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    sendQuotation: (id: string) =>
      apiRequest<Quotation>(`/subscriptions/quotations/${id}/send/`, { method: "POST" }),
    reviewQuotation: (id: string) =>
      apiRequest<Quotation>(`/subscriptions/quotations/${id}/review/`, { method: "POST" }),
    confirmQuotation: (id: string, confirmed_by?: string) =>
      apiRequest<Quotation>(`/subscriptions/quotations/${id}/confirm/`, {
        method: "POST",
        body: JSON.stringify({ confirmed_by }),
      }),
    extendQuotation: (id: string, additional_days: number) =>
      apiRequest<Quotation>(`/subscriptions/quotations/${id}/extend/`, {
        method: "POST",
        body: JSON.stringify({ additional_days }),
      }),
    cancelQuotation: (id: string, reason?: string) =>
      apiRequest<Quotation>(`/subscriptions/quotations/${id}/cancel/`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    convertToSubscription: (id: string, payload?: { start_date?: string; expiry_date?: string }) =>
      apiRequest<SubscriptionDetail>(`/subscriptions/quotations/${id}/convert-to-subscription/`, {
        method: "POST",
        body: JSON.stringify(payload ?? {}),
      }),

    // Subscriptions Management
    getSubscriptions: (params: Query = {}) =>
      apiRequest<SubscriptionDetail[]>(withQuery("/subscriptions/subscriptions/", params)),
    getSubscription: (id: string, params: Query = {}) =>
      apiRequest<SubscriptionDetail>(withQuery(`/subscriptions/subscriptions/${id}/`, params)),
    pauseSubscription: (id: string, reason?: string) =>
      apiRequest<SubscriptionDetail>(`/subscriptions/subscriptions/${id}/pause/`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    resumeSubscription: (id: string) =>
      apiRequest<SubscriptionDetail>(`/subscriptions/subscriptions/${id}/resume/`, { method: "POST" }),
    renewSubscription: (id: string, payload?: { new_start_date?: string; new_expiry_date?: string }) =>
      apiRequest<SubscriptionDetail>(`/subscriptions/subscriptions/${id}/renew/`, {
        method: "POST",
        body: JSON.stringify(payload ?? {}),
      }),
    closeSubscription: (id: string, payload: { reason?: string; early?: boolean }) =>
      apiRequest<SubscriptionDetail>(`/subscriptions/subscriptions/${id}/close/`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    getDueForBilling: (asOf?: string) =>
      apiRequest<SubscriptionBillingExport[]>(withQuery("/subscriptions/subscriptions/due-for-billing/", { as_of: asOf })),
    sweepExpiries: (asOf?: string) =>
      apiRequest<{
        as_of_date: string;
        total_evaluated: number;
        auto_closed_count: number;
        auto_closed_subscriptions: string[];
        action_required_count: number;
        action_required_subscriptions: string[];
      }>("/subscriptions/subscriptions/sweep-expiries/", {
        method: "POST",
        body: JSON.stringify({ as_of: asOf }),
      }),
  },
};
