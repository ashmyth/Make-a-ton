import React from "react";
import type { User } from "../api";
import { LogOut, ArrowRight } from "lucide-react";

interface NavbarProps {
  currentUser: User | null;
  activeView: "portal" | "console" | "commercial";
  onSwitchView: (view: "portal" | "console" | "commercial") => void;
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
  const isStaff = currentUser && ["ADMINISTRATOR", "OPERATIONS", "FINANCE"].includes(currentUser.role);

  return (
    <header
      style={{
        backgroundColor: "var(--color-parchment)",
        borderBottom: "1px solid var(--color-ash)",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: "1440px",
          margin: "0 auto",
          padding: "12px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                width: "28px",
                height: "28px",
                borderRadius: "9999px",
                backgroundColor: "var(--color-off-black)",
                color: "#f6f3f1",
                fontFamily: "var(--font-mono)",
                fontWeight: 600,
                fontSize: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              BL
            </span>
            <span
              className="font-serif"
              style={{
                fontSize: "22px",
                color: "var(--color-off-black)",
                letterSpacing: "-0.02em",
              }}
            >
              Brightloop
            </span>
          </div>

          <span
            style={{
              fontSize: "11px",
              color: "var(--color-smoke)",
              textTransform: "uppercase",
              paddingLeft: "8px",
              borderLeft: "1px solid var(--color-ash)",
            }}
          >
            Editorial Subscription System
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {currentUser && isStaff && (
            <div
              style={{
                display: "inline-flex",
                backgroundColor: "#ffffff",
                border: "1px solid var(--color-ash)",
                borderRadius: "9999px",
                padding: "3px",
              }}
            >
              <button
                onClick={() => onSwitchView("portal")}
                style={{
                  padding: "6px 14px",
                  borderRadius: "9999px",
                  fontSize: "11px",
                  textTransform: "uppercase",
                  fontWeight: 500,
                  cursor: "pointer",
                  border: "none",
                  backgroundColor: activeView === "portal" ? "var(--color-off-black)" : "transparent",
                  color: activeView === "portal" ? "#ffffff" : "var(--color-graphite)",
                  transition: "all 0.15s ease",
                }}
              >
                Customer Portal
              </button>
              <button
                onClick={() => onSwitchView("console")}
                style={{
                  padding: "6px 14px",
                  borderRadius: "9999px",
                  fontSize: "11px",
                  textTransform: "uppercase",
                  fontWeight: 500,
                  cursor: "pointer",
                  border: "none",
                  backgroundColor: activeView === "console" ? "var(--color-off-black)" : "transparent",
                  color: activeView === "console" ? "#ffffff" : "var(--color-graphite)",
                  transition: "all 0.15s ease",
                }}
              >
                Staff Console
              </button>
              <button
                onClick={() => onSwitchView("commercial")}
                style={{
                  padding: "6px 14px",
                  borderRadius: "9999px",
                  fontSize: "11px",
                  textTransform: "uppercase",
                  fontWeight: 500,
                  cursor: "pointer",
                  border: "none",
                  backgroundColor: activeView === "commercial" ? "var(--color-off-black)" : "transparent",
                  color: activeView === "commercial" ? "#ffffff" : "var(--color-graphite)",
                  transition: "all 0.15s ease",
                }}
              >
                Commercial
              </button>
            </div>
          )}

          {currentUser ? (
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: "13px", fontWeight: 500, color: "var(--color-off-black)" }}>
                  {currentUser.email.split("@")[0]}
                </div>
                <div style={{ fontSize: "10px", color: "var(--color-smoke)", textTransform: "uppercase" }}>
                  {currentUser.role}
                </div>
              </div>
              <button
                onClick={onLogout}
                className="btn-ghost"
                style={{ padding: "6px 12px", fontSize: "11px" }}
                title="Sign out"
              >
                <LogOut size={13} />
                <span>Exit</span>
              </button>
            </div>
          ) : (
            <button onClick={onOpenLogin} className="btn-primary-blue">
              <span>Sign In</span>
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
