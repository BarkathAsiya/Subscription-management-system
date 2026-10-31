import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';

export default function TaxesTab({ onNotification }) {
  const [taxes, setTaxes] = useState([]);
  const [products, setProducts] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterScope, setFilterScope] = useState('all');
  const [filterActive, setFilterActive] = useState('all');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTax, setEditingTax] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const initialForm = {
    name: '',
    description: '',
    rate: '',
    applicable_scope: 'all',
    product_type: 'Physical',
    product_id: '',
    plan_id: '',
    start_date: '',
    end_date: '',
    is_active: true,
  };

  const [taxForm, setTaxForm] = useState(initialForm);

  // Interactive Tax Calculator State
  const [calcAmount, setCalcAmount] = useState('1000');
  const [calcProductType, setCalcProductType] = useState('Physical');
  const [calcProductId, setCalcProductId] = useState('');
  const [calcPlanId, setCalcPlanId] = useState('');
  const [calcResult, setCalcResult] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [taxesData, productsData, plansData] = await Promise.all([
        api.getTaxes(),
        api.getProducts(),
        api.getPlans(),
      ]);
      setTaxes(taxesData);
      setProducts(productsData);
      setPlans(plansData);
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }, [onNotification]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleOpenModal = (tax = null) => {
    if (tax) {
      setEditingTax(tax);
      setTaxForm({
        name: tax.name,
        description: tax.description || '',
        rate: tax.rate,
        applicable_scope: tax.applicable_scope,
        product_type: tax.product_type || 'Physical',
        product_id: tax.product_id || '',
        plan_id: tax.plan_id || '',
        start_date: tax.start_date || '',
        end_date: tax.end_date || '',
        is_active: tax.is_active,
      });
    } else {
      setEditingTax(null);
      setTaxForm(initialForm);
    }
    setIsModalOpen(true);
  };

  const handleSaveTax = async (e) => {
    e.preventDefault();
    if (!taxForm.name.trim()) {
      onNotification('Tax rule name is required', 'error');
      return;
    }
    const rateVal = parseFloat(taxForm.rate);
    if (isNaN(rateVal) || rateVal < 0 || rateVal > 100) {
      onNotification('Tax rate must be between 0% and 100%', 'error');
      return;
    }
    if (taxForm.start_date && taxForm.end_date && taxForm.start_date > taxForm.end_date) {
      onNotification('Start date cannot be after end date', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name: taxForm.name.trim(),
        description: taxForm.description.trim(),
        rate: rateVal,
        applicable_scope: taxForm.applicable_scope,
        product_type: taxForm.applicable_scope === 'product_type' ? taxForm.product_type : null,
        product_id: taxForm.applicable_scope === 'product' && taxForm.product_id ? parseInt(taxForm.product_id, 10) : null,
        plan_id: taxForm.applicable_scope === 'plan' && taxForm.plan_id ? parseInt(taxForm.plan_id, 10) : null,
        start_date: taxForm.start_date || null,
        end_date: taxForm.end_date || null,
        is_active: Boolean(taxForm.is_active),
      };

      if (editingTax) {
        await api.updateTax(editingTax.id, payload);
        onNotification(`Tax rule "${payload.name}" updated successfully!`, 'success');
      } else {
        await api.createTax(payload);
        onNotification(`Tax rule "${payload.name}" created successfully!`, 'success');
      }
      setIsModalOpen(false);
      await loadData();
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleStatus = async (tax) => {
    const newStatus = !tax.is_active;
    try {
      await api.toggleTaxStatus(tax.id, newStatus);
      onNotification(`Tax rule "${tax.name}" is now ${newStatus ? 'Active' : 'Inactive'}`, 'success');
      await loadData();
    } catch (err) {
      onNotification(err.message, 'error');
    }
  };

  const handleDeleteTax = async (tax) => {
    if (!window.confirm(`Delete tax rule "${tax.name}"?`)) return;
    try {
      await api.deleteTax(tax.id);
      onNotification(`Tax rule "${tax.name}" deleted successfully`, 'success');
      await loadData();
    } catch (err) {
      onNotification(err.message, 'error');
    }
  };

  // Interactive Tax Calculator Handler
  const handleCalculateTax = async (e) => {
    e.preventDefault();
    const amountNum = parseFloat(calcAmount);
    if (isNaN(amountNum) || amountNum < 0) {
      onNotification('Enter a valid non-negative base amount', 'error');
      return;
    }

    setCalcLoading(true);
    setCalcResult(null);
    try {
      const res = await api.calculateTax({
        amount: amountNum,
        product_type: calcProductType,
        product_id: calcProductId ? parseInt(calcProductId, 10) : null,
        plan_id: calcPlanId ? parseInt(calcPlanId, 10) : null,
      });
      setCalcResult(res);
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setCalcLoading(false);
    }
  };

  const filteredTaxes = taxes.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (t.description && t.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesScope = filterScope === 'all' || t.applicable_scope === filterScope;
    const matchesActive =
      filterActive === 'all' ||
      (filterActive === 'active' && t.is_active) ||
      (filterActive === 'inactive' && !t.is_active);
    return matchesSearch && matchesScope && matchesActive;
  });

  return (
    <div className="tab-container">
      <div className="tab-header">
        <div>
          <h2>Tax Rules & Rate Configuration</h2>
          <p className="tab-subtitle">
            Configure flexible tax slabs (GST, VAT, Sales Tax) mapped to product categories, specific items, or subscription plans.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => handleOpenModal()}>
          + Create Tax Rule
        </button>
      </div>

      {/* Interactive Tax Calculator Tool */}
      <div className="tool-card">
        <div className="tool-card-header">
          <span className="tool-icon">🧾</span>
          <div>
            <h4>Interactive Tax Calculation Engine</h4>
            <p>Compute precise tax liability based on dynamic product category and plan rules.</p>
          </div>
        </div>
        <form onSubmit={handleCalculateTax} className="tool-form">
          <div className="tool-input-row">
            <div className="form-group">
              <label>Base Price / Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                placeholder="1000.00"
                value={calcAmount}
                onChange={(e) => setCalcAmount(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Product Category</label>
              <select value={calcProductType} onChange={(e) => setCalcProductType(e.target.value)}>
                <option value="Physical">Physical Product</option>
                <option value="Service">Service</option>
                <option value="Digital">Digital</option>
              </select>
            </div>
            <div className="form-group">
              <label>Specific Product (Optional)</label>
              <select value={calcProductId} onChange={(e) => setCalcProductId(e.target.value)}>
                <option value="">-- None / Category Wide --</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Plan (Optional)</label>
              <select value={calcPlanId} onChange={(e) => setCalcPlanId(e.target.value)}>
                <option value="">-- None / Standalone --</option>
                {plans.map((pl) => (
                  <option key={pl.id} value={pl.id}>
                    {pl.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group tool-btn-group">
              <button type="submit" className="btn btn-primary" disabled={calcLoading}>
                {calcLoading ? 'Calculating...' : 'Calculate Tax'}
              </button>
            </div>
          </div>
        </form>

        {calcResult && (
          <div className="tool-result-box result-success">
            <div className="result-headline text-primary">
              Tax Calculation Summary ({calcResult.combined_rate}% Total Tax Rate)
            </div>
            <div className="result-breakdown">
              <span>Base Amount: ₹{calcResult.amount.toFixed(2)}</span>
              <span className="text-warning">
                Tax Amount ({calcResult.combined_rate}%): +₹{calcResult.tax_amount.toFixed(2)}
              </span>
              <span className="font-bold text-success">
                Total Price (Incl. Tax): ₹{calcResult.total_with_tax.toFixed(2)}
              </span>
            </div>
            {calcResult.applicable_tax_rules.length > 0 && (
              <div className="matching-taxes-tags">
                <span style={{ fontSize: '0.8rem', color: '#666' }}>Rules Applied: </span>
                {calcResult.applicable_tax_rules.map((r) => (
                  <span key={r.id} className="badge badge-tax">
                    {r.name} ({r.rate}%)
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="filter-bar">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search tax rules by name or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label>Scope:</label>
          <select value={filterScope} onChange={(e) => setFilterScope(e.target.value)}>
            <option value="all">All Scopes</option>
            <option value="product_type">Product Type</option>
            <option value="product">Specific Product</option>
            <option value="plan">Specific Plan</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Status:</label>
          <select value={filterActive} onChange={(e) => setFilterActive(e.target.value)}>
            <option value="all">All Status</option>
            <option value="active">Active Only</option>
            <option value="inactive">Inactive Only</option>
          </select>
        </div>
        <button className="btn btn-secondary" onClick={loadData} title="Refresh">
          ↻ Refresh
        </button>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading tax rules from PostgreSQL...</p>
        </div>
      ) : filteredTaxes.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🧾</div>
          <h3>No tax rules found</h3>
          <p>Configure tax brackets and rates applicable to your catalog.</p>
          <button className="btn btn-primary" onClick={() => handleOpenModal()}>
            + Create Tax Rule
          </button>
        </div>
      ) : (
        <div className="taxes-grid">
          {filteredTaxes.map((t) => (
            <div key={t.id} className={`tax-card ${!t.is_active ? 'tax-card-inactive' : ''}`}>
              <div className="tax-card-header">
                <div>
                  <div className="tax-rate-badge">{t.rate}% RATE</div>
                  <h3 className="tax-title">{t.name}</h3>
                </div>
                <div className="tax-actions">
                  <button className="btn-icon" title="Edit Tax Rule" onClick={() => handleOpenModal(t)}>
                    ✏️
                  </button>
                  <button className="btn-icon btn-danger-icon" title="Delete Tax Rule" onClick={() => handleDeleteTax(t)}>
                    🗑️
                  </button>
                </div>
              </div>

              {t.description && <p className="tax-description">{t.description}</p>}

              <div className="tax-details-list">
                <div className="tax-detail-item">
                  <span className="detail-label">Scope:</span>
                  <span className="detail-value capitalize">
                    {t.applicable_scope === 'all'
                      ? 'All Catalog Items'
                      : t.applicable_scope === 'product_type'
                      ? `Category: ${t.product_type}`
                      : t.applicable_scope === 'product'
                      ? `Product #${t.product_id}`
                      : `Plan #${t.plan_id}`}
                  </span>
                </div>
                {(t.start_date || t.end_date) && (
                  <div className="tax-detail-item">
                    <span className="detail-label">Effective Dates:</span>
                    <span className="detail-value">
                      {t.start_date || 'Immediate'} to {t.end_date || 'Indefinite'}
                    </span>
                  </div>
                )}
                <div className="tax-detail-item">
                  <span className="detail-label">Status:</span>
                  <span className={`badge ${t.is_active ? 'badge-active' : 'badge-inactive'}`}>
                    {t.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>

              <div className="tax-card-footer">
                <button
                  className={`btn btn-sm ${t.is_active ? 'btn-outline-danger' : 'btn-outline-success'}`}
                  onClick={() => handleToggleStatus(t)}
                >
                  {t.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Tax Rule Modal */}
      {isModalOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h3>{editingTax ? 'Edit Tax Rule' : 'Create Tax Rule'}</h3>
              <button className="btn-close" onClick={() => setIsModalOpen(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleSaveTax}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Tax Rule Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. GST Standard 18%, Handloom GST 5%..."
                    value={taxForm.name}
                    onChange={(e) => setTaxForm({ ...taxForm, name: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Tax Rate (%) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    required
                    placeholder="18.00"
                    value={taxForm.rate}
                    onChange={(e) => setTaxForm({ ...taxForm, rate: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <input
                    type="text"
                    placeholder="Explanation of tax applicability..."
                    value={taxForm.description}
                    onChange={(e) => setTaxForm({ ...taxForm, description: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Applicable Scope *</label>
                  <select
                    value={taxForm.applicable_scope}
                    onChange={(e) => setTaxForm({ ...taxForm, applicable_scope: e.target.value })}
                  >
                    <option value="all">All Products & Services</option>
                    <option value="product_type">Specific Category / Product Type</option>
                    <option value="product">Specific Product</option>
                    <option value="plan">Specific Subscription Plan</option>
                  </select>
                </div>

                {taxForm.applicable_scope === 'product_type' && (
                  <div className="form-group">
                    <label>Product Type / Category *</label>
                    <select
                      value={taxForm.product_type}
                      onChange={(e) => setTaxForm({ ...taxForm, product_type: e.target.value })}
                    >
                      <option value="Physical">Physical Product</option>
                      <option value="Service">Service</option>
                      <option value="Digital">Digital</option>
                    </select>
                  </div>
                )}

                {taxForm.applicable_scope === 'product' && (
                  <div className="form-group">
                    <label>Select Product *</label>
                    <select
                      value={taxForm.product_id}
                      onChange={(e) => setTaxForm({ ...taxForm, product_id: e.target.value })}
                      required
                    >
                      <option value="">-- Choose Product --</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {taxForm.applicable_scope === 'plan' && (
                  <div className="form-group">
                    <label>Select Subscription Plan *</label>
                    <select
                      value={taxForm.plan_id}
                      onChange={(e) => setTaxForm({ ...taxForm, plan_id: e.target.value })}
                      required
                    >
                      <option value="">-- Choose Plan --</option>
                      {plans.map((pl) => (
                        <option key={pl.id} value={pl.id}>
                          {pl.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="form-row">
                  <div className="form-group">
                    <label>Effective Start Date</label>
                    <input
                      type="date"
                      value={taxForm.start_date}
                      onChange={(e) => setTaxForm({ ...taxForm, start_date: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Effective End Date</label>
                    <input
                      type="date"
                      value={taxForm.end_date}
                      onChange={(e) => setTaxForm({ ...taxForm, end_date: e.target.value })}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={taxForm.is_active}
                      onChange={(e) => setTaxForm({ ...taxForm, is_active: e.target.checked })}
                    />
                    Tax rule is currently active
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Saving...' : editingTax ? 'Save Changes' : 'Create Tax Rule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
