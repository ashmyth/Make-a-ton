import React from "react";
import { LogOut } from "lucide-react";
import type { User } from "../api";

interface NavbarProps {
  currentUser: User | null;
  activeView: "portal" | "commercial" | "finance";
  onSwitchView: (view: "portal" | "commercial" | "finance") => void;
  onLogout: () => void;
  onOpenLogin: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  activeView,
  onSwitchView,
  onLogout,
  onOpenLogin,
}) => {
  const getSubTitle = () => {
    if (activeView === "commercial") return "Teammate 2 • Catalog & Subscriptions";
    if (activeView === "finance") return "Teammates 3 & 4 • Finance & Billing";
    return "Teammate 4 • Customer Portal";
  };

  return (
    <header style={{
      background: "#000000",
      borderBottom: "1px solid #333333",
      padding: "14px 24px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <div style={{
          background: "#fff313",
          color: "#000000",
          fontWeight: 800,
          fontSize: "14px",
          padding: "4px 8px",
          borderRadius: "4px",
          letterSpacing: "-0.5px",
        }}>
          ON.ENERGY
        </div>
        <span style={{ fontSize: "16px", fontWeight: 600, letterSpacing: "-0.3px", color: "#eeeeee" }}>
          Brightloop
        </span>
        <span style={{ fontSize: "12px", color: "#afafaf", background: "#1a1a1a", padding: "2px 8px", borderRadius: "4px", border: "1px solid #333333" }}>
          {getSubTitle()}
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        {/* View Switcher Pills */}
        <div style={{ display: "flex", background: "#1a1a1a", borderRadius: "6px", padding: "3px", border: "1px solid #333333", gap: "4px" }}>
          <button
            onClick={() => onSwitchView("portal")}
            style={{
              background: activeView === "portal" ? "#fff313" : "transparent",
              color: activeView === "portal" ? "#000000" : "#afafaf",
              border: "none",
              borderRadius: "4px",
              padding: "6px 14px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            Customer Portal
          </button>
          <button
            onClick={() => onSwitchView("commercial")}
            style={{
              background: activeView === "commercial" ? "#fff313" : "transparent",
              color: activeView === "commercial" ? "#000000" : "#afafaf",
              border: "none",
              borderRadius: "4px",
              padding: "6px 14px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            Commercial Console
          </button>
          <button
            onClick={() => onSwitchView("finance")}
            style={{
              background: activeView === "finance" ? "#fff313" : "transparent",
              color: activeView === "finance" ? "#000000" : "#afafaf",
              border: "none",
              borderRadius: "4px",
              padding: "6px 14px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            Finance Console
          </button>
        </div>

        {currentUser ? (
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginLeft: "8px" }}>
            <span style={{ fontSize: "13px", color: "#eeeeee", display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#00e676" }}></span>
              {currentUser.email} ({currentUser.role})
            </span>
            <button
              onClick={onLogout}
              className="btn-secondary"
              style={{ padding: "6px 10px", fontSize: "12px" }}
              title="Sign Out"
            >
              <LogOut size={14} />
            </button>
          </div>
        ) : (
          <button onClick={onOpenLogin} className="btn-yellow" style={{ padding: "6px 14px", fontSize: "13px" }}>
            Sign In
          </button>
        )}
      </div>
    </header>
  );
};
