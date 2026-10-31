const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      let errorMessage = `Request failed with status ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((d) => d.msg || `${d.loc?.join('.')} error`).join(', ');
          } else {
            errorMessage = errorData.detail;
          }
        }
      } catch {
        // use fallback message
      }
      throw new Error(errorMessage);
    }
    return await res.json();
  } catch (err) {
    if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      throw new Error(
        'Unable to reach the backend API server. Ensure FastAPI is running on http://localhost:8000',
        { cause: err }
      );
    }
    throw err;
  }
}

export const api = {
  // System Health
  checkHealth: async () => {
    try {
      const res = await fetch('http://localhost:8000/');
      return await res.json();
    } catch {
      return null;
    }
  },

  // Products
  getProducts: () => request('/products'),
  getProduct: (id) => request(`/products/${id}`),
  createProduct: (data) => request('/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id, data) => request(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id) => request(`/products/${id}`, { method: 'DELETE' }),

  // Variants
  getProductVariants: (productId) => request(`/products/${productId}/variants`),
  createVariant: (productId, data) => request(`/products/${productId}/variants`, { method: 'POST', body: JSON.stringify(data) }),
  updateVariant: (variantId, data) => request(`/variants/${variantId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteVariant: (variantId) => request(`/variants/${variantId}`, { method: 'DELETE' }),

  // Subscription Plans
  getPlans: (params = {}) => {
    const query = new URLSearchParams();
    if (params.product_id) query.append('product_id', params.product_id);
    if (params.billing_period) query.append('billing_period', params.billing_period);
    if (params.is_active !== undefined && params.is_active !== '') query.append('is_active', params.is_active);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request(`/plans${qs}`);
  },
  getPlan: (id) => request(`/plans/${id}`),
  createPlan: (data) => request('/plans', { method: 'POST', body: JSON.stringify(data) }),
  updatePlan: (id, data) => request(`/plans/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  togglePlanStatus: (id, isActive) => request(`/plans/${id}/status?is_active=${isActive}`, { method: 'PATCH' }),
  deletePlan: (id) => request(`/plans/${id}`, { method: 'DELETE' }),

  // Discounts
  getDiscounts: (params = {}) => {
    const query = new URLSearchParams();
    if (params.is_active !== undefined && params.is_active !== '') query.append('is_active', params.is_active);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request(`/discounts${qs}`);
  },
  getDiscount: (id) => request(`/discounts/${id}`),
  createDiscount: (data) => request('/discounts', { method: 'POST', body: JSON.stringify(data) }),
  updateDiscount: (id, data) => request(`/discounts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  toggleDiscountStatus: (id, isActive) => request(`/discounts/${id}/status?is_active=${isActive}`, { method: 'PATCH' }),
  deleteDiscount: (id) => request(`/discounts/${id}`, { method: 'DELETE' }),
  validateDiscount: (data) => request('/discounts/validate', { method: 'POST', body: JSON.stringify(data) }),

  // Taxes
  getTaxes: (params = {}) => {
    const query = new URLSearchParams();
    if (params.applicable_scope) query.append('applicable_scope', params.applicable_scope);
    if (params.is_active !== undefined && params.is_active !== '') query.append('is_active', params.is_active);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request(`/taxes${qs}`);
  },
  getTax: (id) => request(`/taxes/${id}`),
  createTax: (data) => request('/taxes', { method: 'POST', body: JSON.stringify(data) }),
  updateTax: (id, data) => request(`/taxes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  toggleTaxStatus: (id, isActive) => request(`/taxes/${id}/status?is_active=${isActive}`, { method: 'PATCH' }),
  deleteTax: (id) => request(`/taxes/${id}`, { method: 'DELETE' }),
  calculateTax: (data) => request('/taxes/calculate', { method: 'POST', body: JSON.stringify(data) }),
};
