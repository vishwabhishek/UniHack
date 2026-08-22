import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from './Toast';
import { AlertCircle, Eye, EyeOff, ShieldCheck, UserCheck, CheckCircle2, Sparkles, Key } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, register, isLoading } = useAuth();
  const { showToast } = useToast();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<'admin' | 'specialist' | 'reviewer' | 'viewer'>('specialist');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const demoAccounts = [
    {
      roleName: 'Admin',
      email: 'admin@unilog.com',
      password: 'Admin@123456',
      role: 'admin',
      desc: 'Full Master Access & Config',
      badgeClass: 'border-cyan-500/40 text-cyan-400 bg-cyan-950/40'
    },
    {
      roleName: 'Specialist',
      email: 'specialist@unilog.com',
      password: 'Specialist@123456',
      role: 'specialist',
      desc: 'Catalog Curation & Sandbox',
      badgeClass: 'border-blue-500/40 text-blue-400 bg-blue-950/40'
    },
    {
      roleName: 'Reviewer',
      email: 'reviewer@unilog.com',
      password: 'Reviewer@123456',
      role: 'reviewer',
      desc: 'Triage Queue & Exceptions',
      badgeClass: 'border-emerald-500/40 text-emerald-400 bg-emerald-950/40'
    },
    {
      roleName: 'Viewer',
      email: 'viewer@unilog.com',
      password: 'Viewer@123456',
      role: 'viewer',
      desc: 'Read-Only Delivery Inspector',
      badgeClass: 'border-zinc-600 text-zinc-400 bg-zinc-900'
    }
  ];

  const handleQuickLogin = async (acc: typeof demoAccounts[0]) => {
    setMode('login');
    setEmail(acc.email);
    setPassword(acc.password);
    setErrorMessage(null);
    try {
      await login(acc.email, acc.password);
      showToast('Authenticated', `Signed in as ${acc.roleName} (${acc.email})`, 'success');
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please check credentials.');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    try {
      if (mode === 'login') {
        await login(email, password);
        showToast('Authenticated', 'Welcome back to Unilog PIM Workbench', 'success');
      } else {
        await register(email, password, name, role);
        showToast('Account Created', `Registered and saved profile as ${role.toUpperCase()}`, 'success');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify credentials.');
    }
  };

  return (
    <div className="min-h-screen w-full bg-[var(--bg)] text-[var(--text-primary)] font-sans selection:bg-[var(--cyan)] selection:text-[var(--bg)] flex flex-col justify-center">
      <div className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] min-h-screen border-b lg:border-b-0">
        
        {/* Left Side: Pipeline preview & sample */}
        <div className="p-8 sm:p-12 lg:p-14 bg-[radial-gradient(circle_at_15%_20%,rgba(69,224,214,0.06),transparent_45%)] bg-[var(--bg)] flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-[var(--border)]">
          <div>
            {/* Brand Mark */}
            <div className="flex items-center gap-2.5">
              <div className="w-2.5 h-2.5 rounded-[2px] bg-[var(--cyan)]" />
              <div>
                <div className="font-mono text-sm tracking-[0.06em] text-[var(--text-primary)] font-medium">
                  UNIHACK SIMPLIFI
                </div>
                <div className="text-xs text-[var(--text-muted)] tracking-[0.03em] mt-0.5">
                  Industrial product intelligence &amp; evidence workbench
                </div>
              </div>
            </div>

            {/* 7-Stage Enrichment Pipeline */}
            <div className="my-10">
              <div className="text-[11px] text-[var(--text-muted)] uppercase tracking-[0.08em] mb-4 font-mono">
                7-stage enrichment pipeline
              </div>
              <div className="pipeline-row">
                <div className="pl-stage lit"><div className="pl-node" /></div>
                <div className="pl-stage lit"><div className="pl-node" /></div>
                <div className="pl-stage lit"><div className="pl-node" /></div>
                <div className="pl-stage lit"><div className="pl-node" /></div>
                <div className="pl-stage lit"><div className="pl-node" /></div>
                <div className="pl-stage lit"><div className="pl-node" /></div>
                <div className="pl-stage lit"><div className="pl-node" /></div>
              </div>
              <div className="pl-labels">
                <span>sanitize</span>
                <span>resolve</span>
                <span>taxonomy</span>
                <span>extract</span>
                <span>uom</span>
                <span>describe</span>
                <span>deliver</span>
              </div>
            </div>

            {/* Sample Record Preview */}
            <div className="sample-record">
              <div className="raw">"U008LFA 1/2IN BRASS PUSH COUPLING -- No Brand -- 200PSI LEAD FREE"</div>
              <div className="sample-arrow">↓ official manufacturer evidence resolved &amp; normalized</div>
              <div className="clean">SharkBite® U008LFA 1/2 in Brass Push-to-Connect Straight Coupling 200 psi</div>
            </div>
          </div>

          <div className="text-xs text-[var(--text-muted)] mt-8 font-mono">
            252-column delivery schema · Field-level provenance · 0% hallucinated attributes
          </div>
        </div>

        {/* Right Side: Auth Card */}
        <div className="flex items-center justify-center p-6 sm:p-10 lg:p-12 bg-[var(--bg)]">
          <div className="w-full max-w-[420px] bg-[var(--surface-glass)] backdrop-blur-[14px] border border-[var(--border-strong)] rounded-xl p-8 shadow-2xl space-y-5">
            
            <div>
              <h1 className="text-xl font-semibold mb-1 text-[var(--text-primary)]">
                {mode === 'login' ? 'Sign in' : 'Create Account'}
              </h1>
              <p className="text-[13px] text-[var(--text-secondary)]">
                {mode === 'login' ? 'Access the catalog intelligence workbench' : 'Register a new profile (saved persistently)'}
              </p>
            </div>

            {/* Quick 1-Click Demo Profiles */}
            <div className="p-3 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-2">
              <div className="flex items-center justify-between text-[10px] font-mono font-bold uppercase text-[var(--text-muted)]">
                <span className="flex items-center gap-1 text-[var(--cyan)]">
                  <Sparkles className="w-3 h-3" />
                  <span>1-CLICK DEMO ROLES</span>
                </span>
                <span>CLICK TO SIGN IN</span>
              </div>
              <div className="grid grid-cols-2 gap-1.5 font-mono text-xs">
                {demoAccounts.map((acc) => (
                  <button
                    key={acc.role}
                    type="button"
                    onClick={() => handleQuickLogin(acc)}
                    className={`px-2.5 py-1.5 rounded border text-left transition-all hover:scale-[1.02] cursor-pointer flex flex-col justify-between ${acc.badgeClass}`}
                  >
                    <span className="font-bold flex items-center justify-between">
                      <span>{acc.roleName}</span>
                      <Key className="w-3 h-3 opacity-60" />
                    </span>
                    <span className="text-[9px] opacity-75 truncate">{acc.email}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Switcher Tab */}
            <div className="flex rounded-md bg-[var(--surface-1)] p-1 border border-[var(--border-strong)] font-mono text-xs">
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setErrorMessage(null);
                }}
                className={`flex-1 py-1.5 rounded transition-all cursor-pointer ${
                  mode === 'login'
                    ? 'bg-[var(--cyan)] text-[#06201D] font-semibold'
                    : 'text-[var(--text-secondary)] hover:text-white'
                }`}
              >
                SIGN IN
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('register');
                  setErrorMessage(null);
                }}
                className={`flex-1 py-1.5 rounded transition-all cursor-pointer ${
                  mode === 'register'
                    ? 'bg-[var(--cyan)] text-[#06201D] font-semibold'
                    : 'text-[var(--text-secondary)] hover:text-white'
                }`}
              >
                REGISTER NEW
              </button>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="p-2.5 bg-[var(--red-bg)] border border-[var(--red)] rounded-md text-[var(--red)] text-xs flex items-center gap-2 font-mono">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3.5">
              {mode === 'register' && (
                <div>
                  <label className="block text-xs text-[var(--text-secondary)] mb-1 font-mono">Full Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Abhishek Vishwakarma"
                    className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 py-2 text-[13px] text-[var(--text-primary)] focus:outline-none focus:border-[var(--cyan)]"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs text-[var(--text-secondary)] mb-1 font-mono">Corporate Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@unilog.com"
                  className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 py-2 text-[13px] text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--cyan)]"
                />
              </div>

              <div>
                <label className="block text-xs text-[var(--text-secondary)] mb-1 font-mono">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Admin@123456"
                    className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 pr-9 py-2 text-[13px] text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--cyan)]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-white cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {mode === 'register' && (
                <div>
                  <label className="block text-xs text-[var(--text-secondary)] mb-1 font-mono">Role Profile</label>
                  <select
                    value={role}
                    onChange={(e: any) => setRole(e.target.value)}
                    className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 py-2 text-[13px] text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--cyan)] cursor-pointer"
                  >
                    <option value="specialist">Specialist (Curate, Sandbox, Approve)</option>
                    <option value="reviewer">Reviewer (Triage & Approvals)</option>
                    <option value="admin">Administrator (Full Master Access)</option>
                    <option value="viewer">Viewer (Read-Only 252-Col Inspection)</option>
                  </select>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-[var(--cyan)] text-[#06201D] font-bold text-[13px] font-mono rounded-md py-2.5 mt-2 hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer shadow-xs"
              >
                {isLoading ? 'VERIFYING...' : mode === 'login' ? 'SIGN IN' : 'CREATE PERSISTENT ACCOUNT'}
              </button>
            </form>

            <div className="pt-3 border-t border-[var(--border)] text-[11px] text-[var(--text-muted)] font-mono flex items-center justify-between">
              <span>Saved in <code className="text-[var(--cyan)]">data/users.json</code></span>
              <span className="text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>JWT RBAC</span>
              </span>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
};
