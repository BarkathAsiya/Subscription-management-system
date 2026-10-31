
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const subscriptions = [
  { name: 'Netflix', category: 'Entertainment', price: 649, cycle: 'Monthly', renewal: 'Nov 05, 2026', color: '#E50914', logo: 'N', status: 'Active' },
  { name: 'Spotify', category: 'Music', price: 119, cycle: 'Monthly', renewal: 'Nov 08, 2026', color: '#1DB954', logo: 'S', status: 'Active' },
  { name: 'Amazon Prime', category: 'Shopping & Entertainment', price: 1499, cycle: 'Yearly', renewal: 'Dec 12, 2026', color: '#00A8E0', logo: 'a', status: 'Active' },
  { name: 'YouTube Premium', category: 'Entertainment', price: 129, cycle: 'Monthly', renewal: 'Nov 15, 2026', color: '#FF0033', logo: '▶', status: 'Active' },
  { name: 'Disney+ Hotstar', category: 'Entertainment', price: 299, cycle: 'Monthly', renewal: 'Oct 10, 2026', color: '#1769FF', logo: 'D', status: 'Expired' },
]

function Dashboard() {
  const [activeMenu, setActiveMenu] = useState('Dashboard')
  const navigate = useNavigate()

  const activeSubscriptions = subscriptions.filter(item => item.status === 'Active')
  const expiredSubscriptions = subscriptions.filter(item => item.status === 'Expired')

  const monthlySpending = activeSubscriptions.reduce(
    (total, item) => total + (item.cycle === 'Yearly' ? item.price / 12 : item.price), 0
  )

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  return (
    <div className="dashboard-page">
      <aside className="dashboard-sidebar">
        <div className="dashboard-brand">
          <div className="dashboard-logo">S</div>
          <span>SubSentry <b>AI</b></span>
        </div>

        <p className="sidebar-label">MENU</p>

        {['Dashboard', 'My Subscriptions', 'Analytics', 'Settings'].map(item => (
          <button
            key={item}
            className={`sidebar-link ${activeMenu === item ? 'active' : ''}`}
            onClick={() => setActiveMenu(item)}
          >
            <span>{{
              Dashboard: '◫',
              'My Subscriptions': '▣',
              Analytics: '◷',
              Settings: '⚙'
            }[item]}</span>
            {item}
          </button>
        ))}

        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <span>✦</span>
            <b>Stay in control</b>
            <p>Manage all your subscriptions in one place.</p>
          </div>
          <button className="sidebar-link logout-button" onClick={handleLogout}>
            <span>↪</span> Logout
          </button>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <p className="dashboard-date">SATURDAY, OCTOBER 31, 2026</p>
            <h1>Welcome back! <span>✦</span></h1>
            <p className="dashboard-subtitle">Here's what's happening with your subscriptions.</p>
          </div>
          <div className="profile-avatar">U</div>
        </header>

        <section className="dashboard-stats">
          <div className="stat-card">
            <div className="stat-top"><span>Total Subscriptions</span><span>▣</span></div>
            <h2>{subscriptions.length}</h2>
            <p>All your subscriptions</p>
          </div>
          <div className="stat-card">
            <div className="stat-top"><span>Active Subscriptions</span><span>↗</span></div>
            <h2>{activeSubscriptions.length}</h2>
            <p>Currently running</p>
          </div>
          <div className="stat-card">
            <div className="stat-top"><span>Monthly Spending</span><span>₹</span></div>
            <h2>₹{monthlySpending.toFixed(0)}</h2>
            <p>Estimated monthly cost</p>
          </div>
          <div className="stat-card">
            <div className="stat-top"><span>Expired Subscriptions</span><span>◷</span></div>
            <h2>{expiredSubscriptions.length}</h2>
            <p>Need your attention</p>
          </div>
        </section>

        <section className="dashboard-section">
          <div className="section-heading">
            <div>
              <h2>My Subscriptions</h2>
              <p>Keep track of all your plans.</p>
            </div>
            <button className="view-all-button" onClick={() => setActiveMenu('My Subscriptions')}>
              View all →
            </button>
          </div>

          <div className="subscription-grid">
            {subscriptions.map(item => (
              <article className="subscription-card" key={item.name}>
                <div className="subscription-card-top">
                  <div className="subscription-brand-icon" style={{ background: item.color }}>
                    {item.logo}
                  </div>
                  <span className={`status-pill ${item.status.toLowerCase()}`}>
                    {item.status}
                  </span>
                </div>
                <h3>{item.name}</h3>
                <p className="subscription-category">{item.category}</p>
                <div className="subscription-price">
                  <strong>₹{item.price.toLocaleString('en-IN')}</strong>
                  <span>/{item.cycle === 'Yearly' ? 'year' : 'month'}</span>
                </div>
                <div className="subscription-renewal">
                  <span>{item.status === 'Active' ? 'Next renewal' : 'Expired on'}</span>
                  <b>{item.renewal}</b>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="dashboard-section">
          <div className="section-heading">
            <div>
              <h2>Upcoming Renewals</h2>
              <p>Keep an eye on your next payments.</p>
            </div>
          </div>
          <div className="renewal-list">
            {activeSubscriptions.slice().sort((a, b) => new Date(a.renewal) - new Date(b.renewal)).map(item => (
              <div className="renewal-item" key={item.name}>
                <div className="renewal-icon" style={{ background: item.color }}>{item.logo}</div>
                <div className="renewal-name">
                  <b>{item.name}</b>
                  <span>{item.renewal}</span>
                </div>
                <strong>₹{item.price.toLocaleString('en-IN')}</strong>
              </div>
            ))}
          </div>
        </section>

        <footer className="dashboard-footer">
          © 2026 SubSentry AI. Manage smarter, spend wiser.
        </footer>
      </main>
    </div>
  )
}

export default Dashboard

