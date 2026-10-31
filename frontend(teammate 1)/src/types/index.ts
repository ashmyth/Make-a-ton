export type UserRole = 'ADMINISTRATOR' | 'OPERATIONS' | 'FINANCE' | 'CUSTOMER';

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  customer_id: string | null;
  is_active: boolean;
}

export type CustomerType = 'INDIVIDUAL' | 'BUSINESS';
export type CustomerStatus = 'ACTIVE' | 'ARCHIVED';
export type PaymentTerms = 'IMMEDIATE' | 'NET_15' | 'NET_30' | 'NET_60';

export interface Customer {
  id: string;
  customer_code: string;
  customer_type: CustomerType;
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
  tax_identifier: string;
  payment_terms: PaymentTerms;
  status: CustomerStatus;
  portal_user: string | null;
  portal_user_email?: string | null;
  created_at: string;
}

export interface StaffMember {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: 'OPERATIONS' | 'FINANCE' | 'ADMINISTRATOR';
  is_active: boolean;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  actor_email: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, any>;
  ip_address: string | null;
  timestamp: string;
}

