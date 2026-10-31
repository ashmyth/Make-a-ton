import React, { useState, useEffect } from "react";
import {
  Package,
  Layers,
  FileText,
  Repeat,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Plus,
  Copy,
  Archive,
  Send,
  Eye,
  Play,
  Pause,
  RefreshCw,
  XCircle,
  Calculator,
  Search,
  ShieldAlert,
} from "lucide-react";
import {
  api,
  type Product,
  type SubscriptionPlan,
  type QuotationTemplate,
  type Quotation,
  type SubscriptionDetail,
  type PricingCalculationResult,
  type SubscriptionBillingExport,
} from "../api";

export const CommercialConsole: React.FC = () => {
  const [activeTab, setActiveTab] = useState<
    "products" | "plans" | "templates" | "quotations" | "subscriptions"
  >("products");

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Data states
  const [products, setProducts] = useState<Product[]>([]);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [templates, setTemplates] = useState<QuotationTemplate[]>([]);
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [subscriptions, setSubscriptions] = useState<SubscriptionDetail[]>([]);

  // View modes
  const [productViewAsCustomer, setProductViewAsCustomer] = useState(false);
  const [productSearch, setProductSearch] = useState("");
  const [quotationStatusFilter, setQuotationStatusFilter] = useState("all");
  const [subscriptionFilter, setSubscriptionFilter] = useState<"all" | "active" | "paused" | "closed" | "action_required">("all");

  // Modals
  const [isNewProductModalOpen, setIsNewProductModalOpen] = useState(false);
  const [isNewVariantModalOpen, setIsNewVariantModalOpen] = useState(false);
  const [selectedProductForVariant, setSelectedProductForVariant] = useState<Product | null>(null);

  const [isNewPlanModalOpen, setIsNewPlanModalOpen] = useState(false);
  const [isPricingCalcOpen, setIsPricingCalcOpen] = useState(false);
  const [calcSelectedPlan, setCalcSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [calcLines, setCalcLines] = useState<Array<{ product_id: string; variant_id: string | null; quantity: number; is_primary: boolean }>>([]);
  const [calcResult, setCalcResult] = useState<PricingCalculationResult | null>(null);

  const [isNewTemplateModalOpen, setIsNewTemplateModalOpen] = useState(false);
  const [isCreateQuoteFromTemplateModalOpen, setIsCreateQuoteFromTemplateModalOpen] = useState(false);
  const [selectedTemplateForQuote, setSelectedTemplateForQuote] = useState<QuotationTemplate | null>(null);

  const [isNewQuoteModalOpen, setIsNewQuoteModalOpen] = useState(false);
  const [isExtendQuoteModalOpen, setIsExtendQuoteModalOpen] = useState(false);
  const [selectedQuoteForExtend, setSelectedQuoteForExtend] = useState<Quotation | null>(null);
  const [extendDays, setExtendDays] = useState(30);

  const [isConvertQuoteModalOpen, setIsConvertQuoteModalOpen] = useState(false);
  const [selectedQuoteForConvert, setSelectedQuoteForConvert] = useState<Quotation | null>(null);

  const [isPauseSubModalOpen, setIsPauseSubModalOpen] = useState(false);
  const [isRenewSubModalOpen, setIsRenewSubModalOpen] = useState(false);
  const [isCloseSubModalOpen, setIsCloseSubModalOpen] = useState(false);
  const [selectedSub, setSelectedSub] = useState<SubscriptionDetail | null>(null);
  const [actionReason, setActionReason] = useState("");
  const [earlyCloseForce, setEarlyCloseForce] = useState(false);

  const [isBillingFeedOpen, setIsBillingFeedOpen] = useState(false);
  const [billingFeedData, setBillingFeedData] = useState<SubscriptionBillingExport[]>([]);

  // Load active tab data
  useEffect(() => {
    loadData();
  }, [activeTab, productViewAsCustomer]);

  const showMsg = (text: string, type: "success" | "error" = "success") => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 6000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === "products") {
        const query = productViewAsCustomer ? { view_as: "customer" } : { status: "all" };
        const prods = await api.commercial.getProducts(query);
        setProducts(prods);
      } else if (activeTab === "plans") {
        const pl = await api.commercial.getPlans({ status: "all" });
        setPlans(pl);
        const prods = await api.commercial.getProducts();
        setProducts(prods);
      } else if (activeTab === "templates") {
        const tmpls = await api.commercial.getTemplates({ status: "all" });
        setTemplates(tmpls);
        const pl = await api.commercial.getPlans();
        setPlans(pl);
        const prods = await api.commercial.getProducts();
        setProducts(prods);
      } else if (activeTab === "quotations") {
        const quotes = await api.commercial.getQuotations();
        setQuotations(quotes);
        const pl = await api.commercial.getPlans();
        setPlans(pl);
        const prods = await api.commercial.getProducts();
        setProducts(prods);
      } else if (activeTab === "subscriptions") {
        const subs = await api.commercial.getSubscriptions();
        setSubscriptions(subs);
      }
    } catch (err: any) {
      showMsg(err.message || "Failed to load commercial data", "error");
    } finally {
      setLoading(false);
    }
  };

  // Products Handlers
  const handleArchiveProduct = async (id: string) => {
    try {
      await api.commercial.archiveProduct(id);
      showMsg("Product successfully archived (preserved for historical auditing).");
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to archive product", "error");
    }
  };

  const handleArchiveVariant = async (id: string) => {
    try {
      await api.commercial.archiveVariant(id);
      showMsg("Variant archived.");
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to archive variant", "error");
    }
  };

  // Plans Handlers
  const handleArchivePlan = async (id: string) => {
    try {
      await api.commercial.archivePlan(id);
      showMsg("Subscription Plan archived.");
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to archive plan", "error");
    }
  };

  const handleCalculatePricing = async () => {
    if (!calcSelectedPlan || calcLines.length === 0) {
      showMsg("Please select a plan and add at least one product line.", "error");
      return;
    }
    try {
      const res = await api.commercial.calculatePricing(calcSelectedPlan.id, {
        lines: calcLines,
        validate_minimums: true,
      });
      setCalcResult(res);
    } catch (err: any) {
      showMsg(err.message || "Pricing calculation failed", "error");
    }
  };

  // Templates Handlers
  const handleDuplicateTemplate = async (template: QuotationTemplate) => {
    try {
      const cloned = await api.commercial.duplicateTemplate(template.id);
      showMsg(`Deep-cloned template '${template.name}' into '${cloned.name}'.`);
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to duplicate template", "error");
    }
  };

  const handleArchiveTemplate = async (id: string) => {
    try {
      await api.commercial.archiveTemplate(id);
      showMsg("Template archived.");
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to archive template", "error");
    }
  };

  // Quotation Workflow Handlers
  const handleSendQuote = async (id: string) => {
    try {
      await api.commercial.sendQuotation(id);
      showMsg("Quotation marked as Sent to Customer.");
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to send quotation", "error");
    }
  };

  const handleReviewQuote = async (id: string) => {
    try {
      await api.commercial.reviewQuotation(id);
      showMsg("Quotation marked as Reviewed.");
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to review quotation", "error");
    }
  };

  const handleConfirmQuote = async (quote: Quotation) => {
    try {
      await api.commercial.confirmQuotation(quote.id, "Operations Staff");
      showMsg(`Quotation ${quote.quotation_number} confirmed! Ready for conversion to active subscription.`);
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Confirmation failed. Expired quotations cannot be confirmed unless extended.", "error");
    }
  };

  const handleExtendQuote = async () => {
    if (!selectedQuoteForExtend) return;
    try {
      await api.commercial.extendQuotation(selectedQuoteForExtend.id, extendDays);
      showMsg(`Quotation extended by ${extendDays} days.`);
      setIsExtendQuoteModalOpen(false);
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to extend quotation", "error");
    }
  };

  const handleConvertQuote = async () => {
    if (!selectedQuoteForConvert) return;
    try {
      const sub = await api.commercial.convertToSubscription(selectedQuoteForConvert.id);
      showMsg(`Quotation converted! Created subscription ${sub.subscription_number}.`);
      setIsConvertQuoteModalOpen(false);
      setActiveTab("subscriptions");
    } catch (err: any) {
      showMsg(err.message || "Conversion failed.", "error");
    }
  };

  // Subscriptions Handlers
  const handlePauseSub = async () => {
    if (!selectedSub) return;
    try {
      await api.commercial.pauseSubscription(selectedSub.id, actionReason);
      showMsg(`Subscription ${selectedSub.subscription_number} paused.`);
      setIsPauseSubModalOpen(false);
      setActionReason("");
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to pause subscription. Check plan policy.", "error");
    }
  };

  const handleResumeSub = async (sub: SubscriptionDetail) => {
    try {
      await api.commercial.resumeSubscription(sub.id);
      showMsg(`Subscription ${sub.subscription_number} resumed to running condition.`);
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Failed to resume subscription", "error");
    }
  };

  const handleRenewSub = async () => {
    if (!selectedSub) return;
    try {
      const succ = await api.commercial.renewSubscription(selectedSub.id);
      showMsg(`Subscription renewed into successor ${succ.subscription_number}. Predecessor closed.`);
      setIsRenewSubModalOpen(false);
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Renewal failed. Check plan allow_renewal policy.", "error");
    }
  };

  const handleCloseSub = async () => {
    if (!selectedSub) return;
    try {
      await api.commercial.closeSubscription(selectedSub.id, {
        reason: actionReason,
        early: earlyCloseForce,
      });
      showMsg(`Subscription ${selectedSub.subscription_number} closed.`);
      setIsCloseSubModalOpen(false);
      setActionReason("");
      setEarlyCloseForce(false);
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Closure failed.", "error");
    }
  };

  const handleSweepExpiries = async () => {
    try {
      const res = await api.commercial.sweepExpiries();
      showMsg(
        `Expiry sweep complete: ${res.auto_closed_count} subscriptions auto-closed; ${res.action_required_count} routed to Action Required queue.`
      );
      loadData();
    } catch (err: any) {
      showMsg(err.message || "Sweep failed.", "error");
    }
  };

  const handleOpenBillingFeed = async () => {
    try {
      const data = await api.commercial.getDueForBilling();
      setBillingFeedData(data);
      setIsBillingFeedOpen(true);
    } catch (err: any) {
      showMsg(err.message || "Failed to load billing feed", "error");
    }
  };

  // Filtered queries
  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(productSearch.toLowerCase()) ||
    (p.type && p.type.toLowerCase().includes(productSearch.toLowerCase()))
  );

  const filteredQuotes = quotations.filter((q) => {
    if (quotationStatusFilter === "all") return true;
    if (quotationStatusFilter === "expired") return q.is_expired;
    return q.status === quotationStatusFilter;
  });

  const filteredSubs = subscriptions.filter((s) => {
    if (subscriptionFilter === "all") return true;
    if (subscriptionFilter === "active") return s.status === "active" && s.operational_status === "running" && !s.action_required;
    if (subscriptionFilter === "paused") return s.operational_status === "paused";
    if (subscriptionFilter === "closed") return s.status === "closed";
    if (subscriptionFilter === "action_required") return s.action_required;
    return true;
  });

  return (
    <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px 24px" }}>
      {/* Header Banner */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "28px" }}>
        <div>
          <div style={{ fontSize: "12px", color: "#fff313", textTransform: "uppercase", letterSpacing: "1px", fontWeight: 700, marginBottom: "6px" }}>
            Teammate 2 • Commercial Engine
          </div>
          <h1 style={{ fontSize: "32px", fontWeight: 300, letterSpacing: "-0.03em", color: "#eeeeee" }}>
            Commercial Operations & Subscriptions
          </h1>
          <p style={{ color: "#afafaf", fontSize: "14px", marginTop: "4px" }}>
            Catalog management, variant price adjustments, quotation templates & workflow, and active subscription lifecycles.
          </p>
        </div>

        {/* Global Toolbar */}
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={handleSweepExpiries}
            className="btn-secondary"
            title="Automatically closes expired subscriptions under auto_close plans or flags action required"
          >
            <Clock size={15} style={{ color: "#fff313" }} />
            Run Expiry Sweep
          </button>
          <button
            onClick={handleOpenBillingFeed}
            className="btn-yellow"
            title="Inspect subscriptions returned to Teammate 3 billing engine"
          >
            <Repeat size={15} />
            Teammate 3 Billing Feed
          </button>
        </div>
      </div>

      {/* Global Alert Message */}
      {message && (
        <div style={{
          backgroundColor: message.type === "success" ? "rgba(0, 230, 118, 0.1)" : "rgba(255, 77, 77, 0.15)",
          border: `1px solid ${message.type === "success" ? "#00e676" : "#ff4d4d"}`,
          color: message.type === "success" ? "#00e676" : "#ff4d4d",
          padding: "12px 16px",
          borderRadius: "6px",
          marginBottom: "24px",
          fontSize: "14px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
        }}>
          {message.type === "success" ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Domain Navigation Tabs */}
      <div style={{
        display: "flex",
        background: "#1a1a1a",
        padding: "4px",
        borderRadius: "8px",
        border: "1px solid #333333",
        marginBottom: "28px",
        overflowX: "auto",
        gap: "4px",
      }}>
        {[
          { id: "products", label: "Product Catalog & Variants", icon: Package, count: products.length },
          { id: "plans", label: "Subscription Plans & Pricing", icon: Layers, count: plans.length },
          { id: "templates", label: "Quotation Templates", icon: Copy, count: templates.length },
          { id: "quotations", label: "Quotations Workflow", icon: FileText, count: quotations.length },
          { id: "subscriptions", label: "Subscriptions Lifecycle", icon: Repeat, count: subscriptions.length },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                background: isActive ? "#fff313" : "transparent",
                color: isActive ? "#000000" : "#afafaf",
                border: "none",
                borderRadius: "6px",
                padding: "8px 16px",
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                transition: "all 0.15s ease",
                whiteSpace: "nowrap",
              }}
            >
              <Icon size={15} />
              {tab.label}
              <span style={{
                background: isActive ? "#000000" : "#262626",
                color: isActive ? "#fff313" : "#afafaf",
                padding: "1px 6px",
                borderRadius: "10px",
                fontSize: "11px",
                fontWeight: 700,
              }}>
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {loading && (
        <div style={{ textAlign: "center", padding: "48px 0", color: "#afafaf" }}>
          <RefreshCw size={24} style={{ animation: "spin 1s linear infinite" }} />
          <p style={{ marginTop: "12px", fontSize: "14px" }}>Synchronizing commercial data...</p>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 1: PRODUCT CATALOG & VARIANTS                                        */}
      {/* ========================================================================= */}
      {!loading && activeTab === "products" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              <div style={{ position: "relative", width: "260px" }}>
                <Search size={14} style={{ position: "absolute", left: "12px", top: "11px", color: "#afafaf" }} />
                <input
                  type="text"
                  placeholder="Search products or type..."
                  value={productSearch}
                  onChange={(e) => setProductSearch(e.target.value)}
                  style={{
                    background: "#1a1a1a",
                    border: "1px solid #333333",
                    color: "#eeeeee",
                    padding: "8px 12px 8px 32px",
                    borderRadius: "6px",
                    fontSize: "13px",
                    width: "100%",
                  }}
                />
              </div>

              {/* View As Customer Toggle */}
              <button
                onClick={() => setProductViewAsCustomer(!productViewAsCustomer)}
                style={{
                  background: productViewAsCustomer ? "rgba(255, 243, 19, 0.15)" : "#1a1a1a",
                  color: productViewAsCustomer ? "#fff313" : "#afafaf",
                  border: `1px solid ${productViewAsCustomer ? "#fff313" : "#333333"}`,
                  padding: "7px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <Eye size={14} />
                {productViewAsCustomer ? "Customer Mode Active (Cost Price Hidden)" : "Staff Mode (Full Margins Visible)"}
              </button>
            </div>

            <button onClick={() => setIsNewProductModalOpen(true)} className="btn-yellow">
              <Plus size={15} />
              Add Product
            </button>
          </div>

          {filteredProducts.length === 0 ? (
            <div className="card-carbon" style={{ textAlign: "center", padding: "48px 24px" }}>
              <Package size={36} style={{ color: "#afafaf", margin: "0 auto 12px" }} />
              <h3 style={{ fontSize: "16px", fontWeight: 600 }}>No products found</h3>
              <p style={{ color: "#afafaf", fontSize: "13px", marginTop: "4px" }}>
                Create a product or clear your search query.
              </p>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "16px" }}>
              {filteredProducts.map((product) => (
                <div key={product.id} className="card-carbon">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <h3 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee" }}>{product.name}</h3>
                        <span className={`badge ${product.status === "active" ? "badge-active" : "badge-paused"}`}>
                          {product.status}
                        </span>
                        {product.type && (
                          <span style={{ fontSize: "11px", color: "#afafaf", background: "#262626", padding: "2px 8px", borderRadius: "4px" }}>
                            {product.type}
                          </span>
                        )}
                      </div>
                      {product.notes && !productViewAsCustomer && (
                        <p style={{ color: "#afafaf", fontSize: "13px", marginTop: "4px" }}>{product.notes}</p>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      <div style={{ textAlign: "right", marginRight: "12px" }}>
                        <div style={{ fontSize: "18px", fontWeight: 700, color: "#fff313" }}>
                          ₹{product.sales_price}
                        </div>
                        {!productViewAsCustomer && product.cost_price && (
                          <div style={{ fontSize: "11px", color: "#afafaf" }}>
                            Cost: ₹{product.cost_price} (Margin: ₹{(parseFloat(product.sales_price) - parseFloat(product.cost_price)).toFixed(2)})
                          </div>
                        )}
                      </div>

                      {product.status === "active" && !productViewAsCustomer && (
                        <>
                          <button
                            onClick={() => {
                              setSelectedProductForVariant(product);
                              setIsNewVariantModalOpen(true);
                            }}
                            className="btn-secondary"
                            style={{ padding: "6px 10px", fontSize: "12px" }}
                          >
                            <Plus size={13} />
                            Add Variant
                          </button>
                          <button
                            onClick={() => handleArchiveProduct(product.id)}
                            className="btn-secondary"
                            style={{ padding: "6px 10px", fontSize: "12px" }}
                            title="Soft-archive product (preserves historical references)"
                          >
                            <Archive size={13} />
                            Archive
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Variants List */}
                  {product.variants && product.variants.length > 0 && (
                    <div style={{ borderTop: "1px solid #3d3d3d", paddingTop: "12px", marginTop: "12px" }}>
                      <div style={{ fontSize: "12px", color: "#afafaf", fontWeight: 600, marginBottom: "8px", textTransform: "uppercase" }}>
                        Product Variants & Price Adjustments ({product.variants.length})
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                        {product.variants.map((v) => (
                          <div
                            key={v.id}
                            style={{
                              background: "#262626",
                              border: "1px solid #3d3d3d",
                              borderRadius: "6px",
                              padding: "6px 10px",
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                              fontSize: "12px",
                            }}
                          >
                            <span style={{ color: "#eeeeee", fontWeight: 600 }}>
                              {v.attribute_name}: {v.value}
                            </span>
                            <span style={{ color: parseFloat(v.price_adjustment) >= 0 ? "#00e676" : "#ff4d4d", fontWeight: 700 }}>
                              {parseFloat(v.price_adjustment) >= 0 ? `+₹${v.price_adjustment}` : `-₹${Math.abs(parseFloat(v.price_adjustment))}`}
                            </span>
                            <span style={{ color: "#fff313", fontSize: "11px" }}>
                              (Total: ₹{v.total_unit_price})
                            </span>
                            {v.status === "active" && !productViewAsCustomer && (
                              <button
                                onClick={() => handleArchiveVariant(v.id)}
                                style={{ background: "none", border: "none", color: "#afafaf", cursor: "pointer", padding: "0 2px" }}
                                title="Archive variant"
                              >
                                <XCircle size={13} />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: SUBSCRIPTION PLANS & PRICING                                       */}
      {/* ========================================================================= */}
      {!loading && activeTab === "plans" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <p style={{ color: "#afafaf", fontSize: "14px" }}>
              Manage billing intervals (daily, weekly, monthly, yearly), minimum quantities, availability dates, and PRD §7.4 primary pricing overrides.
            </p>
            <div style={{ display: "flex", gap: "10px" }}>
              <button onClick={() => setIsPricingCalcOpen(true)} className="btn-secondary">
                <Calculator size={15} style={{ color: "#fff313" }} />
                PRD §7.4 Pricing Simulator
              </button>
              <button onClick={() => setIsNewPlanModalOpen(true)} className="btn-yellow">
                <Plus size={15} />
                Create Plan
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "16px" }}>
            {plans.map((plan) => (
              <div key={plan.id} className="card-carbon">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                  <div>
                    <h3 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee" }}>{plan.name}</h3>
                    <div style={{ display: "flex", gap: "6px", marginTop: "4px" }}>
                      <span className="badge badge-partial" style={{ textTransform: "capitalize" }}>
                        {plan.billing_interval}
                      </span>
                      <span className={`badge ${plan.status === "active" ? "badge-active" : "badge-paused"}`}>
                        {plan.status}
                      </span>
                    </div>
                  </div>
                  {plan.status === "active" && (
                    <button
                      onClick={() => handleArchivePlan(plan.id)}
                      className="btn-secondary"
                      style={{ padding: "4px 8px", fontSize: "11px" }}
                      title="Archive plan"
                    >
                      Archive
                    </button>
                  )}
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "12px", background: "#1f1f1f", padding: "10px", borderRadius: "6px", margin: "12px 0" }}>
                  <div>
                    <span style={{ color: "#afafaf" }}>Min Quantity:</span>{" "}
                    <strong style={{ color: "#eeeeee" }}>{plan.min_quantity}</strong>
                  </div>
                  <div>
                    <span style={{ color: "#afafaf" }}>Payment Terms:</span>{" "}
                    <strong style={{ color: "#eeeeee" }}>{plan.default_payment_terms}</strong>
                  </div>
                  {plan.default_primary_unit_price && (
                    <div style={{ gridColumn: "span 2" }}>
                      <span style={{ color: "#afafaf" }}>Primary Unit Override:</span>{" "}
                      <strong style={{ color: "#fff313" }}>₹{plan.default_primary_unit_price}</strong>
                    </div>
                  )}
                  {plan.availability_start_date && (
                    <div>
                      <span style={{ color: "#afafaf" }}>Available From:</span>{" "}
                      <strong style={{ color: "#eeeeee" }}>{plan.availability_start_date}</strong>
                    </div>
                  )}
                  {plan.availability_end_date && (
                    <div>
                      <span style={{ color: "#afafaf" }}>Available Until:</span>{" "}
                      <strong style={{ color: "#eeeeee" }}>{plan.availability_end_date}</strong>
                    </div>
                  )}
                </div>

                {/* Plan Policies */}
                <div style={{ fontSize: "11px", display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  <span style={{ background: plan.allow_pause ? "rgba(0, 230, 118, 0.15)" : "#262626", color: plan.allow_pause ? "#00e676" : "#afafaf", padding: "2px 6px", borderRadius: "4px" }}>
                    Pause: {plan.allow_pause ? "Permitted" : "Disallowed"}
                  </span>
                  <span style={{ background: plan.allow_renewal ? "rgba(0, 230, 118, 0.15)" : "#262626", color: plan.allow_renewal ? "#00e676" : "#afafaf", padding: "2px 6px", borderRadius: "4px" }}>
                    Renewal: {plan.allow_renewal ? "Permitted" : "Disallowed"}
                  </span>
                  <span style={{ background: plan.allow_early_closure ? "rgba(0, 230, 118, 0.15)" : "#262626", color: plan.allow_early_closure ? "#00e676" : "#afafaf", padding: "2px 6px", borderRadius: "4px" }}>
                    Early Close: {plan.allow_early_closure ? "Permitted" : "Disallowed"}
                  </span>
                  <span style={{ background: plan.auto_close_at_expiry ? "rgba(0, 230, 118, 0.15)" : "rgba(255, 77, 77, 0.15)", color: plan.auto_close_at_expiry ? "#00e676" : "#ff4d4d", padding: "2px 6px", borderRadius: "4px" }}>
                    Auto-Close at Expiry: {plan.auto_close_at_expiry ? "Yes" : "Action Required Queue"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: QUOTATION TEMPLATES                                                */}
      {/* ========================================================================= */}
      {!loading && activeTab === "templates" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <p style={{ color: "#afafaf", fontSize: "14px" }}>
              Standardize deals with reusable plans, product lines, and default validity windows. Templates can be deep-cloned.
            </p>
            <button onClick={() => setIsNewTemplateModalOpen(true)} className="btn-yellow">
              <Plus size={15} />
              New Template
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "16px" }}>
            {templates.map((template) => (
              <div key={template.id} className="card-carbon">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                  <div>
                    <h3 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee" }}>{template.name}</h3>
                    <div style={{ color: "#fff313", fontSize: "13px", fontWeight: 600, marginTop: "2px" }}>
                      Plan: {template.plan_name}
                    </div>
                  </div>
                  <span className={`badge ${template.status === "active" ? "badge-active" : "badge-paused"}`}>
                    {template.status}
                  </span>
                </div>

                <div style={{ fontSize: "12px", color: "#afafaf", margin: "8px 0" }}>
                  Validity Duration: <strong style={{ color: "#eeeeee" }}>{template.validity_days} days</strong>
                </div>

                {template.notes && (
                  <p style={{ fontSize: "12px", color: "#afafaf", marginBottom: "12px", fontStyle: "italic" }}>
                    "{template.notes}"
                  </p>
                )}

                {/* Preconfigured Lines */}
                <div style={{ background: "#1f1f1f", padding: "10px", borderRadius: "6px", marginBottom: "14px", fontSize: "12px" }}>
                  <div style={{ fontWeight: 600, color: "#afafaf", marginBottom: "6px" }}>Preconfigured Line Items:</div>
                  {template.lines && template.lines.length > 0 ? (
                    template.lines.map((l) => (
                      <div key={l.id} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", color: "#eeeeee" }}>
                        <span>
                          {l.product_name} {l.variant_value && `(${l.variant_value})`} {l.is_primary && "★"}
                        </span>
                        <span>Qty: {l.default_quantity}</span>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: "#afafaf" }}>No default product lines configured.</div>
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    onClick={() => {
                      setSelectedTemplateForQuote(template);
                      setIsCreateQuoteFromTemplateModalOpen(true);
                    }}
                    className="btn-yellow"
                    style={{ flex: 1, padding: "6px 12px", fontSize: "12px", justifyContent: "center" }}
                  >
                    <FileText size={13} />
                    Create Quote
                  </button>
                  <button
                    onClick={() => handleDuplicateTemplate(template)}
                    className="btn-secondary"
                    style={{ padding: "6px 12px", fontSize: "12px" }}
                    title="Deep clone template and its lines"
                  >
                    <Copy size={13} />
                    Duplicate
                  </button>
                  {template.status === "active" && (
                    <button
                      onClick={() => handleArchiveTemplate(template.id)}
                      className="btn-secondary"
                      style={{ padding: "6px 10px", fontSize: "12px" }}
                      title="Archive template"
                    >
                      <Archive size={13} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: QUOTATIONS WORKFLOW                                                */}
      {/* ========================================================================= */}
      {!loading && activeTab === "quotations" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            {/* Filter Pills */}
            <div style={{ display: "flex", gap: "6px", background: "#1a1a1a", padding: "3px", borderRadius: "6px", border: "1px solid #333333" }}>
              {["all", "draft", "sent", "reviewed", "confirmed", "expired"].map((st) => (
                <button
                  key={st}
                  onClick={() => setQuotationStatusFilter(st)}
                  style={{
                    background: quotationStatusFilter === st ? "#fff313" : "transparent",
                    color: quotationStatusFilter === st ? "#000000" : "#afafaf",
                    border: "none",
                    borderRadius: "4px",
                    padding: "5px 12px",
                    fontSize: "12px",
                    fontWeight: 600,
                    cursor: "pointer",
                    textTransform: "capitalize",
                  }}
                >
                  {st}
                </button>
              ))}
            </div>

            <button onClick={() => setIsNewQuoteModalOpen(true)} className="btn-yellow">
              <Plus size={15} />
              New Quotation
            </button>
          </div>

          <div style={{ display: "grid", gap: "14px" }}>
            {filteredQuotes.map((q) => {
              const statusBadges: Record<string, string> = {
                draft: "badge-paused",
                sent: "badge-partial",
                reviewed: "badge-partial",
                confirmed: "badge-active",
                expired: "badge-unpaid",
                cancelled: "badge-paused",
              };
              return (
                <div key={q.id} className="card-carbon">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span style={{ fontSize: "18px", fontWeight: 700, color: "#fff313", letterSpacing: "-0.5px" }}>
                          {q.quotation_number}
                        </span>
                        <span className={`badge ${statusBadges[q.status] || "badge-paused"}`}>
                          {q.status}
                        </span>
                        {q.is_expired && q.status !== "confirmed" && (
                          <span className="badge badge-unpaid" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                            <AlertTriangle size={11} /> Expired on {q.expiry_date}
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: "13px", color: "#eeeeee", marginTop: "4px" }}>
                        Customer ID: <strong>{q.customer_id}</strong> • Plan: <strong>{q.plan_name}</strong>
                      </div>
                      <div style={{ fontSize: "12px", color: "#afafaf", marginTop: "2px" }}>
                        Issued: {q.issue_date} • Valid Until: {q.expiry_date} • Terms: {q.payment_terms || "Immediate"}
                      </div>
                    </div>

                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontSize: "22px", fontWeight: 700, color: "#eeeeee" }}>
                        ₹{q.total_amount}
                      </div>
                      <div style={{ fontSize: "11px", color: "#afafaf" }}>
                        {q.lines.length} billable line{q.lines.length !== 1 ? "s" : ""}
                      </div>
                    </div>
                  </div>

                  {/* Lines snapshot */}
                  <div style={{ background: "#1f1f1f", padding: "8px 12px", borderRadius: "6px", margin: "10px 0", fontSize: "12px" }}>
                    {q.lines.map((l) => (
                      <div key={l.id} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", color: "#eeeeee" }}>
                        <span>
                          {l.description} {l.is_primary && <span style={{ color: "#fff313" }}>★ Primary</span>}
                        </span>
                        <span style={{ color: "#afafaf" }}>
                          {l.quantity} × ₹{l.unit_price} = <strong style={{ color: "#eeeeee" }}>₹{l.line_total}</strong>
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Workflow Action Buttons */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid #3d3d3d", paddingTop: "10px", marginTop: "10px" }}>
                    <div style={{ fontSize: "12px", color: "#afafaf" }}>
                      {q.confirmed_by ? `Confirmed by ${q.confirmed_by} on ${q.confirmed_at?.slice(0, 10)}` : "Awaiting confirmation"}
                    </div>

                    <div style={{ display: "flex", gap: "8px" }}>
                      {q.status === "draft" && (
                        <button onClick={() => handleSendQuote(q.id)} className="btn-secondary" style={{ padding: "5px 10px", fontSize: "12px" }}>
                          <Send size={13} /> Send
                        </button>
                      )}
                      {(q.status === "draft" || q.status === "sent") && (
                        <button onClick={() => handleReviewQuote(q.id)} className="btn-secondary" style={{ padding: "5px 10px", fontSize: "12px" }}>
                          <CheckCircle2 size={13} /> Mark Reviewed
                        </button>
                      )}
                      {q.status !== "confirmed" && q.status !== "cancelled" && (
                        <button
                          onClick={() => handleConfirmQuote(q)}
                          className="btn-yellow"
                          style={{ padding: "5px 12px", fontSize: "12px" }}
                          disabled={q.is_expired}
                          title={q.is_expired ? "Cannot confirm expired quote. Extend validity first." : "Confirm quotation terms"}
                        >
                          <CheckCircle2 size={13} /> Confirm Quote
                        </button>
                      )}
                      {q.is_expired && q.status !== "confirmed" && (
                        <button
                          onClick={() => {
                            setSelectedQuoteForExtend(q);
                            setIsExtendQuoteModalOpen(true);
                          }}
                          className="btn-secondary"
                          style={{ padding: "5px 10px", fontSize: "12px", borderColor: "#fff313", color: "#fff313" }}
                        >
                          <Clock size={13} /> Extend Validity
                        </button>
                      )}
                      {q.status === "confirmed" && (
                        <button
                          onClick={() => {
                            setSelectedQuoteForConvert(q);
                            setIsConvertQuoteModalOpen(true);
                          }}
                          className="btn-yellow"
                          style={{ padding: "5px 14px", fontSize: "12px" }}
                        >
                          <Repeat size={13} /> Convert to Subscription
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: SUBSCRIPTIONS LIFECYCLE                                            */}
      {/* ========================================================================= */}
      {!loading && activeTab === "subscriptions" && (
        <div>
          {/* Subscriptions Metric Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px", marginBottom: "20px" }}>
            <div className="card-carbon">
              <div style={{ fontSize: "12px", color: "#afafaf", textTransform: "uppercase" }}>Total Subscriptions</div>
              <div style={{ fontSize: "28px", fontWeight: 300, color: "#eeeeee", marginTop: "4px" }}>
                {subscriptions.length}
              </div>
            </div>
            <div className="card-carbon">
              <div style={{ fontSize: "12px", color: "#00e676", textTransform: "uppercase" }}>Active (Running)</div>
              <div style={{ fontSize: "28px", fontWeight: 300, color: "#00e676", marginTop: "4px" }}>
                {subscriptions.filter((s) => s.status === "active" && s.operational_status === "running").length}
              </div>
            </div>
            <div className="card-carbon">
              <div style={{ fontSize: "12px", color: "#afafaf", textTransform: "uppercase" }}>Operational Pauses</div>
              <div style={{ fontSize: "28px", fontWeight: 300, color: "#afafaf", marginTop: "4px" }}>
                {subscriptions.filter((s) => s.operational_status === "paused").length}
              </div>
            </div>
            <div className="card-carbon" style={{ borderColor: subscriptions.some((s) => s.action_required) ? "#ff4d4d" : "#333333" }}>
              <div style={{ fontSize: "12px", color: "#ff4d4d", textTransform: "uppercase" }}>Action Required (Expired)</div>
              <div style={{ fontSize: "28px", fontWeight: 300, color: "#ff4d4d", marginTop: "4px" }}>
                {subscriptions.filter((s) => s.action_required).length}
              </div>
            </div>
          </div>

          {/* Filter Pills */}
          <div style={{ display: "flex", gap: "6px", background: "#1a1a1a", padding: "3px", borderRadius: "6px", border: "1px solid #333333", marginBottom: "20px" }}>
            {(["all", "active", "paused", "closed", "action_required"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setSubscriptionFilter(f)}
                style={{
                  background: subscriptionFilter === f ? "#fff313" : "transparent",
                  color: subscriptionFilter === f ? "#000000" : "#afafaf",
                  border: "none",
                  borderRadius: "4px",
                  padding: "5px 12px",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                  textTransform: "capitalize",
                }}
              >
                {f.replace("_", " ")}
              </button>
            ))}
          </div>

          <div style={{ display: "grid", gap: "16px" }}>
            {filteredSubs.map((sub) => (
              <div key={sub.id} className="card-carbon" style={{ borderLeft: sub.action_required ? "3px solid #ff4d4d" : undefined }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ fontSize: "18px", fontWeight: 700, color: "#fff313" }}>
                        {sub.subscription_number}
                      </span>
                      <span className={`badge ${sub.status === "active" ? "badge-active" : sub.status === "paused" ? "badge-paused" : "badge-unpaid"}`}>
                        {sub.status} • {sub.operational_status}
                      </span>
                      {sub.action_required && (
                        <span className="badge badge-unpaid" style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                          <ShieldAlert size={12} /> Action Required: Expired (Billing Halted)
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: "13px", color: "#eeeeee", marginTop: "4px" }}>
                      Customer ID: <strong>{sub.customer_id}</strong> • Plan: <strong>{sub.plan_name}</strong> ({sub.billing_interval})
                    </div>
                    <div style={{ fontSize: "12px", color: "#afafaf", marginTop: "2px" }}>
                      Start: {sub.start_date} • Next Billing: {sub.next_billing_date || "N/A"} • Expiry: {sub.expiry_date || "Indefinite"} • Terms: {sub.payment_terms}
                    </div>
                  </div>

                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "22px", fontWeight: 700, color: "#eeeeee" }}>
                      ₹{sub.total_recurring_amount}
                    </div>
                    <div style={{ fontSize: "11px", color: "#afafaf" }}>
                      Per {sub.billing_interval}
                    </div>
                  </div>
                </div>

                {/* Status Messages */}
                {sub.pause_reason && (
                  <div style={{ background: "rgba(175, 175, 175, 0.1)", border: "1px solid #4b4b4b", padding: "8px", borderRadius: "4px", fontSize: "12px", color: "#afafaf", marginBottom: "10px" }}>
                    Operational Pause on {sub.pause_date}: "{sub.pause_reason}"
                  </div>
                )}
                {sub.closure_reason && (
                  <div style={{ background: "rgba(255, 77, 77, 0.1)", border: "1px solid #ff4d4d", padding: "8px", borderRadius: "4px", fontSize: "12px", color: "#ff4d4d", marginBottom: "10px" }}>
                    Closed on {sub.closure_date}: "{sub.closure_reason}"
                  </div>
                )}
                {sub.action_required_reason && (
                  <div style={{ background: "rgba(255, 77, 77, 0.15)", border: "1px solid #ff4d4d", padding: "8px", borderRadius: "4px", fontSize: "12px", color: "#ff4d4d", marginBottom: "10px" }}>
                    {sub.action_required_reason}
                  </div>
                )}

                {/* Successor & Predecessor links */}
                {(sub.predecessor_number || sub.successor_number) && (
                  <div style={{ fontSize: "11px", color: "#afafaf", marginBottom: "10px" }}>
                    {sub.predecessor_number && <span>Renewed from: <strong>{sub.predecessor_number}</strong> </span>}
                    {sub.successor_number && <span>Renewed into: <strong style={{ color: "#fff313" }}>{sub.successor_number}</strong> </span>}
                  </div>
                )}

                {/* Lines breakdown */}
                <div style={{ background: "#1f1f1f", padding: "8px 12px", borderRadius: "6px", margin: "10px 0", fontSize: "12px" }}>
                  {sub.lines.map((l) => (
                    <div key={l.id} style={{ display: "flex", justifyContent: "space-between", padding: "3px 0", color: "#eeeeee" }}>
                      <span>
                        {l.description} {l.is_primary && <span style={{ color: "#fff313" }}>★ Primary</span>}
                      </span>
                      <span style={{ color: "#afafaf" }}>
                        {l.quantity} × ₹{l.unit_price} = <strong style={{ color: "#eeeeee" }}>₹{l.line_total}</strong>
                      </span>
                    </div>
                  ))}
                </div>

                {/* Subscription Actions */}
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", borderTop: "1px solid #3d3d3d", paddingTop: "10px" }}>
                  {sub.status === "active" && sub.operational_status === "running" && (
                    <button
                      onClick={() => {
                        setSelectedSub(sub);
                        setIsPauseSubModalOpen(true);
                      }}
                      className="btn-secondary"
                      style={{ padding: "5px 12px", fontSize: "12px" }}
                    >
                      <Pause size={13} /> Pause
                    </button>
                  )}
                  {sub.status === "active" && sub.operational_status === "paused" && (
                    <button
                      onClick={() => handleResumeSub(sub)}
                      className="btn-secondary"
                      style={{ padding: "5px 12px", fontSize: "12px", color: "#00e676", borderColor: "#00e676" }}
                    >
                      <Play size={13} /> Resume
                    </button>
                  )}
                  {sub.status === "active" && (
                    <button
                      onClick={() => {
                        setSelectedSub(sub);
                        setIsRenewSubModalOpen(true);
                      }}
                      className="btn-yellow"
                      style={{ padding: "5px 12px", fontSize: "12px" }}
                    >
                      <Repeat size={13} /> Renew
                    </button>
                  )}
                  {sub.status !== "closed" && (
                    <button
                      onClick={() => {
                        setSelectedSub(sub);
                        setIsCloseSubModalOpen(true);
                      }}
                      className="btn-secondary"
                      style={{ padding: "5px 12px", fontSize: "12px", color: "#ff4d4d" }}
                    >
                      <XCircle size={13} /> Close
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: PRD §7.4 PRICING SIMULATOR                                         */}
      {/* ========================================================================= */}
      {isPricingCalcOpen && (
        <div className="modal-overlay" onClick={() => setIsPricingCalcOpen(false)}>
          <div className="modal-content" style={{ maxWidth: "680px" }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "20px", fontWeight: 600, color: "#fff313", marginBottom: "8px", display: "flex", alignItems: "center", gap: "8px" }}>
              <Calculator size={20} />
              PRD §7.4 Pricing Simulator
            </h2>
            <p style={{ color: "#afafaf", fontSize: "13px", marginBottom: "16px" }}>
              Live verification of the commercial rule: Plan per-unit price replaces the primary product base price before variant adjustments; add-ons use product catalog prices; plan fee is never added separately.
            </p>

            <div style={{ marginBottom: "14px" }}>
              <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Select Plan</label>
              <select
                style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }}
                onChange={(e) => {
                  const p = plans.find((x) => x.id === e.target.value) || null;
                  setCalcSelectedPlan(p);
                  setCalcResult(null);
                }}
              >
                <option value="">-- Choose a Subscription Plan --</option>
                {plans.map((pl) => (
                  <option key={pl.id} value={pl.id}>
                    {pl.name} ({pl.billing_interval}) - Min Qty: {pl.min_quantity}
                  </option>
                ))}
              </select>
            </div>

            {/* Line items selector */}
            <div style={{ marginBottom: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "#eeeeee" }}>Proposed Lines:</span>
                <button
                  type="button"
                  onClick={() => {
                    if (products.length > 0) {
                      setCalcLines([
                        ...calcLines,
                        { product_id: products[0].id, variant_id: null, quantity: 1, is_primary: calcLines.length === 0 },
                      ]);
                    }
                  }}
                  className="btn-secondary"
                  style={{ padding: "4px 8px", fontSize: "11px" }}
                >
                  <Plus size={12} /> Add Line
                </button>
              </div>

              {calcLines.map((line, idx) => {
                const prod = products.find((p) => p.id === line.product_id);
                return (
                  <div key={idx} style={{ display: "flex", gap: "8px", marginBottom: "8px", alignItems: "center" }}>
                    <select
                      value={line.product_id}
                      onChange={(e) => {
                        const updated = [...calcLines];
                        updated[idx].product_id = e.target.value;
                        updated[idx].variant_id = null;
                        setCalcLines(updated);
                      }}
                      style={{ flex: 2, padding: "6px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "4px", fontSize: "12px" }}
                    >
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} (Base: ₹{p.sales_price})
                        </option>
                      ))}
                    </select>

                    {prod && prod.variants && prod.variants.length > 0 && (
                      <select
                        value={line.variant_id || ""}
                        onChange={(e) => {
                          const updated = [...calcLines];
                          updated[idx].variant_id = e.target.value || null;
                          setCalcLines(updated);
                        }}
                        style={{ flex: 2, padding: "6px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "4px", fontSize: "12px" }}
                      >
                        <option value="">No Variant (+₹0.00)</option>
                        {prod.variants.map((v) => (
                          <option key={v.id} value={v.id}>
                            {v.attribute_name}: {v.value} (+₹{v.price_adjustment})
                          </option>
                        ))}
                      </select>
                    )}

                    <input
                      type="number"
                      min="1"
                      value={line.quantity}
                      onChange={(e) => {
                        const updated = [...calcLines];
                        updated[idx].quantity = parseInt(e.target.value) || 1;
                        setCalcLines(updated);
                      }}
                      style={{ width: "60px", padding: "6px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "4px", fontSize: "12px" }}
                    />

                    <label style={{ fontSize: "11px", color: "#afafaf", display: "flex", alignItems: "center", gap: "4px" }}>
                      <input
                        type="checkbox"
                        checked={line.is_primary}
                        onChange={(e) => {
                          const updated = [...calcLines];
                          updated[idx].is_primary = e.target.checked;
                          setCalcLines(updated);
                        }}
                      />
                      Primary
                    </label>

                    <button
                      type="button"
                      onClick={() => setCalcLines(calcLines.filter((_, i) => i !== idx))}
                      style={{ background: "none", border: "none", color: "#ff4d4d", cursor: "pointer" }}
                    >
                      <XCircle size={14} />
                    </button>
                  </div>
                );
              })}
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px" }}>
              <button onClick={handleCalculatePricing} className="btn-yellow" style={{ width: "100%", justifyContent: "center" }}>
                Calculate Live Recurring Breakdown
              </button>
            </div>

            {/* Live Calculation Output */}
            {calcResult && (
              <div style={{ background: "#111111", border: "1px solid #fff313", borderRadius: "6px", padding: "14px", fontSize: "13px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <span style={{ color: "#afafaf" }}>Plan Minimum Quantity Met:</span>
                  <span style={{ color: calcResult.min_quantity_met ? "#00e676" : "#ff4d4d", fontWeight: 700 }}>
                    {calcResult.min_quantity_met ? "PASSED" : "FAILED (Below Min)"}
                  </span>
                </div>
                {calcResult.min_quantity_error && (
                  <div style={{ color: "#ff4d4d", fontSize: "12px", marginBottom: "8px" }}>
                    {calcResult.min_quantity_error}
                  </div>
                )}

                <div style={{ borderTop: "1px solid #333333", paddingTop: "8px", marginTop: "8px" }}>
                  {calcResult.lines.map((l) => (
                    <div key={l.line_number} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
                      <span>
                        {l.product_name} {l.variant_name && `(${l.variant_name})`} [{l.base_price_source}]
                      </span>
                      <span>
                        {l.quantity} × ₹{l.unit_price} = <strong>₹{l.line_subtotal}</strong>
                      </span>
                    </div>
                  ))}
                </div>

                <div style={{ borderTop: "1px solid #fff313", paddingTop: "8px", marginTop: "8px", display: "flex", justifyContent: "space-between", fontSize: "16px" }}>
                  <span style={{ color: "#fff313", fontWeight: 700 }}>Recurring Subtotal:</span>
                  <span style={{ color: "#fff313", fontWeight: 800 }}>₹{calcResult.recurring_subtotal}</span>
                </div>
                <div style={{ fontSize: "11px", color: "#afafaf", marginTop: "6px" }}>
                  Policy check: {calcResult.pricing_policy.rule}
                </div>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
              <button onClick={() => setIsPricingCalcOpen(false)} className="btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: NEW PRODUCT                                                       */}
      {/* ========================================================================= */}
      {isNewProductModalOpen && (
        <div className="modal-overlay" onClick={() => setIsNewProductModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginBottom: "16px" }}>Add Catalog Product</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const form = e.target as HTMLFormElement;
                const data = {
                  name: (form.elements.namedItem("name") as HTMLInputElement).value,
                  type: (form.elements.namedItem("type") as HTMLInputElement).value,
                  sales_price: (form.elements.namedItem("sales_price") as HTMLInputElement).value,
                  cost_price: (form.elements.namedItem("cost_price") as HTMLInputElement).value,
                  notes: (form.elements.namedItem("notes") as HTMLTextAreaElement).value,
                };
                try {
                  await api.commercial.createProduct(data);
                  showMsg("Product created successfully.");
                  setIsNewProductModalOpen(false);
                  loadData();
                } catch (err: any) {
                  showMsg(err.message || "Failed to create product", "error");
                }
              }}
            >
              <div style={{ display: "grid", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Product Name *</label>
                  <input required name="name" style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }} />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Category / Type</label>
                  <input name="type" placeholder="e.g. Software, Hardware, Service" style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Sales Price (₹) *</label>
                    <input required type="number" step="0.01" min="0" name="sales_price" style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }} />
                  </div>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Internal Cost Price (₹) *</label>
                    <input required type="number" step="0.01" min="0" name="cost_price" style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }} />
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Internal Notes</label>
                  <textarea name="notes" rows={2} style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }} />
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "20px" }}>
                <button type="button" onClick={() => setIsNewProductModalOpen(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-yellow">Save Product</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: NEW VARIANT                                                       */}
      {/* ========================================================================= */}
      {isNewVariantModalOpen && selectedProductForVariant && (
        <div className="modal-overlay" onClick={() => setIsNewVariantModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginBottom: "8px" }}>
              Add Variant to {selectedProductForVariant.name}
            </h2>
            <p style={{ color: "#afafaf", fontSize: "12px", marginBottom: "16px" }}>
              Variant adjustments are added to the product's effective sales price (can be positive or negative).
            </p>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const form = e.target as HTMLFormElement;
                const data = {
                  product: selectedProductForVariant.id,
                  attribute_name: (form.elements.namedItem("attribute_name") as HTMLInputElement).value,
                  value: (form.elements.namedItem("value") as HTMLInputElement).value,
                  price_adjustment: (form.elements.namedItem("price_adjustment") as HTMLInputElement).value,
                };
                try {
                  await api.commercial.createVariant(data);
                  showMsg("Variant added successfully.");
                  setIsNewVariantModalOpen(false);
                  loadData();
                } catch (err: any) {
                  showMsg(err.message || "Failed to add variant", "error");
                }
              }}
            >
              <div style={{ display: "grid", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Attribute Name *</label>
                  <input required name="attribute_name" placeholder="e.g. Brand, Tier, Region" style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }} />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Attribute Value *</label>
                  <input required name="value" placeholder="e.g. Odoo, Enterprise, US-East" style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }} />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Price Adjustment (₹) *</label>
                  <input required type="number" step="0.01" name="price_adjustment" placeholder="e.g. 560.00" style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }} />
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "20px" }}>
                <button type="button" onClick={() => setIsNewVariantModalOpen(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-yellow">Add Variant</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: EXTEND QUOTATION                                                  */}
      {/* ========================================================================= */}
      {isExtendQuoteModalOpen && selectedQuoteForExtend && (
        <div className="modal-overlay" onClick={() => setIsExtendQuoteModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#fff313", marginBottom: "8px" }}>
              Extend Validity: {selectedQuoteForExtend.quotation_number}
            </h2>
            <p style={{ color: "#afafaf", fontSize: "13px", marginBottom: "16px" }}>
              Extends the validity period of this quotation, resetting any expired condition to allow authorized confirmation.
            </p>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Additional Validity Days</label>
              <input
                type="number"
                min="1"
                value={extendDays}
                onChange={(e) => setExtendDays(parseInt(e.target.value) || 30)}
                style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }}
              />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button onClick={() => setIsExtendQuoteModalOpen(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleExtendQuote} className="btn-yellow">Confirm Extension</button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: CONVERT TO SUBSCRIPTION                                            */}
      {/* ========================================================================= */}
      {isConvertQuoteModalOpen && selectedQuoteForConvert && (
        <div className="modal-overlay" onClick={() => setIsConvertQuoteModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#00e676", marginBottom: "8px" }}>
              Activate Subscription from {selectedQuoteForConvert.quotation_number}
            </h2>
            <p style={{ color: "#afafaf", fontSize: "13px", marginBottom: "16px" }}>
              Converts confirmed commercial quote into a live recurring subscription. Freezes commercial lines and sets initial billing anchor.
            </p>
            <div style={{ background: "#262626", padding: "12px", borderRadius: "6px", marginBottom: "16px", fontSize: "13px" }}>
              <div>Customer: <strong>{selectedQuoteForConvert.customer_id}</strong></div>
              <div>Plan: <strong>{selectedQuoteForConvert.plan_name}</strong></div>
              <div>Recurring Subtotal: <strong style={{ color: "#fff313" }}>₹{selectedQuoteForConvert.total_amount}</strong></div>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button onClick={() => setIsConvertQuoteModalOpen(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleConvertQuote} className="btn-yellow">Activate Subscription</button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: PAUSE SUBSCRIPTION                                                */}
      {/* ========================================================================= */}
      {isPauseSubModalOpen && selectedSub && (
        <div className="modal-overlay" onClick={() => setIsPauseSubModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginBottom: "8px" }}>
              Pause Subscription: {selectedSub.subscription_number}
            </h2>
            <p style={{ color: "#afafaf", fontSize: "13px", marginBottom: "16px" }}>
              Enforces plan pause policy. Paused subscriptions generate zero recurring billing runs while paused.
            </p>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Operational Pause Reason *</label>
              <textarea
                required
                rows={3}
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="e.g. Customer site maintenance outage"
                style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }}
              />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button onClick={() => setIsPauseSubModalOpen(false)} className="btn-secondary">Cancel</button>
              <button onClick={handlePauseSub} className="btn-yellow">Confirm Pause</button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: CLOSE SUBSCRIPTION                                                */}
      {/* ========================================================================= */}
      {isCloseSubModalOpen && selectedSub && (
        <div className="modal-overlay" onClick={() => setIsCloseSubModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#ff4d4d", marginBottom: "8px" }}>
              Close Subscription: {selectedSub.subscription_number}
            </h2>
            <p style={{ color: "#afafaf", fontSize: "13px", marginBottom: "16px" }}>
              Closed subscriptions will never generate any new recurring billing periods. Already-issued invoices remain payable.
            </p>
            <div style={{ marginBottom: "14px" }}>
              <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "4px" }}>Closure Reason</label>
              <textarea
                rows={3}
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="e.g. Term expired or agreed early cancellation"
                style={{ width: "100%", padding: "8px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "6px" }}
              />
            </div>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ fontSize: "12px", color: "#afafaf", display: "flex", alignItems: "center", gap: "6px" }}>
                <input
                  type="checkbox"
                  checked={earlyCloseForce}
                  onChange={(e) => setEarlyCloseForce(e.target.checked)}
                />
                Force Early Closure (Waiver override)
              </label>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button onClick={() => setIsCloseSubModalOpen(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleCloseSub} style={{ background: "#ff4d4d", color: "#000000", border: "none", borderRadius: "6px", padding: "8px 16px", fontWeight: 700, cursor: "pointer" }}>
                Close Subscription
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: RENEW SUBSCRIPTION                                                 */}
      {/* ========================================================================= */}
      {isRenewSubModalOpen && selectedSub && (
        <div className="modal-overlay" onClick={() => setIsRenewSubModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#fff313", marginBottom: "8px" }}>
              Renew Subscription: {selectedSub.subscription_number}
            </h2>
            <p style={{ color: "#afafaf", fontSize: "13px", marginBottom: "16px" }}>
              Creates a linked successor subscription with a new sequential identifier, copies commercial snapshot lines, and marks the predecessor subscription as closed.
            </p>
            <div style={{ background: "#262626", padding: "12px", borderRadius: "6px", marginBottom: "16px", fontSize: "13px" }}>
              <div>Customer: <strong>{selectedSub.customer_id}</strong></div>
              <div>Plan: <strong>{selectedSub.plan_name}</strong></div>
              <div>Recurring Amount: <strong>₹{selectedSub.total_recurring_amount}</strong></div>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button onClick={() => setIsRenewSubModalOpen(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleRenewSub} className="btn-yellow">Execute Renewal</button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: NEW SUBSCRIPTION PLAN                                              */}
      {/* ========================================================================= */}
      {isNewPlanModalOpen && (
        <div className="modal-overlay" onClick={() => setIsNewPlanModalOpen(false)}>
          <div className="modal-content" style={{ maxWidth: "600px" }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginBottom: "14px" }}>Create Subscription Plan</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const form = e.target as HTMLFormElement;
                const data: any = {
                  name: (form.elements.namedItem("name") as HTMLInputElement).value,
                  billing_interval: (form.elements.namedItem("billing_interval") as HTMLSelectElement).value,
                  min_quantity: parseInt((form.elements.namedItem("min_quantity") as HTMLInputElement).value) || 1,
                  default_payment_terms: (form.elements.namedItem("default_payment_terms") as HTMLInputElement).value,
                  allow_pause: (form.elements.namedItem("allow_pause") as HTMLInputElement).checked,
                  allow_renewal: (form.elements.namedItem("allow_renewal") as HTMLInputElement).checked,
                  allow_early_closure: (form.elements.namedItem("allow_early_closure") as HTMLInputElement).checked,
                  auto_close_at_expiry: (form.elements.namedItem("auto_close_at_expiry") as HTMLInputElement).checked,
                };
                const primaryProd = (form.elements.namedItem("primary_product") as HTMLSelectElement).value;
                if (primaryProd) data.primary_product = primaryProd;
                const primaryPrice = (form.elements.namedItem("default_primary_unit_price") as HTMLInputElement).value;
                if (primaryPrice) data.default_primary_unit_price = primaryPrice;

                try {
                  await api.commercial.createPlan(data);
                  showMsg("Subscription Plan created successfully.");
                  setIsNewPlanModalOpen(false);
                  loadData();
                } catch (err: any) {
                  showMsg(err.message || "Failed to create plan", "error");
                }
              }}
            >
              <div style={{ display: "grid", gap: "10px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Plan Name *</label>
                  <input required name="name" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Billing Interval *</label>
                    <select name="billing_interval" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }}>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="yearly">Yearly</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Min Quantity *</label>
                    <input required type="number" min="1" defaultValue="1" name="min_quantity" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Designated Primary Product</label>
                    <select name="primary_product" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }}>
                      <option value="">-- None --</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Primary Unit Price Override (₹)</label>
                    <input type="number" step="0.01" min="0" name="default_primary_unit_price" placeholder="PRD §7.4 override" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Default Payment Terms</label>
                  <input defaultValue="Immediate" name="default_payment_terms" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "12px", color: "#eeeeee", marginTop: "4px" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <input type="checkbox" name="allow_pause" /> Allow Pause
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <input type="checkbox" name="allow_renewal" defaultChecked /> Allow Renewal
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <input type="checkbox" name="allow_early_closure" /> Allow Early Closure
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <input type="checkbox" name="auto_close_at_expiry" defaultChecked /> Auto-Close at Expiry
                  </label>
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "16px" }}>
                <button type="button" onClick={() => setIsNewPlanModalOpen(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-yellow">Save Plan</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: NEW QUOTATION TEMPLATE                                            */}
      {/* ========================================================================= */}
      {isNewTemplateModalOpen && (
        <div className="modal-overlay" onClick={() => setIsNewTemplateModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginBottom: "14px" }}>New Quotation Template</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const form = e.target as HTMLFormElement;
                const data: any = {
                  name: (form.elements.namedItem("name") as HTMLInputElement).value,
                  plan: (form.elements.namedItem("plan") as HTMLSelectElement).value,
                  validity_days: parseInt((form.elements.namedItem("validity_days") as HTMLInputElement).value) || 30,
                  notes: (form.elements.namedItem("notes") as HTMLTextAreaElement).value,
                  lines: [],
                };
                const prodId = (form.elements.namedItem("product") as HTMLSelectElement).value;
                if (prodId) {
                  data.lines.push({
                    product: prodId,
                    default_quantity: 1,
                    is_primary: true,
                    sort_order: 1,
                  });
                }
                try {
                  await api.commercial.createTemplate(data);
                  showMsg("Template created successfully.");
                  setIsNewTemplateModalOpen(false);
                  loadData();
                } catch (err: any) {
                  showMsg(err.message || "Failed to create template", "error");
                }
              }}
            >
              <div style={{ display: "grid", gap: "10px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Template Name *</label>
                  <input required name="name" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Governing Plan *</label>
                  <select required name="plan" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }}>
                    {plans.map((p) => (
                      <option key={p.id} value={p.id}>{p.name} ({p.billing_interval})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Validity Duration (Days) *</label>
                  <input required type="number" min="1" defaultValue="30" name="validity_days" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Primary Product Line</label>
                  <select name="product" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }}>
                    <option value="">-- Select Product --</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>{p.name} (₹{p.sales_price})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Internal Notes</label>
                  <textarea name="notes" rows={2} style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "16px" }}>
                <button type="button" onClick={() => setIsNewTemplateModalOpen(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-yellow">Create Template</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: CREATE QUOTE FROM TEMPLATE                                        */}
      {/* ========================================================================= */}
      {isCreateQuoteFromTemplateModalOpen && selectedTemplateForQuote && (
        <div className="modal-overlay" onClick={() => setIsCreateQuoteFromTemplateModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#fff313", marginBottom: "8px" }}>
              Create Quote from {selectedTemplateForQuote.name}
            </h2>
            <p style={{ color: "#afafaf", fontSize: "12px", marginBottom: "14px" }}>
              Copies template product lines, calculates dynamic expiry ({selectedTemplateForQuote.validity_days} days), and freezes commercial prices.
            </p>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const form = e.target as HTMLFormElement;
                const custId = (form.elements.namedItem("customer_id") as HTMLInputElement).value;
                const notes = (form.elements.namedItem("notes") as HTMLTextAreaElement).value;
                try {
                  const q = await api.commercial.createQuotationFromTemplate(selectedTemplateForQuote.id, {
                    customer_id: custId,
                    notes,
                  });
                  showMsg(`Quotation ${q.quotation_number} generated from template.`);
                  setIsCreateQuoteFromTemplateModalOpen(false);
                  setActiveTab("quotations");
                } catch (err: any) {
                  showMsg(err.message || "Failed to generate quotation", "error");
                }
              }}
            >
              <div style={{ display: "grid", gap: "10px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Customer ID or Code *</label>
                  <input required name="customer_id" placeholder="e.g. CUST-ACME-01 or UUID" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Commercial Scope Notes</label>
                  <textarea name="notes" defaultValue={selectedTemplateForQuote.notes || ""} rows={2} style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "16px" }}>
                <button type="button" onClick={() => setIsCreateQuoteFromTemplateModalOpen(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-yellow">Generate Quote</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: NEW CUSTOM QUOTATION FROM SCRATCH                                  */}
      {/* ========================================================================= */}
      {isNewQuoteModalOpen && (
        <div className="modal-overlay" onClick={() => setIsNewQuoteModalOpen(false)}>
          <div className="modal-content" style={{ maxWidth: "620px" }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#eeeeee", marginBottom: "14px" }}>Create Custom Quotation</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const form = e.target as HTMLFormElement;
                const custId = (form.elements.namedItem("customer_id") as HTMLInputElement).value;
                const planId = (form.elements.namedItem("plan") as HTMLSelectElement).value;
                const validityDays = parseInt((form.elements.namedItem("validity_days") as HTMLInputElement).value) || 30;
                const prodId = (form.elements.namedItem("product") as HTMLSelectElement).value;
                const qty = parseInt((form.elements.namedItem("quantity") as HTMLInputElement).value) || 1;
                const varId = (form.elements.namedItem("variant") as HTMLSelectElement)?.value || null;

                const payload = {
                  customer_id: custId,
                  plan: planId,
                  validity_days: validityDays,
                  lines: [
                    {
                      product: prodId,
                      variant: varId || undefined,
                      quantity: qty,
                      is_primary: true,
                    },
                  ],
                };

                try {
                  const q = await api.commercial.createQuotation(payload);
                  showMsg(`Quotation ${q.quotation_number} created.`);
                  setIsNewQuoteModalOpen(false);
                  loadData();
                } catch (err: any) {
                  showMsg(err.message || "Failed to create quote. Check minimum quantity requirements.", "error");
                }
              }}
            >
              <div style={{ display: "grid", gap: "10px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Customer ID or Code *</label>
                  <input required name="customer_id" placeholder="e.g. CUST-ACME-01 or UUID" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Subscription Plan *</label>
                    <select required name="plan" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }}>
                      {plans.map((p) => (
                        <option key={p.id} value={p.id}>{p.name} (Min Qty: {p.min_quantity})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Validity Duration (Days) *</label>
                    <input required type="number" min="1" defaultValue="30" name="validity_days" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "10px" }}>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Product *</label>
                    <select required name="product" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }}>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>{p.name} (₹{p.sales_price})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: "12px", color: "#afafaf", display: "block", marginBottom: "3px" }}>Quantity *</label>
                    <input required type="number" min="1" defaultValue="2" name="quantity" style={{ width: "100%", padding: "7px", background: "#262626", border: "1px solid #4b4b4b", color: "#eeeeee", borderRadius: "5px" }} />
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "16px" }}>
                <button type="button" onClick={() => setIsNewQuoteModalOpen(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-yellow">Create Quotation</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: TEAMMATE 3 BILLING FEED PREVIEW                                   */}
      {/* ========================================================================= */}
      {isBillingFeedOpen && (
        <div className="modal-overlay" onClick={() => setIsBillingFeedOpen(false)}>
          <div className="modal-content" style={{ maxWidth: "780px" }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <div>
                <h2 style={{ fontSize: "18px", fontWeight: 600, color: "#fff313" }}>
                  Teammate 3 Recurring Billing Feed
                </h2>
                <p style={{ color: "#afafaf", fontSize: "12px" }}>
                  Endpoint: <code style={{ color: "#eeeeee" }}>GET /api/v1/subscriptions/subscriptions/due-for-billing/</code>
                </p>
              </div>
              <span className="badge badge-active">{billingFeedData.length} Due Eligible</span>
            </div>

            <p style={{ color: "#afafaf", fontSize: "12px", marginBottom: "14px" }}>
              Strict exclusion rule: Paused subscriptions, closed subscriptions, and expired action-required subscriptions are guaranteed excluded to prevent duplicate or illegal billing runs.
            </p>

            <div style={{ maxHeight: "360px", overflowY: "auto", background: "#111111", padding: "12px", borderRadius: "6px", border: "1px solid #333333", fontSize: "12px" }}>
              {billingFeedData.length === 0 ? (
                <div style={{ color: "#afafaf", textAlign: "center", padding: "20px" }}>
                  No subscriptions currently due for recurring invoice generation.
                </div>
              ) : (
                billingFeedData.map((b) => (
                  <div key={b.subscription_id} style={{ borderBottom: "1px solid #262626", padding: "8px 0" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", color: "#eeeeee", fontWeight: 600 }}>
                      <span>{b.subscription_number} (Customer: {b.customer_id})</span>
                      <span style={{ color: "#fff313" }}>Next Billing: {b.next_billing_date} ({b.billing_interval})</span>
                    </div>
                    <div style={{ fontSize: "11px", color: "#afafaf", marginTop: "4px" }}>
                      {b.lines.length} billable line{b.lines.length !== 1 ? "s" : ""}: {b.lines.map((l) => `${l.description} (${l.quantity} × ₹${l.unit_price})`).join(", ")}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
              <button onClick={() => setIsBillingFeedOpen(false)} className="btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
