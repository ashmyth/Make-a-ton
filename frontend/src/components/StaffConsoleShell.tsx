import React, { useState } from "react";
import type { User } from "../api";
import {
  LayoutDashboard,
  Users,
  FileSpreadsheet,
  Repeat,
  Inbox,
  FileText,
  CreditCard,
  AlertOctagon,
  Package,
  Layers,
  Percent,
  Tag,
  Copy,
  Shield,
  FileCheck,
  Search,
  ArrowUpRight,
  ChevronDown,
} from "lucide-react";

import { Logo } from "./Logo";
import { FinanceConsole } from "./FinanceConsole";
import { CustomerManagement } from "./CustomerManagement";
import { StaffManagement } from "./StaffManagement";
import { AuditTrail } from "./AuditTrail";
import { CatalogManagement } from "./CatalogManagement";
import { PlansManagement } from "./PlansManagement";
import { TaxesManagement } from "./TaxesManagement";
import { DiscountsManagement } from "./DiscountsManagement";
import { QuotationsManagement } from "./QuotationsManagement";
import { SubscriptionsManagement } from "./SubscriptionsManagement";
import { RequestsManagement } from "./RequestsManagement";
import { BillingFailuresManagement } from "./BillingFailuresManagement";

interface StaffConsoleShellProps {
  currentUser: User;
}

export type ConsoleRoute =
  | "dashboard"
  | "customers"
  | "quotations"
  | "subscriptions"
  | "requests"
  | "invoices"
  | "payments"
  | "billing-failures"
  | "products"
  | "plans"
  | "taxes"
  | "discounts"
  | "templates"
  | "staff"
  | "audit";

export const StaffConsoleShell: React.FC<StaffConsoleShellProps> = ({ currentUser }) => {
  const [activeRoute, setActiveRoute] = useState<ConsoleRoute>("dashboard");
  const [searchQuery, setSearchQuery] = useState("");
  const isAdmin = currentUser.role === "ADMINISTRATOR";

  const renderContent = () => {
    switch (activeRoute) {
      case "dashboard":
      case "invoices":
      case "payments":
        return <FinanceConsole />;
      case "customers":
        return <CustomerManagement />;
      case "quotations":
        return <QuotationsManagement />;
      case "subscriptions":
        return <SubscriptionsManagement />;
      case "requests":
        return <RequestsManagement />;
      case "billing-failures":
        return <BillingFailuresManagement />;
      case "products":
        return <CatalogManagement />;
      case "plans":
        return <PlansManagement />;
      case "taxes":
        return <TaxesManagement />;
      case "discounts":
        return <DiscountsManagement />;
      case "templates":
        return <QuotationsManagement initialTab="templates" />;
      case "staff":
        return <StaffManagement />;
      case "audit":
        return <AuditTrail />;
      default:
        return <FinanceConsole />;
    }
  };

  const navItem = (id: ConsoleRoute, label: string, Icon: React.ComponentType<{ size?: number; style?: React.CSSProperties }>, badge?: number) => {
    const isActive = activeRoute === id;
    return (
      <button
        onClick={() => setActiveRoute(id)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "9px 14px",
          borderRadius: "9999px",
          backgroundColor: isActive ? "var(--color-off-black)" : "transparent",
          color: isActive ? "#ffffff" : "var(--color-graphite)",
          border: "none",
          fontSize: "13px",
          fontFamily: "var(--font-mono)",
          cursor: "pointer",
          textAlign: "left",
          transition: "all 0.15s ease",
          marginBottom: "3px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Icon size={16} style={{ color: isActive ? "#ffffff" : "var(--color-smoke)" }} />
          <span style={{ fontWeight: isActive ? 500 : 400 }}>{label}</span>
        </div>
        {badge !== undefined && badge > 0 && (
          <span
            style={{
              backgroundColor: isActive ? "var(--color-lake-blue)" : "var(--color-periwinkle-mist)",
              color: isActive ? "#ffffff" : "var(--color-lake-blue)",
              fontSize: "10px",
              padding: "2px 7px",
              borderRadius: "9999px",
              fontWeight: 600,
            }}
          >
            {badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--color-parchment)" }}>
      {/* Top Application Bar */}
      <header
        style={{
          height: "64px",
          padding: "0 32px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid var(--color-ash)",
          backgroundColor: "var(--color-parchment)",
        }}
      >
        {/* Brand identity */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Logo size={26} style={{ color: "var(--color-off-black)" }} />
          <span className="font-serif" style={{ fontSize: "24px", color: "var(--color-off-black)", letterSpacing: "-0.02em" }}>
            Brightloop
          </span>
        </div>

        {/* Global Search Pill Input */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            backgroundColor: "#ffffff",
            border: "1px solid var(--color-ash)",
            borderRadius: "9999px",
            padding: "8px 18px",
            width: "380px",
          }}
        >
          <Search size={15} color="var(--color-smoke)" />
          <input
            type="text"
            placeholder="Search customers, invoices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              border: "none",
              background: "transparent",
              color: "var(--color-off-black)",
              fontSize: "13px",
              fontFamily: "var(--font-mono)",
              outline: "none",
              width: "100%",
            }}
          />
          <kbd
            style={{
              fontSize: "10px",
              padding: "2px 6px",
              borderRadius: "4px",
              backgroundColor: "var(--color-parchment)",
              color: "var(--color-smoke)",
              border: "1px solid var(--color-ash)",
            }}
          >
            ⌘K
          </kbd>
        </div>

        {/* User profile capsule */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "9999px",
              backgroundColor: "var(--color-periwinkle-mist)",
              color: "var(--color-lake-blue)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 600,
              fontSize: "12px",
            }}
          >
            {currentUser.full_name ? currentUser.full_name.charAt(0) : "P"}
          </div>
          <div style={{ fontSize: "13px", color: "var(--color-off-black)", fontWeight: 500 }}>
            {currentUser.full_name || currentUser.email} <span style={{ color: "var(--color-smoke)" }}>({currentUser.role})</span>
          </div>
          <ChevronDown size={14} color="var(--color-smoke)" />
        </div>
      </header>

      {/* Main Body: Sidebar + Workspace */}
      <div style={{ display: "flex", minHeight: "calc(100vh - 64px)" }}>
        {/* Sidebar Navigation */}
        <aside
          style={{
            width: "250px",
            borderRight: "1px solid var(--color-ash)",
            padding: "24px 16px",
            flexShrink: 0,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ marginBottom: "20px" }}>
              {navItem("dashboard", "Dashboard", LayoutDashboard)}
            </div>

            {/* SALES SECTION */}
            <div style={{ marginBottom: "22px" }}>
              <div style={{ fontSize: "11px", color: "var(--color-smoke)", textTransform: "uppercase", letterSpacing: "0.05em", padding: "0 14px 8px 14px" }}>
                SALES
              </div>
              {navItem("customers", "Customers", Users)}
              {navItem("quotations", "Quotations", FileSpreadsheet)}
              {navItem("subscriptions", "Subscriptions", Repeat)}
              {navItem("requests", "Requests", Inbox, 3)}
            </div>

            {/* BILLING SECTION */}
            <div style={{ marginBottom: "22px" }}>
              <div style={{ fontSize: "11px", color: "var(--color-smoke)", textTransform: "uppercase", letterSpacing: "0.05em", padding: "0 14px 8px 14px" }}>
                BILLING
              </div>
              {navItem("invoices", "Invoices", FileText)}
              {navItem("payments", "Payments", CreditCard)}
              {navItem("billing-failures", "Failures", AlertOctagon, 2)}
            </div>

            {/* CATALOG SECTION */}
            <div style={{ marginBottom: "22px" }}>
              <div style={{ fontSize: "11px", color: "var(--color-smoke)", textTransform: "uppercase", letterSpacing: "0.05em", padding: "0 14px 8px 14px" }}>
                CATALOG
              </div>
              {navItem("products", "Products", Package)}
              {navItem("plans", "Plans", Layers)}
              {isAdmin && navItem("taxes", "Taxes", Percent)}
              {isAdmin && navItem("discounts", "Discounts", Tag)}
              {navItem("templates", "Templates", Copy)}
            </div>

            {/* ADMIN SECTION */}
            {isAdmin && (
              <div style={{ marginBottom: "20px" }}>
                <div style={{ fontSize: "11px", color: "var(--color-smoke)", textTransform: "uppercase", letterSpacing: "0.05em", padding: "0 14px 8px 14px" }}>
                  ADMIN
                </div>
                {navItem("staff", "Staff", Shield)}
                {navItem("audit", "Audit log", FileCheck)}
              </div>
            )}
          </div>

          {/* Bottom Card: Monad Periwinkle Mist Story Capsule */}
          <div
            style={{
              backgroundColor: "var(--color-periwinkle-mist)",
              border: "1px solid #bfdbfe",
              borderRadius: "20px",
              padding: "20px",
              position: "relative",
            }}
          >
            <div
              style={{
                width: "28px",
                height: "28px",
                borderRadius: "9999px",
                backgroundColor: "var(--color-off-black)",
                color: "#ffffff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "12px",
              }}
            >
              <ArrowUpRight size={14} />
            </div>
            <div className="font-serif" style={{ fontSize: "17px", color: "var(--color-off-black)", lineHeight: "1.25" }}>
              Less admin.
              <br />
              More flow.
            </div>
            <div style={{ fontSize: "11px", color: "var(--color-graphite)", marginTop: "8px" }}>
              • Staff workspace
            </div>
          </div>
        </aside>

        {/* Main Workspace Area */}
        <main style={{ flex: 1, padding: "32px 40px", overflowY: "auto" }}>
          {renderContent()}
        </main>
      </div>
    </div>
  );
};
