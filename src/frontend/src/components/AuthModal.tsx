import React, { useState } from 'react';
import {
  X,
  Lock,
  Mail,
  User as UserIcon,
  ShieldCheck,
  AlertCircle,
  Eye,
  EyeOff
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from './Toast';

export const AuthModal: React.FC = () => {
  const { isAuthModalOpen, closeAuthModal, login, register, isLoading } = useAuth();
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
        showToast('Authenticated', 'Welcome back to Unilog PIM!', 'success');
      } else {
        await register(email, password, name, role);
        showToast('Account Created', `Registered as ${role.toUpperCase()}`, 'success');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please check your credentials.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 font-sans">
      <div className="bg-[var(--surface-2)] border border-[var(--border-strong)] rounded-xl w-full max-w-md shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[var(--border)] bg-[var(--surface-1)] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-2.5 h-2.5 rounded-[2px] bg-[var(--cyan)]" />
            <div>
              <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider font-mono">
                PIM SECURITY &amp; ACCESS GATE
              </h3>
              <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                JWT Authentication &amp; RBAC Permissions
              </p>
            </div>
          </div>

          <button
            onClick={closeAuthModal}
            className="p-1.5 text-[var(--text-muted)] hover:text-white rounded-md hover:bg-[var(--surface-2)] transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Mode Selector */}
        <div className="px-6 pt-4 flex gap-4 border-b border-[var(--border)] font-mono text-xs">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setErrorMessage(null);
            }}
            className={`pb-3 font-semibold transition-all cursor-pointer ${
              mode === 'login'
                ? 'text-[var(--cyan)] border-b-2 border-[var(--cyan)]'
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
            className={`pb-3 font-semibold transition-all cursor-pointer ${
              mode === 'register'
                ? 'text-[var(--cyan)] border-b-2 border-[var(--cyan)]'
                : 'text-[var(--text-secondary)] hover:text-white'
            }`}
          >
            REGISTER NEW PROFILE
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6">
          {errorMessage && (
            <div className="mb-4 p-2.5 bg-[var(--red-bg)] border border-[var(--red)] rounded-md text-[var(--red)] text-xs flex items-center gap-2 font-mono">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="block text-xs text-[var(--text-secondary)] mb-1">Full Name</label>
                <div className="relative">
                  <UserIcon className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Alex Mercer"
                    className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md pl-9 pr-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--cyan)]"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Corporate Email</label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@unilog.com"
                  className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md pl-9 pr-3 py-2 text-xs text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--cyan)]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Password</label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md pl-9 pr-9 py-2 text-xs text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--cyan)]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-white cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {mode === 'register' && (
              <div>
                <label className="block text-xs text-[var(--text-secondary)] mb-1">Assigned Role</label>
                <select
                  value={role}
                  onChange={(e: any) => setRole(e.target.value)}
                  className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 py-2 text-xs text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--cyan)] cursor-pointer"
                >
                  <option value="specialist">Catalog Specialist (Edit &amp; Approve)</option>
                  <option value="reviewer">Data Reviewer (Triage &amp; Approvals)</option>
                  <option value="admin">Platform Administrator (Full Access)</option>
                  <option value="viewer">Auditor / Viewer (Read-Only)</option>
                </select>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[var(--cyan)] text-[#06201D] font-semibold text-xs rounded-md py-2.5 mt-2 hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
            >
              {isLoading ? 'VERIFYING...' : mode === 'login' ? 'SIGN IN' : 'CREATE PROFILE & SIGN IN'}
            </button>
          </form>
        </div>

      </div>
    </div>
  );
};
