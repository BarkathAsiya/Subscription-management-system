import React from 'react';
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, Users, UserRound, BriefcaseBusiness, LogOut, Plus, RefreshCw, LockKeyhole } from "lucide-react";
import { api, clearSession, getSavedUser } from "../api";

export default function Dashboard() {
  const user = getSavedUser(); const navigate = useNavigate();
  const [profile,setProfile]=useState(user); const [users,setUsers]=useState([]);
  const [showCreate,setShowCreate]=useState(false); const [form,setForm]=useState({full_name:"",email:"",password:""});
  const [notice,setNotice]=useState(""); const [error,setError]=useState(""); const [loading,setLoading]=useState(false);
  async function load() {
    setLoading(true); setError("");
    try {
      const me = await api("/api/auth/me"); setProfile(me);
      if (me.role === "admin") setUsers(await api("/api/admin/users"));
      if (me.role === "customer") await api("/api/customer/me");
    } catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }
  useEffect(()=>{load();},[]);
  function logout(){clearSession();navigate("/login");}
  async function createStaff(e){
    e.preventDefault();setNotice("");setError("");
    try { await api("/api/admin/staff",{method:"POST",body:JSON.stringify(form)});setNotice("Staff account created successfully.");setForm({full_name:"",email:"",password:""});setShowCreate(false);load(); }
    catch(e){setError(e.message);}
  }
  const roleLabel = profile?.role?.toUpperCase() || "USER";
  return <main className="dashboard">
    <header className="topbar">
      <div className="brand"><span className="brand-icon"><ShieldCheck size={21}/></span><span>SubSentry <b>AI</b></span></div>
      <div className="top-actions"><span className="status-dot"/> <span className="signed-in">Signed in</span><button className="logout-btn" onClick={logout}><LogOut size={16}/> Logout</button></div>
    </header>
    <div className="dash-content">
      <div className="welcome-row"><div><p className="eyebrow">BRIGHTLOOP SOFTWARE / WORKSPACE</p><h1>Good to see you, {profile?.full_name?.split(" ")[0] || "there"}.</h1><p className="muted">Your secure subscription operations workspace.</p></div><span className={`role-pill ${profile?.role}`}>{roleLabel} ACCESS</span></div>
      {notice && <p className="success banner">{notice}</p>}{error && <p className="error banner">{error}</p>}
      <section className="stat-grid">
        <article className="stat-card"><span className="stat-icon"><UserRound/></span><p>Account</p><h2>{profile?.full_name || "—"}</h2><small>Registered profile</small></article>
        <article className="stat-card"><span className="stat-icon"><ShieldCheck/></span><p>Access level</p><h2>{roleLabel}</h2><small>Role-based permissions</small></article>
        <article className="stat-card"><span className="stat-icon"><LockKeyhole/></span><p>Account status</p><h2>{profile?.is_active ? "Active" : "Inactive"}</h2><small>Authentication status</small></article>
      </section>

      {profile?.role === "admin" && <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">ADMIN CONTROL</p><h2>Team & account management</h2><p className="muted">Only Admin accounts can provision internal Staff access.</p></div><button className="primary-btn compact" onClick={()=>setShowCreate(!showCreate)}><Plus size={16}/> Create staff</button></div>
        {showCreate && <form className="staff-form" onSubmit={createStaff}>
          <input placeholder="Staff full name" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})} required/>
          <input type="email" placeholder="Staff email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} required/>
          <input type="password" placeholder="Temporary password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} minLength="9" required/>
          <button className="primary-btn compact">Create account</button>
          <p className="hint full">Password must be longer than 8 characters and include uppercase, lowercase and special characters.</p>
        </form>}
        <div className="table-wrap"><table><thead><tr><th>NAME</th><th>EMAIL</th><th>ROLE</th><th>STATUS</th></tr></thead><tbody>
          {users.map(u=><tr key={u.id}><td>{u.full_name}</td><td>{u.email}</td><td><span className={`mini-role ${u.role}`}>{u.role}</span></td><td><span className="active-state">{u.is_active?"Active":"Inactive"}</span></td></tr>)}
          {!users.length && <tr><td colSpan="4">No accounts to display.</td></tr>}
        </tbody></table></div>
        <button className="text-btn" onClick={load}><RefreshCw size={14}/> Refresh list</button>
      </section>}

      {profile?.role === "staff" && <section className="panel role-panel"><span className="large-icon"><BriefcaseBusiness/></span><div><p className="eyebrow">INTERNAL STAFF PORTAL</p><h2>Day-to-day operations access</h2><p className="muted">You are signed in as internal Staff. Admin-only account provisioning and system-wide controls are restricted.</p></div></section>}

      {profile?.role === "customer" && <section className="panel role-panel"><span className="large-icon"><UserRound/></span><div><p className="eyebrow">CUSTOMER PORTAL</p><h2>Your account is private</h2><p className="muted">This portal is scoped to your own account. Subscription and invoice views will be added in the next implementation phases.</p><div className="profile-line"><span>Registered email</span><b>{profile?.email}</b></div></div></section>}
      <div style={{display:"flex",justifyContent:"center",marginTop:24}}><button className="primary-btn compact" onClick={()=>navigate("/subscriptions")}>Open subscriptions & invoices</button></div>
      <footer className="dash-footer">SubSentry AI <span>•</span> Identity & Access + Billing Operations</footer>
    </div>
  </main>;
}

