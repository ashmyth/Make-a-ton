# Brightloop Integration Contract: Teammate 1 to Teammate 4

**Sender:** Teammate 1 (Identity, Access & Customer Foundation)  
**Recipient:** Teammate 4 (Payments, Customer Portal, Reporting & Notifications)  
**Status:** Approved & Implemented in Backend  
**Applies To:** Brightloop PRD v1.0 (§4, §7.1, §7.2, §7.12, §7.13) & Tech Stack Documentation  

---

## 1. Executive Summary

This contract defines how **Teammate 4** interacts with the authentication system and customer records created by **Teammate 1**.

Specifically, this document outlines:
1. How to access `request.user.customer_id` and the `Customer` object in your portal views.
2. How to apply backend permissions to guarantee customer data isolation (preventing IDOR attacks).
3. Which endpoints and profile fields are available to customer portal users.
4. How to link customer portal accounts to customer CRM records.

---

## 2. Core Identity & Customer Data Contract

### 2.1 Authenticated `request.user` Accessors

In any Django REST Framework view where the user is authenticated, the custom `User` model (`apps.accounts.models.User`) provides direct accessors:

| Property | Return Type | Description |
| :--- | :--- | :--- |
| `request.user.customer_id` | `UUID` / `None` | The unique UUID of the linked Customer record. Returns `None` if the user is a staff member or has no linked customer profile. |
| `request.user.customer` | `Customer` / `None` | The related [`Customer`](file:///d:/Make-a-ton/backend/apps/customers/models.py) model instance. |
| `request.user.role` | `str` | One of `UserRole.CUSTOMER`, `UserRole.ADMINISTRATOR`, `UserRole.OPERATIONS`, `UserRole.FINANCE`. |
| `request.user.email` | `str` | Normalized, unique email address. |
| `request.user.is_active` | `bool` | Account active flag (soft-deactivated users are blocked at login). |

---

## 3. Backend Enforcement & Data Isolation (PRD §4.1 & §7.1)

Customers must **only** be able to see and interact with their own subscriptions, invoices, and payments. Customers must never access another customer's record by manipulating query parameters or URL paths.

### 3.1 Provided Permission Classes

Import these permission classes directly from `apps.access_control.permissions`:

```python
from apps.access_control.permissions import (
    IsCustomerUser,
    CustomerDataIsolation,
    IsFinanceStaff,
    IsStaffUser,
)
```

- **`IsCustomerUser`**: Ensures the caller is authenticated, active, and has `role == UserRole.CUSTOMER`.
- **`CustomerDataIsolation`**: Object-level permission that verifies `obj.customer_id == request.user.customer_id` (or `obj.portal_user_id == request.user.id`).

### 3.2 Reference Implementation for Teammate 4 Views

#### Example A: Customer Portal Invoices Endpoint
```python
from rest_framework import generics, status
from rest_framework.response import Response
from apps.access_control.permissions import IsCustomerUser
# from apps.billing.models import Invoice
# from apps.billing.serializers import InvoiceSerializer

class CustomerPortalInvoiceListView(generics.ListAPIView):
    """
    Returns only invoices belonging to the authenticated customer.
    """
    permission_classes = [IsCustomerUser]
    # serializer_class = InvoiceSerializer

    def get_queryset(self):
        customer_id = self.request.user.customer_id
        if not customer_id:
            return Invoice.objects.none()
        
        # Strictly scope query to this customer:
        return Invoice.objects.filter(customer_id=customer_id).order_by('-issue_date')
```

#### Example B: Customer Portal Single Invoice Download / View
```python
from rest_framework import generics
from apps.access_control.permissions import CustomerDataIsolation, IsAuthenticatedAndActive
# from apps.billing.models import Invoice

class CustomerPortalInvoiceDetailView(generics.RetrieveAPIView):
    """
    Ensures that a customer cannot view or download an invoice belonging to another customer.
    """
    # queryset = Invoice.objects.all()
    # serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticatedAndActive, CustomerDataIsolation]
    lookup_field = 'id'
```

---

## 4. Endpoints Provided by Teammate 1 for the Portal

Teammate 4 can consume the following existing endpoints for the customer-facing frontend:

### 1. `GET /api/v1/auth/me/`
Returns session and identity details:
```json
{
  "id": "e4b52b21-46ab-41c4-9799-a9a7a6b7381a",
  "email": "customer@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "full_name": "Jane Doe",
  "role": "CUSTOMER",
  "is_active": true,
  "customer_id": "893c5240-27ef-4171-85e8-5b4d7543cf2e",
  "created_at": "2026-10-31T10:00:00Z",
  "updated_at": "2026-10-31T10:00:00Z"
}
```

### 2. `GET /api/v1/customers/my-profile/`
Returns the customer's CRM profile for display in the portal header/settings:
```json
{
  "id": "893c5240-27ef-4171-85e8-5b4d7543cf2e",
  "customer_code": "CUST-E0070020",
  "customer_type": "BUSINESS",
  "display_name": "Acme Corporation",
  "contact_person": "Alice Johnson",
  "email": "contact@acmecorp.com",
  "phone": "+1 (555) 234-5678",
  "billing_street": "100 Innovation Way, Suite 400",
  "billing_city": "San Francisco",
  "billing_state": "CA",
  "billing_postal_code": "94105",
  "billing_country": "United States",
  "full_billing_address": "100 Innovation Way, Suite 400, San Francisco, CA, 94105, United States",
  "tax_identifier": "US-EIN-948271049",
  "payment_terms": "NET_30",
  "status": "ACTIVE"
}
```

### 3. `PATCH /api/v1/customers/{id}/` (Self-Service Boundary)
Per PRD §4.2, customers are allowed to edit specific profile fields only:
* **Permitted fields for Customers:**
  - `contact_person`
  - `phone`
  - `billing_street`, `billing_city`, `billing_state`, `billing_postal_code`, `billing_country`
* **Blocked fields (Staff/Admin only):**
  - `status`, `customer_code`, `payment_terms`, `tax_identifier` (any attempt by a customer to modify these returns `403 Forbidden`).

---

## 5. Portal Account Linking Workflow

A customer record can exist with or without a portal login account:
1. **Initial Staff Creation**: Staff can create a Customer record with contact details and billing address.
2. **Account Linking**: To grant the customer portal access, staff or the customer invites/links a portal account via:
   - `POST /api/v1/customers/{id}/link-portal/`
   - Payload:
     ```json
     {
       "email": "customer.login@example.com",
       "password": "SecurePassword@123"
     }
     ```
   - This sets `Customer.portal_user` to the newly created or existing user account with `role = CUSTOMER`.

---

## 6. Staff Permissions for Reporting & Payments (Teammate 4)

Teammate 4 also builds the Finance dashboard and Payment recording workflows:
* **Finance Staff (`UserRole.FINANCE`)**:
  - Permitted to view all customer records (read-only).
  - Permitted to record payments and view financial dashboards.
  - Can be guarded with `permission_classes = [IsFinanceStaff]`.
* **Operations Staff (`UserRole.OPERATIONS`)**:
  - Has limited reporting access per PRD §4.1.

---

## 7. Checklist for Teammate 4

- [ ] Use `request.user.customer_id` for scoping all customer portal queries.
- [ ] Add `IsCustomerUser` or `CustomerDataIsolation` on portal endpoints.
- [ ] Use `GET /api/v1/auth/me/` on the frontend to check authenticated role and `customer_id`.
- [ ] Ensure payments recorded in Teammate 4 reference the immutable `customer_id`.

