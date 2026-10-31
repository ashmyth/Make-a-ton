import React, { useState } from "react";
import type { User } from "../api";

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

  const navItem = (id: ConsoleRoute, label: string, badge?: number) => {
    const isActive = activeRoute === id;
    return (
      <button
        onClick={() => setActiveRoute(id)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "7px 12px",
          borderRadius: "8px",
          backgroundColor: isActive ? "#ffffff" : "transparent",
          border: isActive ? "1px solid var(--color-ash)" : "1px solid transparent",
          color: isActive ? "var(--color-off-black)" : "var(--color-graphite)",
          fontSize: "12px",
          fontFamily: "var(--font-mono)",
          cursor: "pointer",
          textAlign: "left",
          transition: "all 0.12s ease",
          marginBottom: "2px",
        }}
      >
        <span>{label}</span>
        {badge !== undefined && badge > 0 && (
          <span
            style={{
              backgroundColor: "var(--color-coral)",
              color: "#ffffff",
              fontSize: "10px",
              padding: "1px 6px",
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
    <div style={{ display: "flex", minHeight: "calc(100vh - 57px)", backgroundColor: "var(--color-parchment)" }}>
      {/* Sidebar Navigation */}
      <aside
        style={{
          width: "240px",
          borderRight: "1px solid var(--color-ash)",
          padding: "16px 12px",
          flexShrink: 0,
          backgroundColor: "rgba(246, 243, 241, 0.7)",
        }}
      >
        <div style={{ marginBottom: "16px" }}>
          {navItem("dashboard", "Dashboard")}
        </div>

        {/* SALES SECTION */}
        <div style={{ marginBottom: "16px" }}>
          <div style={{ fontSize: "10px", color: "var(--color-smoke)", textTransform: "uppercase", padding: "0 12px 6px 12px" }}>
            Sales & Clients
          </div>
          {navItem("customers", "Customers")}
          {navItem("quotations", "Quotations")}
          {navItem("subscriptions", "Subscriptions")}
          {navItem("requests", "Requests", 3)}
        </div>

        {/* BILLING SECTION */}
        <div style={{ marginBottom: "16px" }}>
          <div style={{ fontSize: "10px", color: "var(--color-smoke)", textTransform: "uppercase", padding: "0 12px 6px 12px" }}>
            Billing & Collections
          </div>
          {navItem("invoices", "Invoices")}
          {navItem("payments", "Payments")}
          {navItem("billing-failures", "Billing Failures", 2)}
        </div>

        {/* CATALOG SECTION */}
        <div style={{ marginBottom: "16px" }}>
          <div style={{ fontSize: "10px", color: "var(--color-smoke)", textTransform: "uppercase", padding: "0 12px 6px 12px" }}>
            Catalog & Rules
          </div>
          {navItem("products", "Products")}
          {navItem("plans", "Plans")}
          {isAdmin && navItem("taxes", "Taxes")}
          {isAdmin && navItem("discounts", "Discounts")}
          {navItem("templates", "Templates")}
        </div>

        {/* ADMIN SECTION */}
        {isAdmin && (
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "10px", color: "var(--color-smoke)", textTransform: "uppercase", padding: "0 12px 6px 12px" }}>
              Administration
            </div>
            {navItem("staff", "Staff & Roles")}
            {navItem("audit", "Audit Log")}
          </div>
        )}
      </aside>

      {/* Main Workspace Area */}
      <main style={{ flex: 1, padding: "24px 32px", overflowY: "auto", maxWidth: "1280px" }}>
        {renderContent()}
      </main>
    </div>
  );
};
