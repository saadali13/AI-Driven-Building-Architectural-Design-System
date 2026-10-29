import React, { useState } from 'react';
import { 
  Users, 
  UserPlus, 
  Search, 
  MoreVertical, 
  ShieldCheck, 
  Shield, 
  Mail, 
  Building, 
  CheckCircle2, 
  Clock, 
  X, 
  ChevronDown, 
  UserCheck, 
  Download, 
  Trash2, 
  Edit3,
  Check,
  Building2,
  Lock
} from 'lucide-react';
import { useAuth, ROLES, ROLE_DETAILS } from '../../context/AuthContext';


const INITIAL_MEMBERS = [
  {
    id: 'usr_1',
    name: 'Lead Architectural Director',
    email: 'director@archai.design',
    role: ROLES.ARCHITECT,
    customRoleTitle: 'Chief Generative Architect',
    status: 'Active',
    avatar: null,
    projectsAssigned: 14,
    lastActive: 'Just now',
    department: 'Generative Spatial Design',
    permissionsCount: 16,
    joinedDate: 'Jan 15, 2024'
  },
  {
    id: 'usr_2',
    name: 'Senior Structural Engineer',
    email: 'structural.eng@archai.design',
    role: ROLES.PROJECT_MANAGER,
    customRoleTitle: 'Senior Project Supervisor',
    status: 'Active',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
    projectsAssigned: 8,
    lastActive: '12 mins ago',
    department: 'Site & Project Execution',
    permissionsCount: 11,
    joinedDate: 'Feb 02, 2024'
  },
  {
    id: 'usr_3',
    name: 'BIM & Parametric Designer',
    email: 'bim.designer@archai.design',
    role: ROLES.ARCHITECT,
    customRoleTitle: 'Computational Geometry Specialist',
    status: 'Active',
    avatar: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=150&q=80',
    projectsAssigned: 9,
    lastActive: '1 hour ago',
    department: '3D CAD & BIM Modeling',
    permissionsCount: 14,
    joinedDate: 'Mar 10, 2024'
  },
  {
    id: 'usr_4',
    name: 'Platform Security Administrator',
    email: 'sysadmin@archai.design',
    role: ROLES.SYSTEM_ADMIN,
    customRoleTitle: 'Infrastructure Administrator',
    status: 'Active',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80',
    projectsAssigned: 28,
    lastActive: '3 hours ago',
    department: 'System Architecture & AI Infrastructure',
    permissionsCount: 22,
    joinedDate: 'Dec 01, 2023'
  },
  {
    id: 'usr_5',
    name: 'Residential Client Sponsor',
    email: 'client@dha-invest.com',
    role: ROLES.HOMEOWNER,
    customRoleTitle: 'Client / Real Estate Sponsor',
    status: 'Active',
    avatar: null,
    projectsAssigned: 2,
    lastActive: 'Yesterday',
    department: 'Villa Residential Development',
    permissionsCount: 6,
    joinedDate: 'Apr 18, 2024'
  },
  {
    id: 'usr_6',
    name: 'CDA Compliance Auditor',
    email: 'auditor@archai.design',
    role: ROLES.VIEWER,
    customRoleTitle: 'External Structural Auditor',
    status: 'Pending',
    avatar: null,
    projectsAssigned: 3,
    lastActive: 'Invitation Sent',
    department: 'CDA Structural Compliance',
    permissionsCount: 3,
    joinedDate: 'May 04, 2024'
  }
];

export default function TeamModule({ onOpenStudio }) {
  const { user } = useAuth();
  const [members, setMembers] = useState(INITIAL_MEMBERS);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showPermissionsModal, setShowPermissionsModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [actionMenuOpenId, setActionMenuOpenId] = useState(null);
  const [toastMessage, setToastMessage] = useState('');

  const [inviteForm, setInviteForm] = useState({
    name: '',
    email: '',
    role: ROLES.ARCHITECT,
    department: 'Generative Spatial Design',
  });

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3500);
  };

  const filteredMembers = members.filter((m) => {
    const matchesSearch = 
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.customRoleTitle.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesRole = roleFilter === 'ALL' || m.role === roleFilter;
    const matchesStatus = statusFilter === 'ALL' || m.status === statusFilter;

    return matchesSearch && matchesRole && matchesStatus;
  });

  const handleSendInvite = (e) => {
    e.preventDefault();
    if (!inviteForm.email || !inviteForm.name) {
      showToast('Please provide both full name and email address.');
      return;
    }

    const newMember = {
      id: `usr_${Date.now()}`,
      name: inviteForm.name.trim(),
      email: inviteForm.email.trim(),
      role: inviteForm.role,
      customRoleTitle: ROLE_DETAILS[inviteForm.role]?.title || 'Team Member',
      status: 'Pending',
      avatar: null,
      projectsAssigned: 1,
      lastActive: 'Invitation Sent',
      department: inviteForm.department || 'General Architecture',
      permissionsCount: inviteForm.role === ROLES.SYSTEM_ADMIN ? 22 : inviteForm.role === ROLES.ARCHITECT ? 16 : 8,
      joinedDate: 'Just now'
    };

    setMembers([newMember, ...members]);
    setShowInviteModal(false);
    setInviteForm({
      name: '',
      email: '',
      role: ROLES.ARCHITECT,
      department: 'Generative Spatial Design',
    });
    showToast(`Invitation sent to ${newMember.email}!`);
  };

  const handleRemoveMember = (memberId, memberName) => {
    setMembers(members.filter(m => m.id !== memberId));
    showToast(`${memberName} removed from workspace.`);
    setActionMenuOpenId(null);
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 text-slate-900 font-sans">
      
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-xl flex items-center gap-2.5 text-xs font-semibold animate-in fade-in">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header Bar */}
      <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Team Collaboration &amp; Access Control</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Manage organization members, assign project permissions, and invite external clients and auditors.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowInviteModal(true)}
          className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition shadow-md shadow-blue-500/20 flex items-center gap-2 cursor-pointer shrink-0 hover:scale-[1.01]"
        >
          <UserPlus className="w-4 h-4" />
          <span>Invite Team Member</span>
        </button>
      </div>

      {/* Search & Role Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-xs">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by name, email, department, or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {['ALL', ROLES.ARCHITECT, ROLES.PROJECT_MANAGER, ROLES.HOMEOWNER, ROLES.SYSTEM_ADMIN].map((r) => {
            const label = r === 'ALL' ? 'All Roles' : ROLE_DETAILS[r]?.badge || r;
            return (
              <button
                key={r}
                type="button"
                onClick={() => setRoleFilter(r)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                  roleFilter === r
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Members Table */}
      <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-base">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase text-xs font-mono tracking-wider">
              <tr>
                <th className="px-6 py-4">Member Name &amp; Email</th>
                <th className="px-6 py-4">Assigned Role</th>
                <th className="px-6 py-4">Department</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Projects</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredMembers.map((m) => {
                const roleMeta = ROLE_DETAILS[m.role] || ROLE_DETAILS[ROLES.ARCHITECT];
                const isMenuOpen = actionMenuOpenId === m.id;
                return (
                  <tr key={m.id} className="hover:bg-slate-50/70 transition">
                    
                    {/* Name & Avatar */}
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-3.5">
                        {m.avatar ? (
                          <img src={m.avatar} alt={m.name} className="w-11 h-11 rounded-full object-cover ring-2 ring-slate-200" />
                        ) : (
                          <div className="w-11 h-11 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-base shadow-xs">
                            {m.name.charAt(0)}
                          </div>
                        )}
                        <div>
                          <span className="font-bold text-slate-900 block text-base">{m.name}</span>
                          <span className="text-slate-500 text-sm font-mono">{m.email}</span>
                        </div>
                      </div>
                    </td>

                    {/* Role Badge */}
                    <td className="px-6 py-5">
                      <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-mono font-bold border ${roleMeta.color}`}>
                        <span className={`w-2 h-2 rounded-full ${roleMeta.dotColor}`}></span>
                        <span>{roleMeta.title}</span>
                      </span>
                    </td>

                    {/* Department */}
                    <td className="px-6 py-5 text-slate-700 font-semibold text-base">
                      {m.department}
                    </td>

                    {/* Status */}
                    <td className="px-6 py-5">
                      <span className={`px-3 py-1 rounded-lg text-xs font-bold ${
                        m.status === 'Active' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {m.status}
                      </span>
                    </td>

                    {/* Projects count */}
                    <td className="px-6 py-5 font-mono font-bold text-slate-900 text-base">
                      {m.projectsAssigned} Active
                    </td>


                    {/* Actions */}
                    <td className="px-6 py-4 text-right relative">
                      <button
                        type="button"
                        onClick={() => setActionMenuOpenId(isMenuOpen ? null : m.id)}
                        className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 cursor-pointer"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>

                      {isMenuOpen && (
                        <div className="absolute right-6 mt-1 w-40 bg-white border border-slate-200 rounded-xl p-1 shadow-xl z-20 text-left">
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedMember(m);
                              setShowPermissionsModal(true);
                              setActionMenuOpenId(null);
                            }}
                            className="w-full flex items-center gap-2 px-3 py-1.5 text-slate-700 hover:bg-slate-50 rounded-lg text-xs font-medium"
                          >
                            <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                            <span>View Scopes</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleRemoveMember(m.id, m.name)}
                            className="w-full flex items-center gap-2 px-3 py-1.5 text-rose-600 hover:bg-rose-50 rounded-lg text-xs font-medium"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Remove Member</span>
                          </button>
                        </div>
                      )}
                    </td>

                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* INVITE MEMBER MODAL */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white text-slate-900 rounded-3xl max-w-md w-full p-6 sm:p-8 border border-slate-200 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-base text-slate-900">Invite New Team Member</h3>
              <button onClick={() => setShowInviteModal(false)} className="text-slate-400 hover:text-slate-700">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSendInvite} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Full Legal Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Senior Architectural Engineer"
                  value={inviteForm.name}
                  onChange={(e) => setInviteForm({ ...inviteForm, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-blue-600 focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Work Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="colleague@archai.design"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-blue-600 focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Assigned Role</label>
                <select
                  value={inviteForm.role}
                  onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-blue-600 focus:bg-white cursor-pointer"
                >
                  <option value={ROLES.ARCHITECT}>Lead Architect &amp; Designer</option>
                  <option value={ROLES.PROJECT_MANAGER}>Project Manager</option>
                  <option value={ROLES.HOMEOWNER}>Homeowner / Client</option>
                  <option value={ROLES.VIEWER}>Read-Only Stakeholder</option>
                </select>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md shadow-blue-500/20"
                >
                  Send Invitation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PERMISSIONS MODAL */}
      {showPermissionsModal && selectedMember && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white text-slate-900 rounded-3xl max-w-md w-full p-6 sm:p-8 border border-slate-200 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-base text-slate-900">{selectedMember.name}</h3>
                <span className="text-xs text-slate-500 font-mono">{selectedMember.email}</span>
              </div>
              <button onClick={() => setShowPermissionsModal(false)} className="text-slate-400 hover:text-slate-700">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
              <span className="block font-bold text-slate-800 mb-1">Active Clearance Scope:</span>
              <p className="text-slate-600">{ROLE_DETAILS[selectedMember.role]?.description}</p>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setShowPermissionsModal(false)}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
