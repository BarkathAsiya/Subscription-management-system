import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

const money = (n) => Number(n || 0).toLocaleString("en-IN");
const box = { background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: 16 };
const field = { padding: 8, borderRadius: 8, border: "1px solid #d1d5db", width: "100%", boxSizing: "border-box" };
const PAGE = 20;

export default function Finance() {
  const [summary, setSummary] = useState(null);
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("overdue");
  const [skip, setSkip] = useState(0);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [form, setForm] = useState({ invoice_id: "", method: "cash", amount: "", note: "" });

  async function load() {
    try {
      setError("");
      const q = new URLSearchParams({ skip, limit: PAGE });
      if (status) q.set("status", status);
      const [s, inv] = await Promise.all([api("/reports/summary"), api(`/reports/invoices?${q}`)]);
      setSummary(s);
      setRows(inv.items);
      setTotal(inv.total);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, [status, skip]);

  async function pay(e) {
    e.preventDefault();
    setMsg("");
    setError("");
    try {
      await api("/payments", {
        method: "POST",
        body: JSON.stringify({
          invoice_id: Number(form.invoice_id),
          method: form.method,
          amount: Number(form.amount),
          note: form.note || null,
        }),
      });
      setMsg("Payment recorded.");
      setForm({ ...form, invoice_id: "", amount: "", note: "" });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  const cards = summary ? [
    ["Active subscriptions", summary.active_subscriptions],
    ["Revenue collected", money(summary.revenue_collected)],
    ["Amount owed", money(summary.amount_owed)],
    ["Outstanding invoices", summary.outstanding_invoices],
    ["Overdue invoices", summary.overdue_invoices],
    ["Overdue amount", money(summary.overdue_amount)],
  ] : [];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: 20, fontFamily: "system-ui, sans-serif" }}>
      <Link to="/dashboard">← Back to dashboard</Link>
      <h1>Finance dashboard</h1>
      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 12 }}>
        {cards.map(([label, value]) => (
          <div key={label} style={box}>
            <div style={{ color: "#6b7280", fontSize: 13 }}>{label}</div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ ...box, marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>Record a payment</h2>
        <form onSubmit={pay} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10 }}>
          <input style={field} type="number" placeholder="Invoice ID" required value={form.invoice_id}
            onChange={(e) => setForm({ ...form, invoice_id: e.target.value })} />
          <select style={field} value={form.method} onChange={(e) => setForm({ ...form, method: e.target.value })}>
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="bank_transfer">Bank transfer</option>
            <option value="upi">UPI</option>
            <option value="other">Other</option>
          </select>
          <input style={field} type="number" step="0.01" min="0.01" placeholder="Amount" required value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })} />
          <input style={field} placeholder="Note" value={form.note}
            onChange={(e) => setForm({ ...form, note: e.target.value })} />
          <button type="submit" style={{ ...field, background: "#2563eb", color: "#fff", border: "none", cursor: "pointer" }}>
            Save payment
          </button>
        </form>
        {msg && <p style={{ color: "#15803d" }}>{msg}</p>}
      </div>

      <div style={{ ...box, marginTop: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
          <h2 style={{ margin: 0 }}>Invoices</h2>
          <select style={{ ...field, width: "auto" }} value={status}
            onChange={(e) => { setSkip(0); setStatus(e.target.value); }}>
            <option value="">All</option>
            <option value="paid">Paid</option>
            <option value="outstanding">Outstanding</option>
            <option value="overdue">Overdue</option>
          </select>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 10 }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid #e5e7eb" }}>
                <th>ID</th><th>Invoice</th><th>Due</th><th>Total</th><th>Paid</th><th>Balance</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} style={{ borderBottom: "1px solid #f3f4f6", cursor: "pointer" }}
                  onClick={() => setForm({ ...form, invoice_id: String(r.id), amount: String(r.balance) })}>
                  <td>{r.id}</td>
                  <td>{r.invoice_number}</td>
                  <td>{r.due_date ? r.due_date.slice(0, 10) : "-"}</td>
                  <td>{money(r.total)}</td>
                  <td>{money(r.amount_paid)}</td>
                  <td>{money(r.balance)}</td>
                  <td style={{ color: r.is_overdue ? "#b91c1c" : "inherit" }}>{r.is_overdue ? "overdue" : r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ color: "#6b7280", fontSize: 13 }}>Tap a row to fill the payment form.</p>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button disabled={skip === 0} onClick={() => setSkip(Math.max(0, skip - PAGE))}>Previous</button>
          <span>{total === 0 ? 0 : skip + 1}–{Math.min(skip + PAGE, total)} of {total}</span>
          <button disabled={skip + PAGE >= total} onClick={() => setSkip(skip + PAGE)}>Next</button>
        </div>
      </div>
    </div>
  );
}