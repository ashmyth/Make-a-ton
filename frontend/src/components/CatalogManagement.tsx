import React, { useState } from "react";
import { Plus, Search, X } from "lucide-react";

interface Variant {
  id: string;
  attribute: string;
  value: string;
  price_adjustment: string;
}

interface Product {
  id: string;
  name: string;
  type: string;
  sales_price: string;
  cost_price: string;
  notes: string;
  status: "ACTIVE" | "ARCHIVED";
  variants: Variant[];
}

export const CatalogManagement: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([
    {
      id: "PROD-001",
      name: "Cloud SaaS Platform Seat",
      type: "Software License",
      sales_price: "1000.00",
      cost_price: "400.00",
      notes: "Base tier license with SSO and 99.9% uptime SLA.",
      status: "ACTIVE",
      variants: [
        { id: "v1", attribute: "Brand", value: "Odoo", price_adjustment: "+560.00" },
        { id: "v2", attribute: "Storage", value: "500GB SSD", price_adjustment: "+120.00" },
      ],
    },
    {
      id: "PROD-002",
      name: "Dedicated High-Throughput Node",
      type: "Infrastructure",
      sales_price: "2400.00",
      cost_price: "1100.00",
      notes: "Dedicated bare-metal instances with isolated VPC peering.",
      status: "ACTIVE",
      variants: [],
    },
    {
      id: "PROD-003",
      name: "Enterprise 24/7 SLA Support",
      type: "Support Service",
      sales_price: "600.00",
      cost_price: "150.00",
      notes: "15-minute response time guarantee with dedicated engineers.",
      status: "ACTIVE",
      variants: [
        { id: "v3", attribute: "Tier", value: "Gold", price_adjustment: "+400.00" },
      ],
    },
  ]);

  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  // Form states
  const [name, setName] = useState("");
  const [type, setType] = useState("Software");
  const [salesPrice, setSalesPrice] = useState("");
  const [costPrice, setCostPrice] = useState("");
  const [notes, setNotes] = useState("");
  const [variants, setVariants] = useState<Variant[]>([]);

  const handleOpenNew = () => {
    setSelectedProduct(null);
    setName("");
    setType("Software");
    setSalesPrice("");
    setCostPrice("");
    setNotes("");
    setVariants([]);
    setIsEditorOpen(true);
  };

  const handleOpenEdit = (p: Product) => {
    setSelectedProduct(p);
    setName(p.name);
    setType(p.type);
    setSalesPrice(p.sales_price);
    setCostPrice(p.cost_price);
    setNotes(p.notes);
    setVariants(p.variants);
    setIsEditorOpen(true);
  };

  const handleAddVariant = () => {
    setVariants([
      ...variants,
      { id: `v-${Date.now()}`, attribute: "Attribute", value: "Value", price_adjustment: "+0.00" },
    ]);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedProduct) {
      setProducts(
        products.map((p) =>
          p.id === selectedProduct.id
            ? { ...p, name, type, sales_price: salesPrice, cost_price: costPrice, notes, variants }
            : p
        )
      );
    } else {
      const newProd: Product = {
        id: `PROD-${String(products.length + 1).padStart(3, "0")}`,
        name,
        type,
        sales_price: salesPrice,
        cost_price: costPrice,
        notes,
        status: "ACTIVE",
        variants,
      };
      setProducts([...products, newProd]);
    }
    setIsEditorOpen(false);
  };

  return (
    <div>
      {/* Header bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
        <div>
          <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
            Catalog & Offerings
          </span>
          <h1 className="font-serif" style={{ fontSize: "36px", margin: "4px 0 0 0" }}>
            Products & Variants
          </h1>
        </div>
        <button onClick={handleOpenNew} className="btn-primary-blue">
          <Plus size={14} />
          <span>New Product</span>
        </button>
      </div>

      {/* Filter and Search */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          marginBottom: "16px",
          alignItems: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            backgroundColor: "#ffffff",
            border: "1px solid var(--color-ash)",
            borderRadius: "9999px",
            padding: "6px 14px",
            flex: 1,
            maxWidth: "360px",
          }}
        >
          <Search size={14} color="var(--color-smoke)" />
          <input
            type="text"
            placeholder="Search products by name or SKU..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              border: "none",
              outline: "none",
              fontSize: "12px",
              fontFamily: "var(--font-mono)",
              width: "100%",
            }}
          />
        </div>
      </div>

      {/* Table List */}
      <div className="monad-card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
          <thead>
            <tr style={{ backgroundColor: "rgba(246, 243, 241, 0.5)", borderBottom: "1px solid var(--color-ash)" }}>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>ID</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>NAME</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>CATEGORY</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>BASE SALES PRICE</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>COST (INTERNAL)</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>VARIANTS</th>
              <th style={{ padding: "12px 16px", color: "var(--color-smoke)", fontWeight: 500 }}>STATUS</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}></th>
            </tr>
          </thead>
          <tbody>
            {products
              .filter((p) => p.name.toLowerCase().includes(searchTerm.toLowerCase()))
              .map((p) => (
                <tr
                  key={p.id}
                  style={{ borderBottom: "1px solid var(--color-ash)", cursor: "pointer" }}
                  onClick={() => handleOpenEdit(p)}
                >
                  <td style={{ padding: "14px 16px", fontWeight: 500 }}>{p.id}</td>
                  <td style={{ padding: "14px 16px", fontWeight: 600 }}>{p.name}</td>
                  <td style={{ padding: "14px 16px", color: "var(--color-graphite)" }}>{p.type}</td>
                  <td style={{ padding: "14px 16px" }}>
                    ${p.sales_price.split(".")[0]}.
                    <span className="money-decimal">{p.sales_price.split(".")[1] || "00"}</span>
                  </td>
                  <td style={{ padding: "14px 16px", color: "var(--color-smoke)" }}>
                    ${p.cost_price.split(".")[0]}.
                    <span className="money-decimal">{p.cost_price.split(".")[1] || "00"}</span>
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    {p.variants.length > 0 ? (
                      <span className="badge-pill badge-neutral">
                        {p.variants.length} variant{p.variants.length > 1 ? "s" : ""}
                      </span>
                    ) : (
                      <span style={{ color: "var(--color-smoke)" }}>None</span>
                    )}
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    <span className={`badge-pill ${p.status === "ACTIVE" ? "badge-active" : "badge-neutral"}`}>
                      {p.status}
                    </span>
                  </td>
                  <td style={{ padding: "14px 16px", textAlign: "right" }}>
                    <button className="btn-ghost" style={{ padding: "4px 12px", fontSize: "11px" }}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Product Drawer / Modal */}
      {isEditorOpen && (
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
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
              <div>
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)" }}>
                  {selectedProduct ? `Edit ${selectedProduct.id}` : "Catalog Definition"}
                </span>
                <h2 className="font-serif" style={{ fontSize: "28px", margin: "4px 0 0 0" }}>
                  {selectedProduct ? "Product Settings" : "New Catalog Item"}
                </h2>
              </div>
              <button
                onClick={() => setIsEditorOpen(false)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-smoke)" }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Product Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Cloud SaaS Platform Seat"
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--color-ash)",
                    fontSize: "13px",
                    fontFamily: "var(--font-mono)",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                    Sales Price ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={salesPrice}
                    onChange={(e) => setSalesPrice(e.target.value)}
                    placeholder="1000.00"
                    style={{
                      width: "100%",
                      padding: "9px 12px",
                      borderRadius: "6px",
                      border: "1px solid var(--color-ash)",
                      fontSize: "13px",
                      fontFamily: "var(--font-mono)",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                    Cost Price ($ Internal)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={costPrice}
                    onChange={(e) => setCostPrice(e.target.value)}
                    placeholder="400.00"
                    style={{
                      width: "100%",
                      padding: "9px 12px",
                      borderRadius: "6px",
                      border: "1px solid var(--color-ash)",
                      fontSize: "13px",
                      fontFamily: "var(--font-mono)",
                      boxSizing: "border-box",
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--color-smoke)", display: "block", marginBottom: "4px" }}>
                  Notes & Description
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Internal notes or invoice line descriptions..."
                  rows={3}
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--color-ash)",
                    fontSize: "12px",
                    fontFamily: "var(--font-mono)",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              {/* Variants Section */}
              <div style={{ marginTop: "12px", borderTop: "1px solid var(--color-ash)", paddingTop: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <span style={{ fontSize: "12px", fontWeight: 600, textTransform: "uppercase" }}>
                    Variant Price Adjustments
                  </span>
                  <button type="button" onClick={handleAddVariant} className="btn-ghost" style={{ padding: "4px 10px", fontSize: "10px" }}>
                    + Add Variant
                  </button>
                </div>

                {variants.map((v, i) => (
                  <div key={v.id} style={{ display: "flex", gap: "8px", marginBottom: "8px", alignItems: "center" }}>
                    <input
                      type="text"
                      placeholder="Attribute (e.g. Brand)"
                      value={v.attribute}
                      onChange={(e) => {
                        const copy = [...variants];
                        copy[i].attribute = e.target.value;
                        setVariants(copy);
                      }}
                      style={{ flex: 1, padding: "6px 8px", fontSize: "11px", borderRadius: "4px", border: "1px solid var(--color-ash)" }}
                    />
                    <input
                      type="text"
                      placeholder="Value (e.g. Odoo)"
                      value={v.value}
                      onChange={(e) => {
                        const copy = [...variants];
                        copy[i].value = e.target.value;
                        setVariants(copy);
                      }}
                      style={{ flex: 1, padding: "6px 8px", fontSize: "11px", borderRadius: "4px", border: "1px solid var(--color-ash)" }}
                    />
                    <input
                      type="text"
                      placeholder="+560.00"
                      value={v.price_adjustment}
                      onChange={(e) => {
                        const copy = [...variants];
                        copy[i].price_adjustment = e.target.value;
                        setVariants(copy);
                      }}
                      style={{ width: "90px", padding: "6px 8px", fontSize: "11px", borderRadius: "4px", border: "1px solid var(--color-ash)" }}
                    />
                    <button
                      type="button"
                      onClick={() => setVariants(variants.filter((_, idx) => idx !== i))}
                      style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-smoke)" }}
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: "24px", display: "flex", gap: "12px" }}>
                <button type="submit" className="btn-primary-blue" style={{ flex: 1, justifyContent: "center" }}>
                  Save Product
                </button>
                <button type="button" onClick={() => setIsEditorOpen(false)} className="btn-ghost" style={{ flex: 1, justifyContent: "center" }}>
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
