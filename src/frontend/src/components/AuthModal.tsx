import React, { useState } from 'react';
import {
  X,
  Lock,
  Mail,
  User as UserIcon,
  Shield,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Sparkles,
  Zap,
  ArrowRight,
  ShieldCheck,
  Building2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from './Toast';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, closeAuthModal, login, register, demoAccounts, isLoading } = useAuth();
  const { showToast } = useToast();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<'admin' | 'specialist' | 'reviewer' | 'viewer'>('specialist');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    try {
      if (mode === 'login') {
        await login(email, password);
        showToast('Authenticated', `Welcome back to Unilog PIM!`, 'success');
      } else {
        await register(email, password, name, role);
        showToast('Account Created', `Registered as ${role.toUpperCase()}`, 'success');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please check credentials.');
    }
  };

  const handleQuickDemoLogin = async (demo: { email: string; password: string; name: string; role: string }) => {
    setErrorMessage(null);
    setEmail(demo.email);
    setPassword(demo.password);
    try {
      await login(demo.email, demo.password);
      showToast('Demo Account Authenticated', `Signed in as ${demo.name} (${demo.role.toUpperCase()})`, 'success');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to authenticate demo account.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="glass-panel border border-white/[0.12] rounded-3xl w-full max-w-xl shadow-2xl overflow-hidden font-sans">
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-white/[0.08] bg-gradient-to-r from-[#0B101D] via-[#0F1626] to-[#0B101D] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-glow-cyan border border-cyan-400/40">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-white uppercase tracking-wider font-mono flex items-center space-x-2">
                <span>UNILOG PIM SECURITY GATEWAY</span>
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse-glow" />
              </h3>
              <p className="text-[11px] text-slate-400 font-sans mt-0.5">
                JWT Authentication & Role-Based Access Control (RBAC)
              </p>
            </div>
          </div>

          <button
            onClick={closeAuthModal}
            className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-white/[0.08] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 1-Click Quick Demo Evaluation Bar */}
        <div className="p-5 bg-slate-950/60 border-b border-white/[0.06] space-y-2.5 font-mono">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center space-x-1.5">
              <Zap className="w-3 h-3 text-cyan-400" />
              <span>1-CLICK QUICK EVALUATION LOGINS:</span>
            </span>
            <span className="text-[9px] text-slate-400">SELECT TO PRE-AUTHENTICATE</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {demoAccounts.map((demo) => {
              const roleColors: Record<string, string> = {
                admin: 'border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 hover:shadow-glow-cyan',
                specialist: 'border-blue-500/40 text-blue-300 hover:bg-blue-500/10 hover:shadow-glow-blue',
                reviewer: 'border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10 hover:shadow-glow-emerald',
                viewer: 'border-slate-500/40 text-slate-300 hover:bg-slate-500/10'
              };
              return (
                <button
                  key={demo.role}
                  type="button"
                  onClick={() => handleQuickDemoLogin(demo)}
                  className={`p-2 rounded-xl bg-slate-900/80 border text-left transition-all ${
                    roleColors[demo.role] || 'border-white/[0.08] text-slate-300'
                  }`}
                >
                  <div className="text-[10px] font-extrabold uppercase">{demo.role}</div>
                  <div className="text-[9px] text-slate-400 font-sans truncate mt-0.5">{demo.name}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Toggle: Sign In / Sign Up */}
        <div className="px-6 pt-4 flex space-x-2 border-b border-white/[0.06] font-mono text-xs">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setErrorMessage(null);
            }}
            className={`pb-3 font-bold transition-all relative ${
              mode === 'login'
                ? 'text-cyan-300 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            SIGN IN WITH CREDENTIALS
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setErrorMessage(null);
            }}
            className={`pb-3 font-bold transition-all relative ${
              mode === 'register'
                ? 'text-cyan-300 border-b-2 border-cyan-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            CREATE NEW ACCOUNT
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorMessage && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center space-x-2 font-mono">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {mode === 'register' && (
            <div>
              <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1">
                FULL NAME
              </label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Alex Mercer"
                  className="w-full pl-9 pr-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs text-white placeholder-slate-400 focus:border-cyan-400"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1">
              CORPORATE EMAIL ADDRESS
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@unilog.com"
                className="w-full pl-9 pr-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs text-white placeholder-slate-400 focus:border-cyan-400 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1">
              PASSWORD
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password..."
                className="w-full pl-9 pr-10 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs text-white placeholder-slate-400 focus:border-cyan-400 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1">
                ASSIGN ROLE
              </label>
              <select
                value={role}
                onChange={(e: any) => setRole(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs text-slate-200 focus:border-cyan-400 font-mono"
              >
                <option value="specialist">Catalog Specialist (Edit, Sandbox, Approve)</option>
                <option value="reviewer">Data Reviewer (Triage & Approvals)</option>
                <option value="admin">Administrator (Full Access)</option>
                <option value="viewer">Viewer (Read-Only Compliance)</option>
              </select>
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center space-x-2 py-2.5 bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold font-mono shadow-glow-blue transition-all disabled:opacity-50 hover:scale-[1.01]"
            >
              <span>{isLoading ? 'AUTHENTICATING...' : mode === 'login' ? 'SIGN IN TO WORKBENCH' : 'REGISTER & LOGIN'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
