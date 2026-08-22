import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthResponse } from '../types';
import {
  loginUser,
  registerUser,
  getCurrentUserProfile,
  logoutUser,
  setAuthToken,
  getAuthToken,
  getSavedUserProfile
} from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthModalOpen: boolean;
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
  const [user, setUser] = useState<User | null>(getSavedUserProfile());
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);

  useEffect(() => {
    loadInitialUser();
  }, []);

  const loadInitialUser = async () => {
    try {
      const profile = await getCurrentUserProfile();
      setUser(profile);
      setToken(null);
      setAuthToken(null, profile);
    } catch (e) {
      console.error('Session expired or invalid token:', e);
      setAuthToken(null, null);
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
      setToken(null);
      setAuthToken(res.token, res.user);
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
      setToken(null);
      setAuthToken(res.token, res.user);
      setIsAuthModalOpen(false);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    // Clear UI state immediately; the request invalidates the server-side
    // token version and is best-effort if the network is already unavailable.
    void logoutUser().catch((error) => console.warn('Server logout failed:', error));
    setAuthToken(null, null);
    setUser(null);
    setToken(null);
  };

  const hasRole = (allowedRoles: string[]): boolean => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  const canEdit = hasRole(['admin', 'specialist', 'reviewer']);
  const canApprove = hasRole(['admin', 'reviewer']);
  const canAdmin = hasRole(['admin']);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        isAuthModalOpen,
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
