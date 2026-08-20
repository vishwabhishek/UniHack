import React, { useState } from 'react';
import {
  ShieldCheck,
  Lock,
  Mail,
  User as UserIcon,
  AlertCircle,
  Eye,
  EyeOff,
  ArrowRight,
  Database,
  Layers,
  Sparkles,
  CheckCircle2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from './Toast';

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    try {
      if (mode === 'login') {
        await login(email, password);
        showToast('Authentication Successful', `Welcome to Unilog PIM Workbench`, 'success');
      } else {
        await register(email, password, name, role);
        showToast('Account Created', `Registered as ${role.toUpperCase()}`, 'success');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify your credentials.');
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#050811] text-slate-100 flex flex-col justify-between relative overflow-hidden font-sans select-none">
      {/* Dynamic Background Gradient Grid & Glows */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(6,182,212,0.12),transparent_50%),radial-gradient(ellipse_at_bottom_left,rgba(99,102,241,0.12),transparent_50%)] pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header */}
      <header className="relative z-10 px-6 sm:px-12 py-6 flex items-center justify-between border-b border-white/[0.06] bg-slate-950/40 backdrop-blur-md">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-glow-cyan border border-cyan-400/40">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-base font-extrabold tracking-wider text-white font-mono">UNILOG</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 font-mono font-semibold border border-cyan-500/20">
                PIM WORKBENCH
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans tracking-normal">
              Industrial Catalog Enrichment & Master Data Platform
            </p>
          </div>
        </div>

        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900/60 border border-white/[0.08] text-xs font-mono text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>ZERO-TRUST GATEWAY</span>
        </div>
      </header>

      {/* Main Authentication Container */}
      <main className="relative z-10 flex-1 flex items-center justify-center p-4 sm:p-8">
        <div className="w-full max-w-md">
          <div className="glass-panel border border-white/[0.12] rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-2xl bg-[#090D18]/90">
            
            {/* Header Badge */}
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 mb-3 shadow-glow-blue">
                <Lock className="w-6 h-6 text-cyan-400" />
              </div>
              <h2 className="text-xl font-extrabold text-white tracking-tight">
                {mode === 'login' ? 'Enterprise Sign In' : 'Create PIM Account'}
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                {mode === 'login'
                  ? 'Enter your corporate credentials to access the workbench'
                  : 'Register a new profile to access catalog enrichment and QA'}
              </p>
            </div>

            {/* Toggle Tabs */}
            <div className="flex rounded-xl bg-slate-950/80 p-1 mb-6 border border-white/[0.06] font-mono text-xs">
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setErrorMessage(null);
                }}
                className={`flex-1 py-2 rounded-lg font-bold transition-all ${
                  mode === 'login'
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-glow-cyan'
                    : 'text-slate-400 hover:text-white'
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
                className={`flex-1 py-2 rounded-lg font-bold transition-all ${
                  mode === 'register'
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-glow-cyan'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                REGISTER
              </button>
            </div>

            {/* Error Message Alert */}
            {errorMessage && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center space-x-2 font-mono animate-in fade-in">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && (
                <div>
                  <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1.5">
                    FULL NAME
                  </label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Alex Mercer"
                      className="w-full pl-10 pr-3.5 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-xs text-white placeholder-slate-400 focus:border-cyan-400 focus:outline-none transition-colors"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1.5">
                  CORPORATE EMAIL
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@unilog.com"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-xs text-white placeholder-slate-400 focus:border-cyan-400 focus:outline-none transition-colors font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1.5">
                  PASSWORD
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-10 pr-10 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-xs text-white placeholder-slate-400 focus:border-cyan-400 focus:outline-none transition-colors font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {mode === 'register' && (
                <div>
                  <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1.5">
                    ROLE & ACCESS LEVEL
                  </label>
                  <select
                    value={role}
                    onChange={(e: any) => setRole(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-950/90 border border-white/[0.08] rounded-xl text-xs text-slate-200 focus:border-cyan-400 focus:outline-none font-mono"
                  >
                    <option value="specialist">Catalog Specialist (Edit, Sandbox, Approve)</option>
                    <option value="reviewer">Data Reviewer (HITL Triage & Approvals)</option>
                    <option value="admin">Platform Administrator (Full Control)</option>
                    <option value="viewer">Auditor / Viewer (Read-Only 252-Col Inspection)</option>
                  </select>
                </div>
              )}

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full flex items-center justify-center space-x-2 py-3 bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-extrabold font-mono shadow-glow-blue transition-all disabled:opacity-50 hover:scale-[1.01]"
                >
                  <span>{isLoading ? 'AUTHENTICATING...' : mode === 'login' ? 'SIGN IN & ENTER WORKBENCH' : 'CREATE ACCOUNT & SIGN IN'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </form>

            {/* Bottom Security Note */}
            <div className="mt-6 pt-4 border-t border-white/[0.06] text-center">
              <p className="text-[10px] text-slate-400 font-mono flex items-center justify-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>OWASP PBKDF2 & RFC 7519 JWT ENCRYPTION</span>
              </p>
            </div>

          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 px-6 py-4 text-center border-t border-white/[0.06] bg-slate-950/30 text-xs text-slate-400 font-mono">
        UNILOG CIMPLIFI ENTERPRISE · 252-COLUMN INDUSTRIAL PIM ENGINE
      </footer>
    </div>
  );
};
