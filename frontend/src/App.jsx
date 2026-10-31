import { useState, useEffect } from 'react';
import { api } from './api';
import ProductsTab from './components/ProductsTab';
import PlansTab from './components/PlansTab';
import DiscountsTab from './components/DiscountsTab';
import TaxesTab from './components/TaxesTab';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('products');
  const [notification, setNotification] = useState(null);
  const [apiHealth, setApiHealth] = useState({ online: false, checking: true });

  useEffect(() => {
    let isMounted = true;
    api.checkHealth()
      .then((res) => {
        if (isMounted) {
          setApiHealth({ online: Boolean(res?.status === 'online'), checking: false });
        }
      })
      .catch(() => {
        if (isMounted) {
          setApiHealth({ online: false, checking: false });
        }
      });

    const interval = setInterval(() => {
      api.checkHealth()
        .then((res) => {
          if (isMounted) {
            setApiHealth({ online: Boolean(res?.status === 'online'), checking: false });
          }
        })
        .catch(() => {
          if (isMounted) {
            setApiHealth({ online: false, checking: false });
          }
        });
    }, 30000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleNotification = (message, type = 'info') => {
    setNotification({ message, type, id: Date.now() });
    setTimeout(() => {
      setNotification((prev) => (prev?.message === message ? null : prev));
    }, 5000);
  };

  return (
    <div className="app-layout">
      {/* Top Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-logo">🛡️</div>
          <div>
            <h1 className="brand-title">SubSentry AI</h1>
            <p className="brand-subtitle">Catalog, Plan Configuration & Pricing Engine</p>
          </div>
        </div>

        <div className="header-status">
          <div className={`status-pill ${apiHealth.online ? 'status-online' : 'status-offline'}`}>
            <span className="status-dot"></span>
            {apiHealth.checking
              ? 'Connecting...'
              : apiHealth.online
              ? 'Backend & PostgreSQL Connected'
              : 'Backend Offline (FastAPI Port 8000)'}
          </div>
          <span className="badge badge-team">Person 2 Module</span>
        </div>
      </header>

      {/* Global Toast / Notification */}
      {notification && (
        <div className={`notification-toast toast-${notification.type}`}>
          <span>{notification.message}</span>
          <button className="toast-close" onClick={() => setNotification(null)}>
            ✕
          </button>
        </div>
      )}

      {/* Main Navigation Tabs */}
      <nav className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'products' ? 'active' : ''}`}
          onClick={() => setActiveTab('products')}
        >
          <span className="tab-icon">📦</span>
          <span>Products & Variants</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'plans' ? 'active' : ''}`}
          onClick={() => setActiveTab('plans')}
        >
          <span className="tab-icon">📅</span>
          <span>Subscription Plans</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'discounts' ? 'active' : ''}`}
          onClick={() => setActiveTab('discounts')}
        >
          <span className="tab-icon">🏷️</span>
          <span>Discount Rules</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'taxes' ? 'active' : ''}`}
          onClick={() => setActiveTab('taxes')}
        >
          <span className="tab-icon">🧾</span>
          <span>Tax Rules</span>
        </button>
      </nav>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'products' && <ProductsTab onNotification={handleNotification} />}
        {activeTab === 'plans' && <PlansTab onNotification={handleNotification} />}
        {activeTab === 'discounts' && <DiscountsTab onNotification={handleNotification} />}
        {activeTab === 'taxes' && <TaxesTab onNotification={handleNotification} />}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div>
          <strong>Subscription Management System</strong> &bull; Person 2 Module: Products, Variants, Plan Config, Discounts & Taxes
        </div>
        <div className="footer-git-info">
          Git Branch: <code>Liya-Roy</code> &bull; PostgreSQL: <code>subscription_management</code>
        </div>
      </footer>
    </div>
  );
}
