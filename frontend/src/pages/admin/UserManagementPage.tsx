import React, { useState } from 'react';
import {
  Users,
  Search,
  ShieldCheck,
  UserCheck,
  UserX,
  Edit2,
  CheckCircle2,
  X,
} from 'lucide-react';
import { INITIAL_USERS } from '../../data/mockData';
import { User, UserRole } from '../../types';

export const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>(INITIAL_USERS);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [editUserModal, setEditUserModal] = useState<User | null>(null);
  const [selectedRole, setSelectedRole] = useState<UserRole>('customer');

  const filteredUsers = users.filter((u) => {
    if (roleFilter !== 'all' && u.role !== roleFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      if (!u.name.toLowerCase().includes(q) && !u.email.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const handleToggleStatus = (id: string) => {
    setUsers((prev) =>
      prev.map((u) =>
        u.id === id ? { ...u, status: u.status === 'active' ? 'suspended' : 'active' } : u
      )
    );
  };

  const handleRoleSave = () => {
    if (editUserModal) {
      setUsers((prev) =>
        prev.map((u) => (u.id === editUserModal.id ? { ...u, role: selectedRole } : u))
      );
      setEditUserModal(null);
    }
  };

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-[#E2E7E1] pb-5">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F4EFF7] text-[#5C2D6D] text-xs font-semibold border border-[#E0D0E7] mb-2">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Administration Access Control</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
          User Record & Role Management
        </h1>
        <p className="text-xs text-[#68736C] mt-1">
          Audit user profiles, assign privileged architect/admin roles, and manage account statuses.
        </p>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white border border-[#E2E7E1] rounded-2xl p-4 shadow-xs flex flex-col sm:flex-row gap-3 items-center justify-between text-xs">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[#68736C]" />
          <input
            type="text"
            placeholder="Search users by name, email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl pl-9 pr-4 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
          />
        </div>

        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D] w-full sm:w-auto"
        >
          <option value="all">All Roles</option>
          <option value="customer">Homeowner</option>
          <option value="architect">PCATP Architect</option>
          <option value="admin">System Admin</option>
          <option value="contractor">Contractor</option>
        </select>
      </div>

      {/* Users Table */}
      <div className="bg-white border border-[#E2E7E1] rounded-2xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px] bg-[#F7F7F2]">
                <th className="p-3.5 font-semibold">User</th>
                <th className="p-3.5 font-semibold">Assigned Role</th>
                <th className="p-3.5 font-semibold">Affiliation / Firm</th>
                <th className="p-3.5 font-semibold">Status</th>
                <th className="p-3.5 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#202923]">
              {filteredUsers.map((u) => (
                <tr key={u.id} className="hover:bg-[#F7F7F2]">
                  <td className="p-3.5">
                    <p className="font-semibold text-[#202923]">{u.name}</p>
                    <p className="text-[11px] text-[#68736C]">{u.email}</p>
                  </td>
                  <td className="p-3.5">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#EEF4F0] text-[#23483D] border border-[#DCE7DE] uppercase">
                      {u.role}
                    </span>
                  </td>
                  <td className="p-3.5 text-[#68736C]">{u.firmName || 'Independent'}</td>
                  <td className="p-3.5">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${u.status === 'active' ? 'bg-[#EEF4F0] text-[#15803D]' : 'bg-[#FEF2F2] text-[#DC2626]'}`}>
                      {u.status}
                    </span>
                  </td>
                  <td className="p-3.5 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => {
                          setEditUserModal(u);
                          setSelectedRole(u.role);
                        }}
                        className="p-1.5 rounded-lg border border-[#E2E7E1] text-[#202923] hover:bg-[#F7F7F2]"
                        title="Edit Role"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleToggleStatus(u.id)}
                        className={`p-1.5 rounded-lg border ${u.status === 'active' ? 'border-[#E2E7E1] text-[#68736C] hover:text-[#DC2626]' : 'border-emerald-300 text-emerald-600'}`}
                        title={u.status === 'active' ? 'Suspend User' : 'Activate User'}
                      >
                        {u.status === 'active' ? <UserX className="h-3.5 w-3.5" /> : <UserCheck className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Role Modal */}
      {editUserModal && (
        <div className="fixed inset-0 z-50 bg-[#202923]/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-[#E2E7E1] rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-[#202923]">Modify User Role: {editUserModal.name}</h3>
            <div>
              <label className="block text-xs font-semibold text-[#68736C] mb-1">Select System Role</label>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value as UserRole)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-xs text-[#202923] focus:outline-none focus:border-[#23483D]"
              >
                <option value="customer">Homeowner (Customer)</option>
                <option value="architect">PCATP Licensed Architect</option>
                <option value="contractor">Builder / Contractor</option>
                <option value="admin">System Administrator</option>
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setEditUserModal(null)}
                className="px-4 py-2 rounded-xl border border-[#E2E7E1] text-xs font-semibold text-[#68736C]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRoleSave}
                className="px-4 py-2 rounded-xl bg-[#23483D] text-white text-xs font-semibold hover:bg-[#1A372E]"
              >
                Save Role
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
