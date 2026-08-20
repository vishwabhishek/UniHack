import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from './Toast';
import { AlertCircle, Eye, EyeOff } from 'lucide-react';

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
        showToast('Authenticated', 'Welcome back to Unilog PIM Workbench', 'success');
      } else {
        await register(email, password, name, role);
        showToast('Account Created', `Registered profile as ${role.toUpperCase()}`, 'success');
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
                  Industrial product intelligence &amp; enrichment
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
              <div className="raw">"APPDE DW-5SST -- Unbranded -- 50.25in 120v"</div>
              <div className="sample-arrow">↓ resolved, extracted, normalized</div>
              <div className="clean">DISHWASHER LEG 5 SST 120V 15A 50-1/4IN</div>
            </div>
          </div>

          <div className="text-xs text-[var(--text-muted)] mt-8">
            252-column delivery schema · UNSPSC classification · zero hallucinated attributes
          </div>
        </div>

        {/* Right Side: Auth Card */}
        <div className="flex items-center justify-center p-6 sm:p-10 lg:p-12 bg-[var(--bg)]">
          <div className="w-full max-w-[380px] bg-[var(--surface-glass)] backdrop-blur-[14px] border border-[var(--border-strong)] rounded-xl p-8 shadow-2xl">
            
            <h1 className="text-xl font-semibold mb-1 text-[var(--text-primary)]">
              {mode === 'login' ? 'Sign in' : 'Create Account'}
            </h1>
            <p className="text-[13px] text-[var(--text-secondary)] mb-6">
              {mode === 'login' ? 'Access the catalog workbench' : 'Register a new data specialist profile'}
            </p>

            {/* Switcher Tab */}
            <div className="flex rounded-md bg-[var(--surface-1)] p-1 mb-5 border border-[var(--border-strong)] font-mono text-xs">
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setErrorMessage(null);
                }}
                className={`flex-1 py-1.5 rounded transition-all ${
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
                className={`flex-1 py-1.5 rounded transition-all ${
                  mode === 'register'
                    ? 'bg-[var(--cyan)] text-[#06201D] font-semibold'
                    : 'text-[var(--text-secondary)] hover:text-white'
                }`}
              >
                REGISTER
              </button>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="mb-4 p-2.5 bg-[var(--red-bg)] border border-[var(--red)] rounded-md text-[var(--red)] text-xs flex items-center gap-2 font-mono">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && (
                <div>
                  <label className="block text-xs text-[var(--text-secondary)] mb-1.5">Full Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Abhishek Vishwakarma"
                    className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 py-2.5 text-[13px] text-[var(--text-primary)] focus:outline-none focus:border-[var(--cyan)]"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs text-[var(--text-secondary)] mb-1.5">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@distributor.com"
                  className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 py-2.5 text-[13px] text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--cyan)]"
                />
              </div>

              <div>
                <label className="block text-xs text-[var(--text-secondary)] mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 pr-9 py-2.5 text-[13px] text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--cyan)]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {mode === 'register' && (
                <div>
                  <label className="block text-xs text-[var(--text-secondary)] mb-1.5">Role</label>
                  <select
                    value={role}
                    onChange={(e: any) => setRole(e.target.value)}
                    className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 py-2.5 text-[13px] text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--cyan)]"
                  >
                    <option value="specialist">Specialist (Curate, Sandbox, Approve)</option>
                    <option value="reviewer">Reviewer (Triage & Approvals)</option>
                    <option value="admin">Administrator (Full Access)</option>
                    <option value="viewer">Viewer (Read-Only 252-Col Inspection)</option>
                  </select>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-[var(--cyan)] text-[#06201D] font-semibold text-[13px] rounded-md py-2.5 mt-2 hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
              >
                {isLoading ? 'Verifying...' : mode === 'login' ? 'Sign in' : 'Create account'}
              </button>
            </form>

            <div className="flex justify-between items-center mt-4 text-xs text-[var(--text-muted)]">
              <span>Forgot password?</span>
              <a href="#" onClick={(e) => { e.preventDefault(); setMode(mode === 'login' ? 'register' : 'login'); }} className="text-[var(--cyan)] no-underline">
                {mode === 'login' ? 'Request access' : 'Existing account? Sign in'}
              </a>
            </div>

            <div className="mt-6 pt-5 border-t border-[var(--border)] text-[11px] text-[var(--text-muted)]">
              Roles: admin · specialist · reviewer · viewer — access is enforced server-side, not just hidden in this screen.
            </div>

          </div>
        </div>

      </div>
    </div>
  );
};
