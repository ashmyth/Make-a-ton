import React, { useState } from "react";
import { X } from "lucide-react";

export interface Customer {
  id: string;
  name: string;
  contact_person: string;
  email: string;
  phone: string;
  billing_street: string;
  billing_city: string;
  billing_state: string;
  billing_postal_code: string;
  billing_country: string;
  is_active: boolean;
  created_at: string;
}

export const CustomerManagement: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([
    {
      id: "CUST-001",
      name: "Acme Corporation",
      contact_person: "John Doe",
      email: "contact@acme.com",
      phone: "+1 555-019-2834",
      billing_street: "12 MG Road",
      billing_city: "Bengaluru",
      billing_state: "KA",
      billing_postal_code: "560001",
      billing_country: "India",
      is_active: true,
      created_at: "2026-01-10",
    },
    {
      id: "CUST-002",
      name: "Zed Co",
      contact_person: "Sarah Connor",
      email: "sarah@zed.io",
      phone: "+1 555-839-2019",
      billing_street: "100 Innovation Way",
      billing_city: "San Francisco",
      billing_state: "CA",
      billing_postal_code: "94105",
      billing_country: "United States",
      is_active: true,
      created_at: "2026-02-14",
    },
  ]);

  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);

  // Form states
  const [name, setName] = useState("");
  const [contactPerson, setContactPerson] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");

  const handleCreateCustomer = (e: React.FormEvent) => {
    e.preventDefault();
    const newCust: Customer = {
      id: `CUST-00${customers.length + 1}`,
      name,
      contact_person: contactPerson,
      email,
      phone: phone || "+1 555-000-0000",
      billing_street: "100 Market St",
      billing_city: "San Francisco",
      billing_state: "CA",
      billing_postal_code: "94105",
      billing_country: "USA",
      is_active: true,
      created_at: new Date().toISOString().split("T")[0],
    };
    setCustomers([...customers, newCust]);
    setIsNewModalOpen(false);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Directory & CRM
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Customers
          </h1>
        </div>
        <button onClick={() => { setName(""); setEmail(""); setPhone(""); setIsNewModalOpen(true); }} className="btn-primary-blue">
          <span>+ New Customer</span>
        </button>
      </div>

      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>ID</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CUSTOMER NAME</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CONTACT PERSON</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>EMAIL</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>ACTIVE SUBS</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>BALANCE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>STATUS</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}></th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr
                key={c.id}
                style={{ borderBottom: "1px solid var(--color-ash)", cursor: "pointer" }}
                onClick={() => setSelectedCustomer(c)}
              >
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{c.id}</td>
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{c.name}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>{c.contact_person}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>{c.email}</td>
                <td style={{ padding: "14px 16px" }}>2 active</td>
                <td style={{ padding: "14px 16px", fontWeight: 500 }}>
                  $1,950.<span className="money-decimal">00</span>
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <span className={`badge-pill ${c.is_active ? "badge-active" : "badge-neutral"}`}>
                    {c.is_active ? "Active" : "Archived"}
                  </span>
                </td>
                <td style={{ padding: "14px 16px", textAlign: "right" }}>
                  <button className="btn-ghost" style={{ padding: "4px 12px", fontSize: "11px" }}>
                    View / Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Customer Drawer Modal */}
      {selectedCustomer && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(36, 36, 36, 0.4)",
            backdropFilter: "blur(4px)",
            display: "flex",
            justifyContent: "flex-end",
            zIndex: 100,
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "520px",
              backgroundColor: "var(--color-parchment)",
              height: "100%",
              boxShadow: "-10px 0 30px rgba(0,0,0,0.1)",
              padding: "32px",
              overflowY: "auto",
              boxSizing: "border-box",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
              <div>
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
                  {selectedCustomer.id}
                </span>
                <h2 className="font-serif" style={{ fontSize: "28px", margin: "4px 0 0 0" }}>
                  {selectedCustomer.name}
                </h2>
              </div>
              <button onClick={() => setSelectedCustomer(null)} style={{ background: "none", border: "none", cursor: "pointer" }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px", fontSize: "12px" }}>
              <div className="monad-card" style={{ padding: "16px", backgroundColor: "#ffffff" }}>
                <div style={{ color: "var(--color-smoke)", fontSize: "10px", textTransform: "uppercase", marginBottom: "6px" }}>
                  Contact Information
                </div>
                <div><strong>Contact:</strong> {selectedCustomer.contact_person}</div>
                <div><strong>Email:</strong> {selectedCustomer.email}</div>
                <div><strong>Phone:</strong> {selectedCustomer.phone}</div>
              </div>

              <div className="monad-card" style={{ padding: "16px", backgroundColor: "#ffffff" }}>
                <div style={{ color: "var(--color-smoke)", fontSize: "10px", textTransform: "uppercase", marginBottom: "6px" }}>
                  Billing Address
                </div>
                <div>{selectedCustomer.billing_street}</div>
                <div>{selectedCustomer.billing_city}, {selectedCustomer.billing_state} {selectedCustomer.billing_postal_code}</div>
                <div>{selectedCustomer.billing_country}</div>
              </div>

              <div className="monad-card" style={{ padding: "16px", backgroundColor: "#ffffff" }}>
                <div style={{ color: "var(--color-smoke)", fontSize: "10px", textTransform: "uppercase", marginBottom: "6px" }}>
                  Financial Standing
                </div>
                <div><strong>Total Outstanding:</strong> $1,950.00</div>
                <div><strong>Overdue Balance:</strong> $0.00</div>
                <div><strong>Default Payment Terms:</strong> Net 30 Days</div>
              </div>

              <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
                <button className="btn-primary-blue" style={{ flex: 1, justifyContent: "center" }}>
                  New Quotation
                </button>
                <button onClick={() => setSelectedCustomer(null)} className="btn-ghost" style={{ flex: 1, justifyContent: "center" }}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Customer Modal */}
      {isNewModalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(36, 36, 36, 0.4)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
          }}
        >
          <div className="monad-card" style={{ width: "100%", maxWidth: "460px", backgroundColor: "#ffffff" }}>
            <h2 className="font-serif" style={{ fontSize: "24px", margin: "0 0 16px 0" }}>Create Customer Record</h2>
            <form onSubmit={handleCreateCustomer} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Company Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Corporation"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "13px", boxSizing: "border-box" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Primary Contact Person
                </label>
                <input
                  type="text"
                  required
                  placeholder="John Doe"
                  value={contactPerson}
                  onChange={(e) => setContactPerson(e.target.value)}
                  style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "13px", boxSizing: "border-box" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="billing@acme.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "13px", boxSizing: "border-box" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Phone Number
                </label>
                <input
                  type="text"
                  placeholder="+1 (555) 000-0000"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "13px", boxSizing: "border-box" }}
                />
              </div>

              <div style={{ display: "flex", gap: "10px", marginTop: "14px" }}>
                <button type="submit" className="btn-primary-blue" style={{ flex: 1, justifyContent: "center" }}>
                  Save Customer
                </button>
                <button type="button" onClick={() => setIsNewModalOpen(false)} className="btn-ghost" style={{ flex: 1, justifyContent: "center" }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
