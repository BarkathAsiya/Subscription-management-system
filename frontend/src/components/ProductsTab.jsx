import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';

export default function ProductsTab({ onNotification }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  // Modals state
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState({
    name: '',
    product_type: 'Physical',
    sales_price: '',
    cost_price: '',
    notes: '',
  });

  // Variant management state
  const [activeProductForVariants, setActiveProductForVariants] = useState(null);
  const [variantForm, setVariantForm] = useState({ name: '', additional_price: '' });
  const [editingVariant, setEditingVariant] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getProducts();
      setProducts(data);
      setActiveProductForVariants((prev) => {
        if (!prev) return null;
        return data.find((p) => p.id === prev.id) || null;
      });
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }, [onNotification]);

  useEffect(() => {
    let isMounted = true;
    api.getProducts()
      .then((data) => {
        if (isMounted) {
          setProducts(data);
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

  const handleOpenProductModal = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setProductForm({
        name: product.name,
        product_type: product.product_type,
        sales_price: product.sales_price,
        cost_price: product.cost_price,
        notes: product.notes || '',
      });
    } else {
      setEditingProduct(null);
      setProductForm({
        name: '',
        product_type: 'Physical',
        sales_price: '',
        cost_price: '',
        notes: '',
      });
    }
    setIsProductModalOpen(true);
  };

  const handleSaveProduct = async (e) => {
    e.preventDefault();
    if (!productForm.name.trim()) {
      onNotification('Product name is required', 'error');
      return;
    }
    const salesPrice = parseFloat(productForm.sales_price);
    const costPrice = parseFloat(productForm.cost_price);
    if (isNaN(salesPrice) || salesPrice < 0 || isNaN(costPrice) || costPrice < 0) {
      onNotification('Prices must be valid non-negative numbers', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name: productForm.name.trim(),
        product_type: productForm.product_type,
        sales_price: salesPrice,
        cost_price: costPrice,
        notes: productForm.notes.trim(),
      };

      if (editingProduct) {
        await api.updateProduct(editingProduct.id, payload);
        onNotification(`Product "${payload.name}" updated successfully!`, 'success');
      } else {
        await api.createProduct(payload);
        onNotification(`Product "${payload.name}" created successfully!`, 'success');
      }
      setIsProductModalOpen(false);
      await loadProducts();
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteProduct = async (product) => {
    if (!window.confirm(`Are you sure you want to delete product "${product.name}" and all its variants?`)) {
      return;
    }
    try {
      await api.deleteProduct(product.id);
      onNotification(`Product "${product.name}" deleted successfully`, 'success');
      if (activeProductForVariants?.id === product.id) {
        setActiveProductForVariants(null);
      }
      await loadProducts();
    } catch (err) {
      onNotification(err.message, 'error');
    }
  };

  const handleSaveVariant = async (e) => {
    e.preventDefault();
    if (!variantForm.name.trim()) {
      onNotification('Variant name is required', 'error');
      return;
    }
    const addPrice = parseFloat(variantForm.additional_price);
    if (isNaN(addPrice) || addPrice < 0) {
      onNotification('Additional price must be a valid non-negative number', 'error');
      return;
    }

    setSubmitting(true);
    try {
      if (editingVariant) {
        await api.updateVariant(editingVariant.id, {
          name: variantForm.name.trim(),
          additional_price: addPrice,
        });
        onNotification(`Variant updated successfully!`, 'success');
        setEditingVariant(null);
      } else {
        await api.createVariant(activeProductForVariants.id, {
          name: variantForm.name.trim(),
          additional_price: addPrice,
        });
        onNotification(`Variant added to ${activeProductForVariants.name}!`, 'success');
      }
      setVariantForm({ name: '', additional_price: '' });
      await loadProducts();
    } catch (err) {
      onNotification(err.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteVariant = async (variantId, variantName) => {
    if (!window.confirm(`Delete variant "${variantName}"?`)) return;
    try {
      await api.deleteVariant(variantId);
      onNotification(`Variant "${variantName}" deleted`, 'success');
      await loadProducts();
    } catch (err) {
      onNotification(err.message, 'error');
    }
  };

  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.product_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.notes && p.notes.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = filterType === 'all' || p.product_type.toLowerCase() === filterType.toLowerCase();
    return matchesSearch && matchesType;
  });

  return (
    <div className="tab-container">
      <div className="tab-header">
        <div>
          <h2>Product Management & Variants</h2>
          <p className="tab-subtitle">
            Manage your physical and service catalog, configure product variants, and calculate final retail prices.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => handleOpenProductModal()}>
          + Add New Product
        </button>
      </div>

      <div className="filter-bar">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search products by name, type, notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label>Type:</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="all">All Types</option>
            <option value="Physical">Physical</option>
            <option value="Service">Service</option>
            <option value="Digital">Digital</option>
          </select>
        </div>
        <button className="btn btn-secondary" onClick={loadProducts} title="Refresh">
          ↻ Refresh
        </button>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading products from PostgreSQL...</p>
        </div>
      ) : filteredProducts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📦</div>
          <h3>No products found</h3>
          <p>Get started by adding your first product.</p>
          <button className="btn btn-primary" onClick={() => handleOpenProductModal()}>
            + Add Product
          </button>
        </div>
      ) : (
        <div className="products-grid">
          {filteredProducts.map((p) => (
            <div key={p.id} className="product-card">
              <div className="product-card-header">
                <div>
                  <span className={`badge badge-${p.product_type.toLowerCase()}`}>{p.product_type}</span>
                  <h3 className="product-title">{p.name}</h3>
                </div>
                <div className="product-actions">
                  <button className="btn-icon" title="Edit Product" onClick={() => handleOpenProductModal(p)}>
                    ✏️
                  </button>
                  <button className="btn-icon btn-danger-icon" title="Delete Product" onClick={() => handleDeleteProduct(p)}>
                    🗑️
                  </button>
                </div>
              </div>

              <div className="product-pricing">
                <div className="price-box">
                  <span className="price-label">Sales Price</span>
                  <span className="price-value">₹{p.sales_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="price-box">
                  <span className="price-label">Cost Price</span>
                  <span className="price-value-sub">₹{p.cost_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>

              {p.notes && <p className="product-notes">{p.notes}</p>}

              <div className="product-card-footer">
                <span className="variants-count">
                  {p.variants?.length || 0} Variant{(p.variants?.length || 0) === 1 ? '' : 's'}
                </span>
                <button
                  className="btn btn-outline"
                  onClick={() => {
                    setActiveProductForVariants(p);
                    setEditingVariant(null);
                    setVariantForm({ name: '', additional_price: '' });
                  }}
                >
                  Manage Variants ⚙️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Product Create/Edit Modal */}
      {isProductModalOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h3>{editingProduct ? 'Edit Product' : 'Create New Product'}</h3>
              <button className="btn-close" onClick={() => setIsProductModalOpen(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleSaveProduct}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Product Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Cotton Saree"
                    value={productForm.name}
                    onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Product Type *</label>
                  <select
                    value={productForm.product_type}
                    onChange={(e) => setProductForm({ ...productForm, product_type: e.target.value })}
                  >
                    <option value="Physical">Physical Product</option>
                    <option value="Service">Service</option>
                    <option value="Digital">Digital</option>
                  </select>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Sales Price (₹) *</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      placeholder="1000.00"
                      value={productForm.sales_price}
                      onChange={(e) => setProductForm({ ...productForm, sales_price: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Cost Price (₹) *</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      placeholder="700.00"
                      value={productForm.cost_price}
                      onChange={(e) => setProductForm({ ...productForm, cost_price: e.target.value })}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Notes & Description</label>
                  <textarea
                    rows="3"
                    placeholder="Details about fabric, material, specifications..."
                    value={productForm.notes}
                    onChange={(e) => setProductForm({ ...productForm, notes: e.target.value })}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setIsProductModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Saving...' : editingProduct ? 'Save Changes' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Variant Management Modal */}
      {activeProductForVariants && (
        <div className="modal-backdrop">
          <div className="modal modal-lg">
            <div className="modal-header">
              <div>
                <h3>Variants for: {activeProductForVariants.name}</h3>
                <p className="modal-subtitle">
                  Base Price: <strong>₹{activeProductForVariants.sales_price.toFixed(2)}</strong>
                </p>
              </div>
              <button className="btn-close" onClick={() => setActiveProductForVariants(null)}>
                ✕
              </button>
            </div>

            <div className="modal-body">
              {/* Add / Edit Variant Form */}
              <div className="variant-form-card">
                <h4>{editingVariant ? 'Edit Variant' : 'Add New Variant'}</h4>
                <form onSubmit={handleSaveVariant} className="variant-form">
                  <div className="form-group">
                    <label>Variant Name *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Red Zari Border, Size XL..."
                      value={variantForm.name}
                      onChange={(e) => setVariantForm({ ...variantForm, name: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Additional Price (₹) *</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      placeholder="200.00"
                      value={variantForm.additional_price}
                      onChange={(e) => setVariantForm({ ...variantForm, additional_price: e.target.value })}
                    />
                  </div>
                  <div className="form-group live-price-preview">
                    <label>Final Price Calculation:</label>
                    <div className="price-calc-badge">
                      Base (₹{activeProductForVariants.sales_price}) + Add (₹{parseFloat(variantForm.additional_price) || 0}) ={' '}
                      <strong>₹{(activeProductForVariants.sales_price + (parseFloat(variantForm.additional_price) || 0)).toFixed(2)}</strong>
                    </div>
                  </div>
                  <div className="variant-form-actions">
                    {editingVariant && (
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => {
                          setEditingVariant(null);
                          setVariantForm({ name: '', additional_price: '' });
                        }}
                      >
                        Cancel Edit
                      </button>
                    )}
                    <button type="submit" className="btn btn-primary" disabled={submitting}>
                      {submitting ? 'Saving...' : editingVariant ? 'Update Variant' : '+ Add Variant'}
                    </button>
                  </div>
                </form>
              </div>

              {/* Existing Variants Table */}
              <h4 style={{ marginTop: '1.5rem', marginBottom: '0.5rem' }}>Existing Variants</h4>
              {(!activeProductForVariants.variants || activeProductForVariants.variants.length === 0) ? (
                <p className="text-muted">No variants created yet for this product. Use the form above to add one.</p>
              ) : (
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Variant Name</th>
                        <th>Base Price</th>
                        <th>Additional Price</th>
                        <th>Final Retail Price</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeProductForVariants.variants.map((v) => (
                        <tr key={v.id}>
                          <td>#{v.id}</td>
                          <td><strong>{v.name}</strong></td>
                          <td>₹{activeProductForVariants.sales_price.toFixed(2)}</td>
                          <td className="text-success">+₹{v.additional_price.toFixed(2)}</td>
                          <td className="text-primary font-bold">
                            ₹{v.final_price?.toFixed(2) || (activeProductForVariants.sales_price + v.additional_price).toFixed(2)}
                          </td>
                          <td>
                            <div className="row-actions">
                              <button
                                className="btn btn-sm btn-outline"
                                onClick={() => {
                                  setEditingVariant(v);
                                  setVariantForm({ name: v.name, additional_price: v.additional_price });
                                }}
                              >
                                Edit
                              </button>
                              <button
                                className="btn btn-sm btn-danger"
                                onClick={() => handleDeleteVariant(v.id, v.name)}
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setActiveProductForVariants(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
