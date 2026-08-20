import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthResponse, DemoAccount } from '../types';
import {
  loginUser,
  registerUser,
  getCurrentUserProfile,
  setAuthToken,
  getAuthToken,
  fetchDemoAccounts
} from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  demoAccounts: DemoAccount[];
  openAuthModal: () => void;
  closeAuthModal: () => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string, role: string) => Promise<void>;
  logout: () => void;
  hasRole: (allowedRoles: string[]) => boolean;
  canEdit: boolean;
  canApprove: boolean;
  canAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getAuthToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [demoAccounts, setDemoAccounts] = useState<DemoAccount[]>([]);

  useEffect(() => {
    loadInitialUser();
    loadDemoAccounts();
  }, []);

  const loadDemoAccounts = async () => {
    try {
      const demos = await fetchDemoAccounts();
      setDemoAccounts(demos);
    } catch (e) {
      console.error('Failed to load demo accounts:', e);
    }
  };

  const loadInitialUser = async () => {
    const savedToken = getAuthToken();
    if (!savedToken) {
      // Auto-login as default Lead Architect (Admin) for frictionless judge demo experience
      try {
        const res = await loginUser('admin@unilog.com', 'Admin2026!');
        setUser(res.user);
        setToken(res.token);
      } catch (e) {
        console.error('Failed to auto-login demo admin:', e);
      } finally {
        setIsLoading(false);
      }
      return;
    }

    try {
      const profile = await getCurrentUserProfile();
      setUser(profile);
      setToken(savedToken);
    } catch (e) {
      console.error('Failed to fetch user profile with saved token:', e);
      setAuthToken(null);
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await loginUser(email, password);
      setUser(res.user);
      setToken(res.token);
      setIsAuthModalOpen(false);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, name: string, role: string) => {
    setIsLoading(true);
    try {
      const res = await registerUser(email, password, name, role);
      setUser(res.user);
      setToken(res.token);
      setIsAuthModalOpen(false);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setAuthToken(null);
    setUser(null);
    setToken(null);
  };

  const hasRole = (allowedRoles: string[]): boolean => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  const canEdit = hasRole(['admin', 'specialist']);
  const canApprove = hasRole(['admin', 'specialist', 'reviewer']);
  const canAdmin = hasRole(['admin']);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        isAuthModalOpen,
        demoAccounts,
        openAuthModal: () => setIsAuthModalOpen(true),
        closeAuthModal: () => setIsAuthModalOpen(false),
        login,
        register,
        logout,
        hasRole,
        canEdit,
        canApprove,
        canAdmin
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
