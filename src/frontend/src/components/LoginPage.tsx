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
  CheckCircle2,
  Cpu,
  Layers,
  ArrowDownRight,
  Terminal
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
        showToast('Authenticated', 'Welcome back to Unilog PIM Workbench', 'success');
      } else {
        await register(email, password, name, role);
        showToast('Account Created', `Registered profile as ${role.toUpperCase()}`, 'success');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify credentials.');
    }
  };

  const pipelineStages = [
    { num: '01', title: 'Ingestion & Placeholder Sanitizer', desc: 'Strips null flags, isolates vendor tokens & MPN' },
    { num: '02', title: 'Canonical Entity & Brand Resolver', desc: 'Maps codes to legal mfrs & trademarked brands (®, ™)' },
    { num: '03', title: 'Taxonomy & UNSPSC Classification', desc: 'Assigns 3-level Classpath & 8-digit UNSPSC code' },
    { num: '04', title: 'Attribute Extraction & LOV Engine', desc: '50-slot spec extraction with strict LOV validation' },
    { num: '05', title: 'UOM & Fraction Standardization', desc: 'Decimal to 64th fractions & standard unit spacing' },
    { num: '06', title: '5-Tier Description Synthesis', desc: 'Invoice (<=40 CAPS), Mobile (60-80), Short, Long, Web' },
    { num: '07', title: '252-Column Delivery Mapping', desc: 'Syndication to Unilog standard CSV/Excel layout' },
  ];

  return (
    <div className="min-h-screen w-full bg-[#0B0E13] text-[#E7EAF0] flex flex-col lg:flex-row font-sans selection:bg-[#45E0D6] selection:text-[#0B0E13]">
      
      {/* LEFT PANEL: 7-Stage Pipeline Blueprint & Value Demonstration */}
      <div className="lg:w-[56%] bg-[#0B0E13] border-b lg:border-b-0 lg:border-r border-[#232935] p-6 sm:p-10 lg:p-12 flex flex-col justify-between relative overflow-hidden">
        {/* Subtle Ambient Radial Accents */}
        <div className="absolute top-0 left-0 w-96 h-96 bg-[#45E0D6]/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-[#3B82F6]/5 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="relative z-10">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-[#12161D] border border-[#232935] flex items-center justify-center shadow-[0_0_20px_rgba(69,224,214,0.15)]">
              <Database className="w-5 h-5 text-[#45E0D6]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-base font-extrabold tracking-wider text-white font-mono">UNILOG</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#45E0D6]/10 text-[#45E0D6] font-mono font-bold border border-[#45E0D6]/20">
                  CIMPLIFI™ PIM
                </span>
              </div>
              <p className="text-xs text-[#8B93A3]">
                Industrial Product Intelligence & Master Data Enrichment
              </p>
            </div>
          </div>
        </div>

        {/* 7-Stage Pipeline Lit Sequence */}
        <div className="my-8 relative z-10 space-y-4">
          <div className="flex items-center justify-between border-b border-[#232935] pb-2">
            <h3 className="text-xs font-mono font-bold text-[#8B93A3] uppercase tracking-wider flex items-center space-x-2">
              <Cpu className="w-3.5 h-3.5 text-[#45E0D6]" />
              <span>DETERMINISTIC 7-STAGE ENRICHMENT PIPELINE</span>
            </h3>
            <span className="text-[10px] font-mono text-[#3DDC84] font-bold">100% LOV COMPLIANT</span>
          </div>

          <div className="grid grid-cols-1 gap-2">
            {pipelineStages.map((stage) => (
              <div
                key={stage.num}
                className="flex items-center space-x-3 px-3.5 py-2.5 rounded-xl bg-[#12161D] border border-[#232935] hover:border-[#45E0D6]/40 transition-colors group"
              >
                <span className="font-mono text-xs font-bold text-[#45E0D6] group-hover:text-white transition-colors">
                  {stage.num}
                </span>
                <div className="w-1.5 h-1.5 rounded-full bg-[#3DDC84]" />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-[#E7EAF0] truncate font-sans">
                    {stage.title}
                  </div>
                  <div className="text-[11px] text-[#8B93A3] truncate font-sans">
                    {stage.desc}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Real Transformation Before/After Card */}
        <div className="relative z-10 p-4 rounded-xl bg-[#12161D] border border-[#232935] font-mono text-xs">
          <div className="flex items-center justify-between text-[11px] text-[#8B93A3] mb-2 font-mono">
            <span className="flex items-center space-x-1">
              <Terminal className="w-3 h-3 text-[#E8A33D]" />
              <span>LIVE TRANSFORM PREVIEW</span>
            </span>
            <span className="text-[#3DDC84]">11.4ms LATENCY</span>
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div className="flex items-start space-x-2">
              <span className="text-[#EF5A5A] font-bold flex-shrink-0">RAW IN:</span>
              <span className="text-[#8B93A3] truncate">PDSH4816AF Dishwasher SS -- Unbranded -- APPDE</span>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-[#3DDC84] font-bold flex-shrink-0">ENRICHED:</span>
              <span className="text-[#E7EAF0] truncate">Frigidaire® Gallery 24 in Built-In Dishwasher 49 dBA SST 120V</span>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT PANEL: Interactive Authentication Card */}
      <div className="lg:w-[44%] bg-[#0B0E13] flex items-center justify-center p-6 sm:p-10 lg:p-12 relative">
        <div className="w-full max-w-md">
          {/* Glass Card: The One Place Using Glass Treatment */}
          <div className="bg-[#12161D]/90 backdrop-blur-xl border border-[#232935] rounded-2xl p-6 sm:p-8 shadow-glass-card relative">
            
            {/* Header */}
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#1A1F29] border border-[#232935] mb-3 text-[#45E0D6]">
                <Lock className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-white tracking-tight font-sans">
                {mode === 'login' ? 'Enterprise Gateway Sign In' : 'Create PIM Access Profile'}
              </h2>
              <p className="text-xs text-[#8B93A3] mt-1 font-sans">
                {mode === 'login'
                  ? 'Enter corporate credentials to access catalog & review queue'
                  : 'Register a new profile to curate and validate industrial data'}
              </p>
            </div>

            {/* Mode Selector */}
            <div className="flex rounded-xl bg-[#0B0E13] p-1 mb-6 border border-[#232935] font-mono text-xs">
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setErrorMessage(null);
                }}
                className={`flex-1 py-2 rounded-lg font-bold transition-all ${
                  mode === 'login'
                    ? 'bg-[#1A1F29] text-[#45E0D6] border border-[#232935] shadow-sm'
                    : 'text-[#8B93A3] hover:text-white'
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
                    ? 'bg-[#1A1F29] text-[#45E0D6] border border-[#232935] shadow-sm'
                    : 'text-[#8B93A3] hover:text-white'
                }`}
              >
                REGISTER
              </button>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="mb-4 p-3 bg-[#EF5A5A]/10 border border-[#EF5A5A]/30 rounded-xl text-[#EF5A5A] text-xs flex items-center space-x-2 font-mono">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && (
                <div>
                  <label className="block text-[10px] font-mono uppercase font-bold text-[#8B93A3] mb-1">
                    FULL NAME
                  </label>
                  <div className="relative">
                    <UserIcon className="w-4 h-4 text-[#8B93A3] absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Alex Mercer"
                      className="w-full pl-10 pr-3.5 py-2.5 bg-[#0B0E13] border border-[#232935] rounded-xl text-xs text-white placeholder-[#525B6C] focus:border-[#45E0D6] focus:outline-none transition-colors"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-[10px] font-mono uppercase font-bold text-[#8B93A3] mb-1">
                  CORPORATE EMAIL
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-[#8B93A3] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@unilog.com"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-[#0B0E13] border border-[#232935] rounded-xl text-xs text-white placeholder-[#525B6C] focus:border-[#45E0D6] focus:outline-none transition-colors font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase font-bold text-[#8B93A3] mb-1">
                  PASSWORD
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-[#8B93A3] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-10 pr-10 py-2.5 bg-[#0B0E13] border border-[#232935] rounded-xl text-xs text-white placeholder-[#525B6C] focus:border-[#45E0D6] focus:outline-none transition-colors font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#8B93A3] hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {mode === 'register' && (
                <div>
                  <label className="block text-[10px] font-mono uppercase font-bold text-[#8B93A3] mb-1">
                    ROLE & PERMISSIONS
                  </label>
                  <select
                    value={role}
                    onChange={(e: any) => setRole(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-[#0B0E13] border border-[#232935] rounded-xl text-xs text-[#E7EAF0] focus:border-[#45E0D6] focus:outline-none font-mono"
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
                  className="w-full flex items-center justify-center space-x-2 py-2.5 bg-[#45E0D6] hover:bg-[#34cbbf] text-[#0B0E13] rounded-xl text-xs font-bold font-mono transition-all disabled:opacity-50 hover:scale-[1.01] shadow-[0_0_16px_rgba(69,224,214,0.3)]"
                >
                  <span>{isLoading ? 'VERIFYING...' : mode === 'login' ? 'SIGN IN TO WORKBENCH' : 'CREATE ACCOUNT & SIGN IN'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </form>

            {/* Bottom Security Note */}
            <div className="mt-6 pt-4 border-t border-[#232935] text-center">
              <p className="text-[10px] text-[#8B93A3] font-mono flex items-center justify-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#3DDC84]" />
                <span>OWASP PBKDF2 & RFC 7519 JWT ENCRYPTION</span>
              </p>
            </div>

          </div>
        </div>
      </div>

    </div>
  );
};
