import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';

export default function PlansTab({ onNotification }) {
  const [plans, setPlans] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPeriod, setFilterPeriod] = useState('all');
  const [filterActive, setFilterActive] = useState('all');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const initialForm = {
    name: '',
    description: '',
    billing_period: 'monthly',
    price: '',
    product_id: '',
    variant_id: '',
    min_quantity: 1,
    start_date: '',
    end_date: '',
    allow_pause: true,
    allow_renewal: true,
    allow_early_close: true,
    auto_close_on_condition: false,
    is_active: true,
  };

  const [planForm, setPlanForm] = useState(initialForm);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [plansData, productsData] = await Promise.all([
        api.getPlans(),
        api.getProducts(),
      ]);
      setPlans(plansData);
      setProducts(productsData);
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }, [onNotification]);

  useEffect(() => {
    let isMounted = true;
    Promise.all([api.getPlans(), api.getProducts()])
      .then(([plansData, productsData]) => {
        if (isMounted) {
          setPlans(plansData);
          setProducts(productsData);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          onNotification(err.message, 'error');
          setLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, [onNotification]);

  const handleOpenModal = (plan = null) => {
    if (plan) {
      setEditingPlan(plan);
      setPlanForm({
        name: plan.name,
        description: plan.description || '',
        billing_period: plan.billing_period,
        price: plan.price,
        product_id: plan.product_id,
        variant_id: plan.variant_id || '',
        min_quantity: plan.min_quantity,
        start_date: plan.start_date || '',
        end_date: plan.end_date || '',
        allow_pause: plan.allow_pause,
        allow_renewal: plan.allow_renewal,
        allow_early_close: plan.allow_early_close,
        auto_close_on_condition: plan.auto_close_on_condition,
        is_active: plan.is_active,
      });
    } else {
      setEditingPlan(null);
      setPlanForm({
        ...initialForm,
        product_id: products.length > 0 ? products[0].id : '',
      });
    }
    setIsModalOpen(true);
  };

  const handleSavePlan = async (e) => {
    e.preventDefault();
    if (!planForm.name.trim()) {
      onNotification('Plan name is required', 'error');
      return;
    }
    const priceNum = parseFloat(planForm.price);
    if (isNaN(priceNum) || priceNum < 0) {
      onNotification('Price must be a valid positive number', 'error');
      return;
    }
    if (!planForm.product_id) {
      onNotification('You must associate a product with this plan', 'error');
      return;
    }
    if (planForm.start_date && planForm.end_date && planForm.start_date > planForm.end_date) {
      onNotification('Start date cannot be after end date', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name: planForm.name.trim(),
        description: planForm.description.trim(),
        billing_period: planForm.billing_period,
        price: priceNum,
        product_id: parseInt(planForm.product_id, 10),
        variant_id: planForm.variant_id ? parseInt(planForm.variant_id, 10) : null,
        min_quantity: parseInt(planForm.min_quantity, 10) || 1,
        start_date: planForm.start_date || null,
        end_date: planForm.end_date || null,
        allow_pause: Boolean(planForm.allow_pause),
        allow_renewal: Boolean(planForm.allow_renewal),
        allow_early_close: Boolean(planForm.allow_early_close),
        auto_close_on_condition: Boolean(planForm.auto_close_on_condition),
        is_active: Boolean(planForm.is_active),
      };

      if (editingPlan) {
        await api.updatePlan(editingPlan.id, payload);
        onNotification(`Plan "${payload.name}" updated successfully!`, 'success');
      } else {
        await api.createPlan(payload);
        onNotification(`Plan "${payload.name}" created successfully!`, 'success');
      }
      setIsModalOpen(false);
      await loadData();
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleStatus = async (plan) => {
    const newStatus = !plan.is_active;
    try {
      await api.togglePlanStatus(plan.id, newStatus);
      onNotification(`Plan "${plan.name}" is now ${newStatus ? 'Active' : 'Inactive'}`, 'success');
      await loadData();
    } catch (err) {
      onNotification(err.message, 'error');
    }
  };

  const handleDeletePlan = async (plan) => {
    if (!window.confirm(`Are you sure you want to delete plan "${plan.name}"?`)) return;
    try {
      await api.deletePlan(plan.id);
      onNotification(`Plan "${plan.name}" deleted successfully`, 'success');
      await loadData();
    } catch (err) {
      onNotification(err.message, 'error');
    }
  };

  // Get selected product's variants for the form dropdown
  const selectedProduct = products.find((p) => p.id === parseInt(planForm.product_id, 10));
  const availableVariants = selectedProduct?.variants || [];

  const filteredPlans = plans.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (p.product_name && p.product_name.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesPeriod = filterPeriod === 'all' || p.billing_period === filterPeriod;
    const matchesActive =
      filterActive === 'all' ||
      (filterActive === 'active' && p.is_active) ||
      (filterActive === 'inactive' && !p.is_active);
    return matchesSearch && matchesPeriod && matchesActive;
  });

  return (
    <div className="tab-container">
      <div className="tab-header">
        <div>
          <h2>Subscription Plan Configuration</h2>
          <p className="tab-subtitle">
            Configure recurring billing cadences, pricing tiers, min order quantities, and lifecycle policies (pause, renew, close).
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => handleOpenModal()}>
          + Create Subscription Plan
        </button>
      </div>

      <div className="filter-bar">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search plans by name, product, description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label>Billing Period:</label>
          <select value={filterPeriod} onChange={(e) => setFilterPeriod(e.target.value)}>
            <option value="all">All Periods</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
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
          <p>Loading subscription plans from PostgreSQL...</p>
        </div>
      ) : filteredPlans.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📅</div>
          <h3>No subscription plans found</h3>
          <p>Create your first recurring subscription plan attached to a product.</p>
          <button className="btn btn-primary" onClick={() => handleOpenModal()}>
            + Create Plan
          </button>
        </div>
      ) : (
        <div className="plans-grid">
          {filteredPlans.map((plan) => (
            <div key={plan.id} className={`plan-card ${!plan.is_active ? 'plan-card-inactive' : ''}`}>
              <div className="plan-card-header">
                <div>
                  <div className="badges-row">
                    <span className="badge badge-period">{plan.billing_period.toUpperCase()}</span>
                    <span className={`badge ${plan.is_active ? 'badge-active' : 'badge-inactive'}`}>
                      {plan.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <h3 className="plan-title">{plan.name}</h3>
                </div>
                <div className="plan-actions">
                  <button className="btn-icon" title="Edit Plan" onClick={() => handleOpenModal(plan)}>
                    ✏️
                  </button>
                  <button className="btn-icon btn-danger-icon" title="Delete Plan" onClick={() => handleDeletePlan(plan)}>
                    🗑️
                  </button>
                </div>
              </div>

              <div className="plan-pricing">
                <span className="plan-price">₹{plan.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                <span className="plan-period">/ {plan.billing_period}</span>
              </div>

              {plan.description && <p className="plan-description">{plan.description}</p>}

              <div className="plan-details-list">
                <div className="plan-detail-item">
                  <span className="detail-label">Associated Product:</span>
                  <span className="detail-value">
                    {plan.product_name || `Product #${plan.product_id}`}
                    {plan.variant_name && <span className="variant-tag"> ({plan.variant_name})</span>}
                  </span>
                </div>
                <div className="plan-detail-item">
                  <span className="detail-label">Minimum Quantity:</span>
                  <span className="detail-value">{plan.min_quantity} item(s)</span>
                </div>
                {(plan.start_date || plan.end_date) && (
                  <div className="plan-detail-item">
                    <span className="detail-label">Availability:</span>
                    <span className="detail-value">
                      {plan.start_date || 'Immediate'} to {plan.end_date || 'Indefinite'}
                    </span>
                  </div>
                )}
              </div>

              {/* Policy badges */}
              <div className="policy-badges">
                <span className={`policy-pill ${plan.allow_pause ? 'pill-enabled' : 'pill-disabled'}`}>
                  {plan.allow_pause ? '✓ Pause' : '✕ No Pause'}
                </span>
                <span className={`policy-pill ${plan.allow_renewal ? 'pill-enabled' : 'pill-disabled'}`}>
                  {plan.allow_renewal ? '✓ Renewal' : '✕ No Renewal'}
                </span>
                <span className={`policy-pill ${plan.allow_early_close ? 'pill-enabled' : 'pill-disabled'}`}>
                  {plan.allow_early_close ? '✓ Early Close' : '✕ Lock-in'}
                </span>
                {plan.auto_close_on_condition && (
                  <span className="policy-pill pill-warning">⚡ Auto-close</span>
                )}
              </div>

              <div className="plan-card-footer">
                <button
                  className={`btn btn-sm ${plan.is_active ? 'btn-outline-danger' : 'btn-outline-success'}`}
                  onClick={() => handleToggleStatus(plan)}
                >
                  {plan.is_active ? 'Deactivate Plan' : 'Activate Plan'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Plan Modal */}
      {isModalOpen && (
        <div className="modal-backdrop">
          <div className="modal modal-lg">
            <div className="modal-header">
              <h3>{editingPlan ? 'Edit Subscription Plan' : 'Create Subscription Plan'}</h3>
              <button className="btn-close" onClick={() => setIsModalOpen(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleSavePlan}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Plan Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Monthly Saree Box, VIP Styling Pass..."
                    value={planForm.name}
                    onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    rows="2"
                    placeholder="Describe plan perks, deliverables, frequency..."
                    value={planForm.description}
                    onChange={(e) => setPlanForm({ ...planForm, description: e.target.value })}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Associated Product *</label>
                    <select
                      required
                      value={planForm.product_id}
                      onChange={(e) => {
                        setPlanForm({ ...planForm, product_id: e.target.value, variant_id: '' });
                      }}
                    >
                      <option value="">-- Select Product --</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.product_type}) - ₹{p.sales_price}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Variant (Optional)</label>
                    <select
                      value={planForm.variant_id}
                      onChange={(e) => setPlanForm({ ...planForm, variant_id: e.target.value })}
                      disabled={availableVariants.length === 0}
                    >
                      <option value="">
                        {availableVariants.length === 0 ? '(No variants for this product)' : '(All / Base Product)'}
                      </option>
                      {availableVariants.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.name} (+₹{v.additional_price})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Billing Period *</label>
                    <select
                      value={planForm.billing_period}
                      onChange={(e) => setPlanForm({ ...planForm, billing_period: e.target.value })}
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="yearly">Yearly</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Plan Price (₹) *</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      placeholder="1150.00"
                      value={planForm.price}
                      onChange={(e) => setPlanForm({ ...planForm, price: e.target.value })}
                    />
                  </div>

                  <div className="form-group">
                    <label>Minimum Quantity</label>
                    <input
                      type="number"
                      min="1"
                      required
                      value={planForm.min_quantity}
                      onChange={(e) => setPlanForm({ ...planForm, min_quantity: e.target.value })}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Availability Start Date</label>
                    <input
                      type="date"
                      value={planForm.start_date}
                      onChange={(e) => setPlanForm({ ...planForm, start_date: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Availability End Date</label>
                    <input
                      type="date"
                      value={planForm.end_date}
                      onChange={(e) => setPlanForm({ ...planForm, end_date: e.target.value })}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Plan Lifecycle Policies</label>
                  <div className="checkbox-grid">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={planForm.allow_pause}
                        onChange={(e) => setPlanForm({ ...planForm, allow_pause: e.target.checked })}
                      />
                      Allow subscriber to pause plan
                    </label>

                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={planForm.allow_renewal}
                        onChange={(e) => setPlanForm({ ...planForm, allow_renewal: e.target.checked })}
                      />
                      Allow plan renewal at end of cycle
                    </label>

                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={planForm.allow_early_close}
                        onChange={(e) => setPlanForm({ ...planForm, allow_early_close: e.target.checked })}
                      />
                      Allow early plan closure / cancellation
                    </label>

                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={planForm.auto_close_on_condition}
                        onChange={(e) => setPlanForm({ ...planForm, auto_close_on_condition: e.target.checked })}
                      />
                      Auto-close plan when configured conditions expire
                    </label>

                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={planForm.is_active}
                        onChange={(e) => setPlanForm({ ...planForm, is_active: e.target.checked })}
                      />
                      Plan is currently active
                    </label>
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Saving...' : editingPlan ? 'Save Changes' : 'Create Plan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
