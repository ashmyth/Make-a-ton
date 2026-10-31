import { UserProfile, Customer, StaffMember, AuditLogEntry } from '../types';

const API_BASE = '/api/v1';

let cachedCsrfToken = '';

export async function fetchCsrfToken(): Promise<string> {
  if (cachedCsrfToken) return cachedCsrfToken;
  try {
    const res = await fetch(`${API_BASE}/auth/csrf/`, { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      cachedCsrfToken = data.csrfToken;
      return cachedCsrfToken;
    }
  } catch (err) {
    console.error('Failed to fetch CSRF token:', err);
  }
  return '';
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const method = options.method || 'GET';
  const headers = new Headers(options.headers || {});
  headers.set('Accept', 'application/json');

  if (['POST', 'PATCH', 'PUT', 'DELETE'].includes(method.toUpperCase())) {
    headers.set('Content-Type', 'application/json');
    const csrf = await fetchCsrfToken();
    if (csrf) {
      headers.set('X-CSRFToken', csrf);
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg = data.detail || data.message || JSON.stringify(data);
    const err: any = new Error(errorMsg);
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data as T;
}

export const api = {
  auth: {
    csrf: () => request<{ csrfToken: string }>('/auth/csrf/'),
    me: () => request<UserProfile>('/auth/me/'),
    login: (credentials: { email: string; password: string }) =>
      request<UserProfile>('/auth/login/', {
        method: 'POST',
        body: JSON.stringify(credentials),
      }),
    logout: () =>
      request<void>('/auth/logout/', {
        method: 'POST',
      }),
    register: (data: { email: string; password: string; first_name: string; last_name: string }) =>
      request<UserProfile>('/auth/register/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    passwordResetRequest: (email: string) =>
      request<{ message: string }>('/auth/password-reset/', {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),
    passwordResetConfirm: (payload: { token: string; new_password: string }) =>
      request<{ message: string }>('/auth/password-reset-confirm/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  staff: {
    list: () => request<{ results: StaffMember[]; count: number }>('/staff/'),
    create: (data: { email: string; password: string; first_name: string; last_name: string; role: string }) =>
      request<StaffMember>('/staff/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: Partial<StaffMember>) =>
      request<StaffMember>(`/staff/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    deactivate: (id: string) =>
      request<{ message: string; staff: StaffMember }>(`/staff/${id}/deactivate/`, {
        method: 'POST',
      }),
    activate: (id: string) =>
      request<{ message: string; staff: StaffMember }>(`/staff/${id}/activate/`, {
        method: 'POST',
      }),
  },

  customers: {
    list: (params: { search?: string; status?: string; customer_type?: string } = {}) => {
      const q = new URLSearchParams();
      if (params.search) q.set('search', params.search);
      if (params.status) q.set('status', params.status);
      if (params.customer_type) q.set('customer_type', params.customer_type);
      return request<{ results: Customer[]; count: number }>(`/customers/?${q.toString()}`);
    },
    get: (id: string) => request<Customer>(`/customers/${id}/`),
    create: (data: Partial<Customer>) =>
      request<Customer>('/customers/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: Partial<Customer>) =>
      request<Customer>(`/customers/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    archive: (id: string) =>
      request<Customer>(`/customers/${id}/archive/`, {
        method: 'POST',
      }),
    unarchive: (id: string) =>
      request<Customer>(`/customers/${id}/unarchive/`, {
        method: 'POST',
      }),
    linkPortal: (id: string, payload: { email?: string; password?: string; user_id?: string }) =>
      request<Customer>(`/customers/${id}/link-portal/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    myProfile: () => request<Customer>('/customers/my-profile/'),
  },

  audit: {
    list: (params: { action?: string; search?: string } = {}) => {
      const q = new URLSearchParams();
      if (params.action) q.set('action', params.action);
      if (params.search) q.set('search', params.search);
      return request<{ results: AuditLogEntry[]; count: number }>(`/audit/?${q.toString()}`);
    },
  },
};

