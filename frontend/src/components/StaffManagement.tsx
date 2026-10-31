import React, { useState } from "react";
import { UserPlus } from "lucide-react";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: "ADMINISTRATOR" | "OPERATIONS" | "FINANCE";
  is_active: boolean;
  created_at: string;
}

export const StaffManagement: React.FC = () => {
  const [staffList, setStaffList] = useState<UserProfile[]>([
    {
      id: "u-1",
      email: "alice@brightloop.io",
      full_name: "Alice Vance",
      role: "ADMINISTRATOR",
      is_active: true,
      created_at: "2026-01-01",
    },
    {
      id: "u-2",
      email: "priya@brightloop.io",
      full_name: "Priya Sharma",
      role: "FINANCE",
      is_active: true,
      created_at: "2026-02-15",
    },
    {
      id: "u-3",
      email: "bob@brightloop.io",
      full_name: "Bob Miller",
      role: "OPERATIONS",
      is_active: true,
      created_at: "2026-03-10",
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"ADMINISTRATOR" | "OPERATIONS" | "FINANCE">("OPERATIONS");

  const handleAddStaff = (e: React.FormEvent) => {
    e.preventDefault();
    const newStaff: UserProfile = {
      id: `u-${Date.now()}`,
      email,
      full_name: fullName,
      role,
      is_active: true,
      created_at: new Date().toISOString().split("T")[0],
    };
    setStaffList([...staffList, newStaff]);
    setIsModalOpen(false);
  };

  const handleToggleActive = (id: string) => {
    setStaffList(
      staffList.map((s) => (s.id === id ? { ...s, is_active: !s.is_active } : s))
    );
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Access Control & RBAC
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Staff & Permissions
          </h1>
        </div>
        <button onClick={() => { setFullName(""); setEmail(""); setIsModalOpen(true); }} className="btn-primary-blue">
          <UserPlus size={14} />
          <span>Invite Staff</span>
        </button>
      </div>

      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>NAME</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>EMAIL</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>ASSIGNED ROLE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>STATUS</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {staffList.map((s) => (
              <tr key={s.id} style={{ borderBottom: "1px solid var(--color-ash)" }}>
                <td style={{ padding: "14px 16px", fontWeight: 600 }}>{s.full_name}</td>
                <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>{s.email}</td>
                <td style={{ padding: "14px 16px" }}>
                  <span className="badge-pill badge-neutral">{s.role}</span>
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <span className={`badge-pill ${s.is_active ? "badge-active" : "badge-neutral"}`}>
                    {s.is_active ? "Active" : "Deactivated"}
                  </span>
                </td>
                <td style={{ padding: "14px 16px", textAlign: "right" }}>
                  <button
                    onClick={() => handleToggleActive(s.id)}
                    className="btn-ghost"
                    style={{ padding: "4px 10px", fontSize: "11px", color: s.is_active ? "#991b1b" : "inherit" }}
                  >
                    {s.is_active ? "Deactivate" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
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
          <div className="monad-card" style={{ width: "100%", maxWidth: "440px", backgroundColor: "#ffffff" }}>
            <h2 className="font-serif" style={{ fontSize: "24px", margin: "0 0 16px 0" }}>Add Staff Member</h2>
            <form onSubmit={handleAddStaff} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="Dave Bowman"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
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
                  placeholder="dave@brightloop.io"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "13px", boxSizing: "border-box" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Role Profile
                </label>
                <select
                  value={role}
                  onChange={(e: any) => setRole(e.target.value)}
                  style={{ width: "100%", padding: "9px 12px", borderRadius: "6px", border: "1px solid var(--color-ash)", fontSize: "12px", fontFamily: "var(--font-mono)" }}
                >
                  <option value="OPERATIONS">Operations Staff</option>
                  <option value="FINANCE">Finance Staff</option>
                  <option value="ADMINISTRATOR">Administrator</option>
                </select>
              </div>

              <div style={{ display: "flex", gap: "10px", marginTop: "14px" }}>
                <button type="submit" className="btn-primary-blue" style={{ flex: 1, justifyContent: "center" }}>
                  Create Account
                </button>
                <button type="button" onClick={() => setIsModalOpen(false)} className="btn-ghost" style={{ flex: 1, justifyContent: "center" }}>
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
