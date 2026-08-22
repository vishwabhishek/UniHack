import React, { useState, useEffect } from 'react';
import { User } from '../types';
import { fetchUsers, updateUserRole } from '../services/api';
import { Users, Shield, CheckCircle2, AlertCircle, RefreshCw, UserCheck, Key } from 'lucide-react';

interface UserManagementProps {
  currentUser: User | null;
}

export const UserManagement: React.FC<UserManagementProps> = ({ currentUser }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Role edit modal state
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>('viewer');
  const [updating, setUpdating] = useState<boolean>(false);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchUsers();
      setUsers(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser?.role === 'admin') {
      loadUsers();
    }
  }, [currentUser]);

  if (currentUser?.role !== 'admin') {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="bg-amber-950/40 border border-amber-800/60 rounded-xl p-6 text-center">
          <Shield className="w-12 h-12 text-amber-400 mx-auto mb-3" />
          <h2 className="text-xl font-bold text-amber-200 mb-2">Admin Access Required</h2>
          <p className="text-amber-300/80 text-sm max-w-md mx-auto">
            User management and role assignment are restricted to administrators. Contact your platform administrator to modify user permissions.
          </p>
        </div>
      </div>
    );
  }

  const handleRoleChangeConfirm = async () => {
    if (!editingUser) return;
    setUpdating(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const res = await updateUserRole(editingUser.id, selectedRole);
      setSuccessMessage(res.message || `User role updated to ${selectedRole}`);
      setEditingUser(null);
      await loadUsers();
    } catch (err: any) {
      setError(err.message || 'Failed to update user role');
    } finally {
      setUpdating(false);
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-purple-900/60 text-purple-200 border border-purple-700/60 flex items-center gap-1"><Shield className="w-3 h-3" /> Admin</span>;
      case 'specialist':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-blue-900/60 text-blue-200 border border-blue-700/60 flex items-center gap-1"><Key className="w-3 h-3" /> Specialist</span>;
      case 'reviewer':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-emerald-900/60 text-emerald-200 border border-emerald-700/60 flex items-center gap-1"><UserCheck className="w-3 h-3" /> Reviewer</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-zinc-800 text-zinc-300 border border-zinc-700">Viewer</span>;
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Users className="w-6 h-6 text-blue-400" />
            <h1 className="text-xl font-bold text-zinc-100">Enterprise User Management & RBAC</h1>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Manage enterprise operators, inspect assigned roles, and assign permissions. Role changes immediately invalidate existing active tokens.
          </p>
        </div>
        <button
          onClick={loadUsers}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-xs font-medium text-zinc-200 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Users
        </button>
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-red-950/50 border border-red-800 rounded-lg p-3 text-xs text-red-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}
      {successMessage && (
        <div className="bg-emerald-950/50 border border-emerald-800 rounded-lg p-3 text-xs text-emerald-200 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-400" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-zinc-300">
            <thead className="bg-zinc-950/70 text-zinc-400 border-b border-zinc-800 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Email Address</th>
                <th className="px-4 py-3">Current Role</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-zinc-400" />
                    Loading enterprise users...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                    No registered users found.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-zinc-800/40 transition-colors">
                    <td className="px-4 py-3 font-medium text-zinc-200">
                      {u.name || 'Unnamed Operator'}
                      {u.id === currentUser?.id && (
                        <span className="ml-2 text-[10px] bg-blue-950 text-blue-300 border border-blue-800 px-1.5 py-0.5 rounded">
                          You
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-zinc-400">{u.email}</td>
                    <td className="px-4 py-3">{getRoleBadge(u.role)}</td>
                    <td className="px-4 py-3 text-zinc-500 font-mono">
                      {u.created_at ? new Date(u.created_at * 1000).toLocaleString() : 'System Seed'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => {
                          setEditingUser(u);
                          setSelectedRole(u.role);
                        }}
                        disabled={u.id === currentUser?.id}
                        className="px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded text-xs font-medium text-zinc-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        Change Role
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Role Change Modal */}
      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-400" />
              <h3 className="text-base font-bold text-zinc-100">Update User Role & Permissions</h3>
            </div>

            <div className="text-xs text-zinc-400 space-y-1">
              <p><span className="text-zinc-500">User:</span> <strong className="text-zinc-200">{editingUser.name}</strong></p>
              <p><span className="text-zinc-500">Email:</span> <span className="font-mono text-zinc-300">{editingUser.email}</span></p>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-medium text-zinc-300">Select New Role</label>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-hidden focus:border-blue-500"
              >
                <option value="viewer">Viewer (Read-only catalog & search)</option>
                <option value="reviewer">Reviewer (Review queue & attribute approvals)</option>
                <option value="specialist">Specialist (Evidence ingestion & manual overrides)</option>
                <option value="admin">Admin (Full administrative & user management)</option>
              </select>
            </div>

            <div className="bg-amber-950/30 border border-amber-900/50 rounded-lg p-3 text-[11px] text-amber-300/90 leading-relaxed">
              <strong>Security Policy Note:</strong> Modifying a user's role will increment their active token version, immediately revoking existing session tokens and requiring them to re-authenticate.
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setEditingUser(null)}
                disabled={updating}
                className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-xs font-medium text-zinc-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRoleChangeConfirm}
                disabled={updating}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                {updating && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                Confirm Role Update
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
