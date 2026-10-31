import React from "react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ShieldCheck, ArrowRight, Mail, Lock, UserRound } from "lucide-react";
import { api, saveSession } from "../api";

function Shell({ title, subtitle, children }) {
  return <main className="auth-shell">
    <div className="auth-glow glow-one" /><div className="auth-glow glow-two" />
    <section className="auth-card">
      <Link to="/login" className="brand"><span className="brand-icon"><ShieldCheck size={21}/></span><span>SubSentry <b>AI</b></span></Link>
      <div className="auth-heading"><p className="eyebrow">BRIGHTLOOP SOFTWARE</p><h1>{title}</h1><p>{subtitle}</p></div>
      {children}
      <p className="auth-foot">Secure subscription operations · Phase 1</p>
    </section>
  </main>;
}

function Field({ label, icon: Icon, ...props }) {
  return <label className="field"><span>{label}</span><div className="input-wrap"><Icon size={17}/><input {...props}/></div></label>;
}

export function LoginPage() {
  const [form, setForm] = useState({email:"", password:""});
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const update = e => setForm({...form, [e.target.name]:e.target.value});
  async function submit(e) {
    e.preventDefault(); setError(""); setBusy(true);
    try { const data = await api("/api/auth/login", {method:"POST", body:JSON.stringify(form)}); saveSession(data); navigate("/dashboard"); }
    catch(err) { setError(err.message); } finally { setBusy(false); }
  }
  return <Shell title="Welcome back." subtitle="Sign in to your subscription operations workspace.">
    <form onSubmit={submit} className="auth-form">
      <Field label="Work email" icon={Mail} name="email" type="email" placeholder="you@company.com" value={form.email} onChange={update} required/>
      <Field label="Password" icon={Lock} name="password" type="password" placeholder="Enter your password" value={form.password} onChange={update} required/>
      <div className="form-meta"><Link to="/forgot-password">Forgot password?</Link></div>
      {error && <p className="error">{error}</p>}
      <button className="primary-btn" disabled={busy}>{busy ? "Signing in…" : "Sign in"} <ArrowRight size={17}/></button>
    </form>
    <p className="switch-auth">New customer? <Link to="/register">Create an account</Link></p>
  </Shell>;
}

export function RegisterPage() {
  const [form, setForm] = useState({full_name:"", email:"", password:""});
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const update = e => setForm({...form, [e.target.name]:e.target.value});
  async function submit(e) {
    e.preventDefault(); setError(""); setBusy(true);
    try { const data = await api("/api/auth/register", {method:"POST", body:JSON.stringify(form)}); saveSession(data); navigate("/dashboard"); }
    catch(err) { setError(err.message); } finally { setBusy(false); }
  }
  return <Shell title="Create your account." subtitle="Get started with Brightloop's subscription platform.">
    <form onSubmit={submit} className="auth-form">
      <Field label="Full name" icon={UserRound} name="full_name" placeholder="Your full name" value={form.full_name} onChange={update} required/>
      <Field label="Email address" icon={Mail} name="email" type="email" placeholder="you@example.com" value={form.email} onChange={update} required/>
      <Field label="Password" icon={Lock} name="password" type="password" placeholder="Create a strong password" value={form.password} onChange={update} required minLength="9"/>
      <p className="hint">More than 8 characters, including uppercase, lowercase and a special character.</p>
      {error && <p className="error">{error}</p>}
      <button className="primary-btn" disabled={busy}>{busy ? "Creating account…" : "Create customer account"} <ArrowRight size={17}/></button>
    </form>
    <p className="switch-auth">Already registered? <Link to="/login">Sign in</Link></p>
  </Shell>;
}

export function ForgotPasswordPage() {
  const [email,setEmail]=useState(""); const [message,setMessage]=useState(""); const [error,setError]=useState("");
  async function submit(e){e.preventDefault();setError("");setMessage("");try{const d=await api("/api/auth/forgot-password",{method:"POST",body:JSON.stringify({email})});setMessage(d.message);}catch(err){setError(err.message);}}
  return <Shell title="Reset your password." subtitle="We'll send a secure reset link if the account exists.">
    <form onSubmit={submit} className="auth-form">
      <Field label="Registered email" icon={Mail} name="email" type="email" placeholder="you@example.com" value={email} onChange={e=>setEmail(e.target.value)} required/>
      {message && <p className="success">{message}</p>}{error && <p className="error">{error}</p>}
      <button className="primary-btn">Send reset link <ArrowRight size={17}/></button>
    </form><p className="switch-auth"><Link to="/login">Back to sign in</Link></p>
  </Shell>;
}

export function ResetPasswordPage() {
  const [params]=useSearchParams(); const [password,setPassword]=useState(""); const [message,setMessage]=useState(""); const [error,setError]=useState("");
  async function submit(e){e.preventDefault();setError("");setMessage("");try{const d=await api("/api/auth/reset-password",{method:"POST",body:JSON.stringify({token:params.get("token"),new_password:password})});setMessage(d.message);}catch(err){setError(err.message);}}
  return <Shell title="Choose a new password." subtitle="Your reset link is valid for 30 minutes and can be used once.">
    <form onSubmit={submit} className="auth-form">
      <Field label="New password" icon={Lock} name="password" type="password" placeholder="Enter a strong password" value={password} onChange={e=>setPassword(e.target.value)} required minLength="9"/>
      <p className="hint">More than 8 characters, including uppercase, lowercase and a special character.</p>
      {message && <p className="success">{message} <Link to="/login">Sign in</Link></p>}{error && <p className="error">{error}</p>}
      <button className="primary-btn">Update password <ArrowRight size={17}/></button>
    </form>
  </Shell>;
}
