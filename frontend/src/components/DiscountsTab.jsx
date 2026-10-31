import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';

export default function DiscountsTab({ onNotification }) {
  const [discounts, setDiscounts] = useState([]);
  const [products, setProducts] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterActive, setFilterActive] = useState('all');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDiscount, setEditingDiscount] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const initialForm = {
    code: '',
    description: '',
    discount_type: 'percentage',
    discount_value: '',
    min_purchase_amount: '0',
    min_quantity: '1',
    start_date: '',
    end_date: '',
    usage_limit: '',
    applicable_to: 'all',
    product_id: '',
    variant_id: '',
    plan_id: '',
    is_active: true,
  };

  const [discountForm, setDiscountForm] = useState(initialForm);

  // Live Discount Validator / Calculator Tool state
  const [testCode, setTestCode] = useState('');
  const [testSubtotal, setTestSubtotal] = useState('1000');
  const [testQuantity, setTestQuantity] = useState('1');
  const [testProductId, setTestProductId] = useState('');
  const [testPlanId, setTestPlanId] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [discountsData, productsData, plansData] = await Promise.all([
        api.getDiscounts(),
        api.getProducts(),
        api.getPlans(),
      ]);
      setDiscounts(discountsData);
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

  const handleOpenModal = (disc = null) => {
    if (disc) {
      setEditingDiscount(disc);
      setDiscountForm({
        code: disc.code,
        description: disc.description || '',
        discount_type: disc.discount_type,
        discount_value: disc.discount_value,
        min_purchase_amount: disc.min_purchase_amount,
        min_quantity: disc.min_quantity,
        start_date: disc.start_date || '',
        end_date: disc.end_date || '',
        usage_limit: disc.usage_limit || '',
        applicable_to: disc.applicable_to,
        product_id: disc.product_id || '',
        variant_id: disc.variant_id || '',
        plan_id: disc.plan_id || '',
        is_active: disc.is_active,
      });
    } else {
      setEditingDiscount(null);
      setDiscountForm(initialForm);
    }
    setIsModalOpen(true);
  };

  const handleSaveDiscount = async (e) => {
    e.preventDefault();
    if (!discountForm.code.trim()) {
      onNotification('Discount code is required', 'error');
      return;
    }
    const val = parseFloat(discountForm.discount_value);
    if (isNaN(val) || val < 0) {
      onNotification('Discount value must be a non-negative number', 'error');
      return;
    }
    if (discountForm.discount_type === 'percentage' && val > 100) {
      onNotification('Percentage discount cannot exceed 100%', 'error');
      return;
    }
    if (discountForm.start_date && discountForm.end_date && discountForm.start_date > discountForm.end_date) {
      onNotification('Start date cannot be after end date', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        code: discountForm.code.trim().toUpperCase(),
        description: discountForm.description.trim(),
        discount_type: discountForm.discount_type,
        discount_value: val,
        min_purchase_amount: parseFloat(discountForm.min_purchase_amount) || 0.0,
        min_quantity: parseInt(discountForm.min_quantity, 10) || 1,
        start_date: discountForm.start_date || null,
        end_date: discountForm.end_date || null,
        usage_limit: discountForm.usage_limit ? parseInt(discountForm.usage_limit, 10) : null,
        applicable_to: discountForm.applicable_to,
        product_id: discountForm.product_id ? parseInt(discountForm.product_id, 10) : null,
        variant_id: discountForm.variant_id ? parseInt(discountForm.variant_id, 10) : null,
        plan_id: discountForm.plan_id ? parseInt(discountForm.plan_id, 10) : null,
        is_active: Boolean(discountForm.is_active),
      };

      if (editingDiscount) {
        await api.updateDiscount(editingDiscount.id, payload);
        onNotification(`Discount "${payload.code}" updated successfully!`, 'success');
      } else {
        await api.createDiscount(payload);
        onNotification(`Discount "${payload.code}" created successfully!`, 'success');
      }
      setIsModalOpen(false);
      await loadData();
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleStatus = async (discount) => {
    const newStatus = !discount.is_active;
    try {
      await api.toggleDiscountStatus(discount.id, newStatus);
      onNotification(`Discount "${discount.code}" is now ${newStatus ? 'Active' : 'Inactive'}`, 'success');
      await loadData();
    } catch (err) {
      onNotification(err.message, 'error');
    }
  };

  const handleDeleteDiscount = async (discount) => {
    if (!window.confirm(`Delete discount rule "${discount.code}"?`)) return;
    try {
      await api.deleteDiscount(discount.id);
      onNotification(`Discount "${discount.code}" deleted successfully`, 'success');
      await loadData();
    } catch (err) {
      onNotification(err.message, 'error');
    }
  };

  // Test discount calculation handler
  const handleTestDiscount = async (e) => {
    e.preventDefault();
    if (!testCode.trim()) {
      onNotification('Enter a discount code to test', 'error');
      return;
    }
    setTestLoading(true);
    setTestResult(null);
    try {
      const res = await api.validateDiscount({
        code: testCode.trim().toUpperCase(),
        subtotal: parseFloat(testSubtotal) || 0,
        quantity: parseInt(testQuantity, 10) || 1,
        product_id: testProductId ? parseInt(testProductId, 10) : null,
        plan_id: testPlanId ? parseInt(testPlanId, 10) : null,
      });
      setTestResult(res);
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setTestLoading(false);
    }
  };

  const filteredDiscounts = discounts.filter((d) => {
    const matchesSearch =
      d.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (d.description && d.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = filterType === 'all' || d.discount_type === filterType;
    const matchesActive =
      filterActive === 'all' ||
      (filterActive === 'active' && d.is_active) ||
      (filterActive === 'inactive' && !d.is_active);
    return matchesSearch && matchesType && matchesActive;
  });

  return (
    <div className="tab-container">
      <div className="tab-header">
        <div>
          <h2>Discount Rules & Management</h2>
          <p className="tab-subtitle">
            Configure percentage and fixed promotional discounts, enforce usage limits, minimum quantities, and date windows.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => handleOpenModal()}>
          + Create Discount Rule
        </button>
      </div>

      {/* Interactive Discount Eligibility Calculator Tool */}
      <div className="tool-card">
        <div className="tool-card-header">
          <span className="tool-icon">🏷️</span>
          <div>
            <h4>Interactive Discount Validator & Pricing Engine</h4>
            <p>Simulate order validation against your active discount rules in real-time.</p>
          </div>
        </div>
        <form onSubmit={handleTestDiscount} className="tool-form">
          <div className="tool-input-row">
            <div className="form-group">
              <label>Promo Code</label>
              <input
                type="text"
                placeholder="e.g. FESTIVE20, SAVE150"
                value={testCode}
                onChange={(e) => setTestCode(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Subtotal (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                placeholder="1000.00"
                value={testSubtotal}
                onChange={(e) => setTestSubtotal(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Quantity</label>
              <input
                type="number"
                min="1"
                value={testQuantity}
                onChange={(e) => setTestQuantity(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Product (Optional)</label>
              <select value={testProductId} onChange={(e) => setTestProductId(e.target.value)}>
                <option value="">-- Any / Not Specified --</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Plan (Optional)</label>
              <select value={testPlanId} onChange={(e) => setTestPlanId(e.target.value)}>
                <option value="">-- Any / Not Specified --</option>
                {plans.map((pl) => (
                  <option key={pl.id} value={pl.id}>
                    {pl.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group tool-btn-group">
              <button type="submit" className="btn btn-primary" disabled={testLoading}>
                {testLoading ? 'Validating...' : 'Validate & Calculate'}
              </button>
            </div>
          </div>
        </form>

        {testResult && (
          <div className={`tool-result-box ${testResult.is_valid ? 'result-success' : 'result-error'}`}>
            {testResult.is_valid ? (
              <div>
                <div className="result-headline text-success">
                  ✓ Code <strong>{testResult.code}</strong> Applied Successfully!
                </div>
                <div className="result-breakdown">
                  <span>Subtotal: ₹{parseFloat(testSubtotal).toFixed(2)}</span>
                  <span className="text-success">
                    Discount ({testResult.discount_type === 'percentage' ? `${testResult.discount_value}%` : `Flat ₹${testResult.discount_value}`}): -₹{testResult.discount_amount.toFixed(2)}
                  </span>
                  <span className="font-bold text-primary">Final Payable: ₹{testResult.final_amount.toFixed(2)}</span>
                </div>
              </div>
            ) : (
              <div className="text-danger">
                ✕ Discount Not Applicable: <strong>{testResult.reason}</strong>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="filter-bar">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search discount codes or descriptions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label>Type:</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="all">All Types</option>
            <option value="percentage">Percentage (%)</option>
            <option value="fixed">Fixed (₹)</option>
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
          <p>Loading discount rules from PostgreSQL...</p>
        </div>
      ) : filteredDiscounts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🏷️</div>
          <h3>No discount rules found</h3>
          <p>Configure percentage or fixed promotional discounts for your store.</p>
          <button className="btn btn-primary" onClick={() => handleOpenModal()}>
            + Create Discount
          </button>
        </div>
      ) : (
        <div className="discounts-grid">
          {filteredDiscounts.map((d) => (
            <div key={d.id} className={`discount-card ${!d.is_active ? 'discount-card-inactive' : ''}`}>
              <div className="discount-card-header">
                <div>
                  <div className="discount-code-badge">{d.code}</div>
                  <span className={`badge ${d.is_active ? 'badge-active' : 'badge-inactive'}`}>
                    {d.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="discount-actions">
                  <button className="btn-icon" title="Edit Discount" onClick={() => handleOpenModal(d)}>
                    ✏️
                  </button>
                  <button className="btn-icon btn-danger-icon" title="Delete Discount" onClick={() => handleDeleteDiscount(d)}>
                    🗑️
                  </button>
                </div>
              </div>

              <div className="discount-value-display">
                {d.discount_type === 'percentage' ? `${d.discount_value}% OFF` : `₹${d.discount_value.toFixed(2)} FLAT OFF`}
              </div>

              {d.description && <p className="discount-description">{d.description}</p>}

              <div className="discount-conditions">
                <div className="condition-item">
                  <span className="condition-label">Applicable Scope:</span>
                  <span className="condition-value capitalize">{d.applicable_to}</span>
                </div>
                {d.min_purchase_amount > 0 && (
                  <div className="condition-item">
                    <span className="condition-label">Min Purchase:</span>
                    <span className="condition-value">₹{d.min_purchase_amount.toFixed(2)}</span>
                  </div>
                )}
                {d.min_quantity > 1 && (
                  <div className="condition-item">
                    <span className="condition-label">Min Quantity:</span>
                    <span className="condition-value">{d.min_quantity} items</span>
                  </div>
                )}
                {(d.start_date || d.end_date) && (
                  <div className="condition-item">
                    <span className="condition-label">Validity:</span>
                    <span className="condition-value">
                      {d.start_date || 'Anytime'} to {d.end_date || 'Ongoing'}
                    </span>
                  </div>
                )}
                {d.usage_limit && (
                  <div className="condition-item">
                    <span className="condition-label">Usage:</span>
                    <span className="condition-value">
                      {d.times_used} / {d.usage_limit} used
                    </span>
                  </div>
                )}
              </div>

              <div className="discount-card-footer">
                <button
                  className={`btn btn-sm ${d.is_active ? 'btn-outline-danger' : 'btn-outline-success'}`}
                  onClick={() => handleToggleStatus(d)}
                >
                  {d.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => {
                    setTestCode(d.code);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                >
                  Test Code ⚡
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Discount Modal */}
      {isModalOpen && (
        <div className="modal-backdrop">
          <div className="modal modal-lg">
            <div className="modal-header">
              <h3>{editingDiscount ? 'Edit Discount Rule' : 'Create Discount Rule'}</h3>
              <button className="btn-close" onClick={() => setIsModalOpen(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleSaveDiscount}>
              <div className="modal-body">
                <div className="form-row">
                  <div className="form-group">
                    <label>Discount Code *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. FESTIVE20"
                      value={discountForm.code}
                      onChange={(e) => setDiscountForm({ ...discountForm, code: e.target.value.toUpperCase() })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Discount Type *</label>
                    <select
                      value={discountForm.discount_type}
                      onChange={(e) => setDiscountForm({ ...discountForm, discount_type: e.target.value })}
                    >
                      <option value="percentage">Percentage (%)</option>
                      <option value="fixed">Fixed Amount (₹)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>
                      Discount Value {discountForm.discount_type === 'percentage' ? '(%) *' : '(₹) *'}
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max={discountForm.discount_type === 'percentage' ? 100 : undefined}
                      required
                      placeholder={discountForm.discount_type === 'percentage' ? '20' : '150.00'}
                      value={discountForm.discount_value}
                      onChange={(e) => setDiscountForm({ ...discountForm, discount_value: e.target.value })}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <input
                    type="text"
                    placeholder="Short description of this promo code..."
                    value={discountForm.description}
                    onChange={(e) => setDiscountForm({ ...discountForm, description: e.target.value })}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Min Purchase Amount (₹)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={discountForm.min_purchase_amount}
                      onChange={(e) => setDiscountForm({ ...discountForm, min_purchase_amount: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Min Order Quantity</label>
                    <input
                      type="number"
                      min="1"
                      value={discountForm.min_quantity}
                      onChange={(e) => setDiscountForm({ ...discountForm, min_quantity: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Total Usage Limit (Optional)</label>
                    <input
                      type="number"
                      min="1"
                      placeholder="Unlimited"
                      value={discountForm.usage_limit}
                      onChange={(e) => setDiscountForm({ ...discountForm, usage_limit: e.target.value })}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Start Date</label>
                    <input
                      type="date"
                      value={discountForm.start_date}
                      onChange={(e) => setDiscountForm({ ...discountForm, start_date: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>End Date</label>
                    <input
                      type="date"
                      value={discountForm.end_date}
                      onChange={(e) => setDiscountForm({ ...discountForm, end_date: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Applicable To</label>
                    <select
                      value={discountForm.applicable_to}
                      onChange={(e) => setDiscountForm({ ...discountForm, applicable_to: e.target.value })}
                    >
                      <option value="all">All Items</option>
                      <option value="product">Specific Product</option>
                      <option value="plan">Specific Subscription Plan</option>
                    </select>
                  </div>
                </div>

                {discountForm.applicable_to === 'product' && (
                  <div className="form-group">
                    <label>Select Product *</label>
                    <select
                      value={discountForm.product_id}
                      onChange={(e) => setDiscountForm({ ...discountForm, product_id: e.target.value })}
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

                {discountForm.applicable_to === 'plan' && (
                  <div className="form-group">
                    <label>Select Subscription Plan *</label>
                    <select
                      value={discountForm.plan_id}
                      onChange={(e) => setDiscountForm({ ...discountForm, plan_id: e.target.value })}
                      required
                    >
                      <option value="">-- Choose Plan --</option>
                      {plans.map((pl) => (
                        <option key={pl.id} value={pl.id}>
                          {pl.name} (₹{pl.price})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={discountForm.is_active}
                      onChange={(e) => setDiscountForm({ ...discountForm, is_active: e.target.checked })}
                    />
                    Discount rule is currently active
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Saving...' : editingDiscount ? 'Save Changes' : 'Create Discount'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
