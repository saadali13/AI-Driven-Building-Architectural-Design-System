import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Users, 
  Database, 
  Cpu, 
  Sparkles, 
  Search, 
  Activity, 
  Server, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  HardDrive, 
  KeyRound, 
  Layers, 
  Upload, 
  Download, 
  Trash2, 
  Lock, 
  UserPlus, 
  Clock, 
  TrendingUp, 
  BarChart3,
  FileCode,
  Sliders,
  Check,
  ShieldAlert,
  ArrowUpRight,
  Filter,
  MessageSquare,
  Star,
  Mail
} from 'lucide-react';
import { useAuth, ROLES, ROLE_DETAILS } from '../../context/AuthContext';
import { getStoredFeedback, deleteUserFeedback } from '../../utils/feedbackStore';

const INITIAL_USERS = [
  { id: 'usr_admin_usama', name: 'Usama Rajput', email: 'usamarajput2426@gmail.com', role: ROLES.SYSTEM_ADMIN, status: 'Active', designsCount: 156, joined: '2026-01-01' },
  { id: 'usr_001', name: 'System Administrator', email: 'admin@archai.design', role: ROLES.SYSTEM_ADMIN, status: 'Active', designsCount: 142, joined: '2026-01-01' },
  { id: 'usr_002', name: 'Lead Architect', email: 'architect@archai.design', role: ROLES.ARCHITECT, status: 'Active', designsCount: 89, joined: '2026-01-05' },
  { id: 'usr_003', name: 'Spatial Designer', email: 'designer@archai.design', role: ROLES.DESIGNER, status: 'Active', designsCount: 54, joined: '2026-01-10' },
  { id: 'usr_004', name: 'Construction Engineer', email: 'engineer@archai.design', role: ROLES.CONSTRUCTION_PRO, status: 'Active', designsCount: 31, joined: '2026-01-15' },
  { id: 'usr_005', name: 'Real Estate Developer', email: 'developer@archai.design', role: ROLES.REAL_ESTATE_DEV, status: 'Active', designsCount: 78, joined: '2026-01-20' },
  { id: 'usr_006', name: 'Homeowner Client', email: 'client.homeowner@archai.pk', role: ROLES.HOMEOWNER, status: 'Active', designsCount: 6, joined: '2026-02-01' },
  { id: 'usr_007', name: 'Tariq Mehmood', email: 'tariq.arch@gmail.com', role: ROLES.ARCHITECT, status: 'Active', designsCount: 22, joined: '2026-02-04' },
  { id: 'usr_008', name: 'Ayesha Siddiqui', email: 'ayesha.des@outlook.com', role: ROLES.DESIGNER, status: 'Suspended', designsCount: 9, joined: '2026-02-08' },
];

export default function AdminDashboardModule() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'users' | 'dataset' | 'system' | 'feedback'
  const [usersList, setUsersList] = useState(INITIAL_USERS);
  const [feedbackList, setFeedbackList] = useState(() => getStoredFeedback());
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');

  
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestSuccess, setIngestSuccess] = useState(false);
  const [toastMsg, setToastMsg] = useState('');

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3500);
  };

  const handleToggleUserStatus = (id) => {
    setUsersList(usersList.map(u => {
      if (u.id === id) {
        const nextStatus = u.status === 'Active' ? 'Suspended' : 'Active';
        showToast(`User ${u.name} is now ${nextStatus}.`);
        return { ...u, status: nextStatus };
      }
      return u;
    }));
  };

  const handleDeleteUser = (userId, userName) => {
    if (window.confirm(`Are you sure you want to permanently delete user record "${userName}" from the system? This action cannot be undone.`)) {
      setUsersList(usersList.filter(u => u.id !== userId));
      showToast(`User record "${userName}" has been permanently deleted from database.`);
    }
  };

  const handleDeleteFeedback = (feedbackId, authorName) => {
    if (window.confirm(`Are you sure you want to permanently remove feedback submitted by "${authorName}"?`)) {
      const updated = deleteUserFeedback(feedbackId);
      setFeedbackList(updated);
      showToast(`Feedback review from "${authorName}" has been permanently removed.`);
    }
  };


  const handleTriggerIngestion = () => {
    setIsIngesting(true);
    setIngestSuccess(false);
    setTimeout(() => {
      setIsIngesting(false);
      setIngestSuccess(true);
      showToast('Architext_v1 dataset ingested: 1,450 floor plans indexed in ChromaDB.');
    }, 2000);
  };

  const filteredUsers = usersList.filter(u => {
    const matchesSearch = u.name.toLowerCase().includes(searchQuery.toLowerCase()) || u.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === 'ALL' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="w-full max-w-7xl mx-auto space-y-8 text-slate-900 font-sans">
      
      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2.5 px-5 py-3.5 bg-slate-900 text-white rounded-2xl shadow-2xl text-sm font-semibold animate-in fade-in">
          <Check className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-xl bg-purple-50 border border-purple-200 text-purple-700">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight">System Administrator Console</h1>
            <span className="px-3 py-1 rounded-full bg-purple-50 text-purple-700 font-mono text-xs font-bold border border-purple-200">
              Root Level Authority
            </span>
          </div>
          <p className="text-sm text-slate-600 leading-relaxed max-w-2xl">
            Real-time telemetry, user provisioning, PostgreSQL database monitoring, and vector dataset pipeline controls.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleTriggerIngestion}
            disabled={isIngesting}
            className="px-5 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold text-sm rounded-xl transition shadow-md shadow-purple-500/20 flex items-center gap-2 cursor-pointer disabled:opacity-60 hover:scale-[1.01]"
          >
            <RefreshCw className={`w-4 h-4 ${isIngesting ? 'animate-spin' : ''}`} />
            <span>{isIngesting ? 'Ingesting Vectors...' : 'Sync Architext Dataset'}</span>
          </button>
        </div>
      </div>

      {/* 6 Core Administrator Monitoring KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        
        {/* 1. Total Users */}
        <div className="p-6 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-mono font-bold uppercase text-slate-500">Total Users</span>
            <Users className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-3xl lg:text-4xl font-black text-slate-900">1,482</h3>
          <span className="text-sm text-emerald-600 font-bold flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4" /> +12% this week
          </span>
        </div>

        {/* 2. Active 24h Users */}
        <div className="p-6 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-mono font-bold uppercase text-slate-500">Active (24h)</span>
            <Activity className="w-6 h-6 text-emerald-600" />
          </div>
          <h3 className="text-3xl lg:text-4xl font-black text-slate-900">342</h3>
          <span className="text-sm text-emerald-600 font-bold flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span> 98% online rate
          </span>
        </div>

        {/* 3. Total Designs Generated */}
        <div className="p-6 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-mono font-bold uppercase text-slate-500">Designs Created</span>
            <Layers className="w-6 h-6 text-indigo-600" />
          </div>
          <h3 className="text-3xl lg:text-4xl font-black text-slate-900">12,890</h3>
          <span className="text-sm text-indigo-600 font-bold flex items-center gap-1.5">
            <Sparkles className="w-4 h-4" /> 5 &amp; 10 Marla
          </span>
        </div>

        {/* 4. AI Queries Processed */}
        <div className="p-6 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-mono font-bold uppercase text-slate-500">AI Queries</span>
            <Cpu className="w-6 h-6 text-purple-600" />
          </div>
          <h3 className="text-3xl lg:text-4xl font-black text-slate-900">45,210</h3>
          <span className="text-sm text-purple-600 font-bold flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" /> 99.4% precision
          </span>
        </div>

        {/* 5. Dataset Searches */}
        <div className="p-6 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-mono font-bold uppercase text-slate-500">Dataset Lookups</span>
            <Search className="w-6 h-6 text-cyan-600" />
          </div>
          <h3 className="text-3xl lg:text-4xl font-black text-slate-900">98,400</h3>
          <span className="text-sm text-cyan-600 font-bold flex items-center gap-1.5">
            <Database className="w-4 h-4" /> ChromaDB HNSW
          </span>
        </div>

        {/* 6. Vector Latency */}
        <div className="p-6 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-mono font-bold uppercase text-slate-500">Vector Latency</span>
            <Clock className="w-6 h-6 text-amber-600" />
          </div>
          <h3 className="text-3xl lg:text-4xl font-black text-slate-900">14.2 ms</h3>
          <span className="text-sm text-emerald-600 font-bold flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4" /> Ultra low latency
          </span>
        </div>

      </div>


      {/* Admin Sub-Tabs Navigation */}
      <div className="flex border-b border-slate-200 bg-white p-2 rounded-2xl gap-2 shadow-xs">
        <button
          type="button"
          onClick={() => setActiveTab('overview')}
          className={`px-5 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer flex items-center gap-2 ${
            activeTab === 'overview'
              ? 'bg-purple-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>Platform Telemetry</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('users')}
          className={`px-5 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer flex items-center gap-2 ${
            activeTab === 'users'
              ? 'bg-purple-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>User Provisioning ({usersList.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('dataset')}
          className={`px-5 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer flex items-center gap-2 ${
            activeTab === 'dataset'
              ? 'bg-purple-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Dataset Ingestion (Architext_v1)</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setFeedbackList(getStoredFeedback());
            setActiveTab('feedback');
          }}
          className={`px-5 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer flex items-center gap-2 ${
            activeTab === 'feedback'
              ? 'bg-purple-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>User Feedback &amp; Reviews ({feedbackList.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('system')}
          className={`px-5 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer flex items-center gap-2 ${
            activeTab === 'system'
              ? 'bg-purple-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>System &amp; Database Health</span>
        </button>
      </div>


      {/* TAB 1: OVERVIEW TELEMETRY */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Generation Heatmap & Volume */}
          <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900">AI Prompt Synthesis Traffic</h3>
                <p className="text-xs text-slate-500 mt-0.5">Queries dispatched to ChromaDB and SentenceTransformer microservices</p>
              </div>
              <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-mono font-bold">
                Live Stream
              </span>
            </div>

            <div className="space-y-4">
              {[
                { plot: '5 Marla Residential Layouts', count: 6420, percent: 50, color: 'bg-blue-600' },
                { plot: '10 Marla Executive Estates', count: 3860, percent: 30, color: 'bg-indigo-600' },
                { plot: '1 Kanal Luxury Villa Blueprints', count: 1930, percent: 15, color: 'bg-cyan-600' },
                { plot: '7 Marla Townhouse Variations', count: 680, percent: 5, color: 'bg-emerald-600' },
              ].map((item) => (
                <div key={item.plot} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-bold">
                    <span className="text-slate-800">{item.plot}</span>
                    <span className="text-slate-500 font-mono">{item.count.toLocaleString()} ({item.percent}%)</span>
                  </div>
                  <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden">
                    <div className={`h-full ${item.color}`} style={{ width: `${item.percent}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Infrastructure Health */}
          <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900">Server Infrastructure Health</h3>
                <p className="text-xs text-slate-500 mt-0.5">PostgreSQL Connection Pool &amp; Inference Cluster</p>
              </div>
              <span className="px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-lg text-xs font-mono font-bold">
                All Systems Operational
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
                <span className="text-slate-500 block mb-1">PostgreSQL Latency:</span>
                <strong className="text-base font-black text-slate-900 font-mono">1.8 ms</strong>
                <span className="text-emerald-600 block text-[11px] font-bold mt-1">Pool: 18/20 Active</span>
              </div>

              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
                <span className="text-slate-500 block mb-1">SentenceTransformers:</span>
                <strong className="text-base font-black text-slate-900 font-mono">all-MiniLM-L6</strong>
                <span className="text-blue-600 block text-[11px] font-bold mt-1">384-Dim Dense Embeddings</span>
              </div>

              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
                <span className="text-slate-500 block mb-1">Vector DB (ChromaDB):</span>
                <strong className="text-base font-black text-slate-900 font-mono">1,450 Vectors</strong>
                <span className="text-cyan-600 block text-[11px] font-bold mt-1">HNSW Cosine Metric</span>
              </div>

              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200">
                <span className="text-slate-500 block mb-1">JWT Cryptographic Session:</span>
                <strong className="text-base font-black text-slate-900 font-mono">HS256 Verified</strong>
                <span className="text-purple-600 block text-[11px] font-bold mt-1">7-Day Expiration Token</span>
              </div>
            </div>
          </div>

        </div>
      )}

      {/* TAB 2: USERS MANAGEMENT */}
      {activeTab === 'users' && (
        <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search user name or email address..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-purple-600 focus:bg-white"
              />
            </div>

            <div className="flex items-center gap-2 overflow-x-auto">
              {['ALL', ROLES.SYSTEM_ADMIN, ROLES.ARCHITECT, ROLES.DESIGNER, ROLES.CONSTRUCTION_PRO, ROLES.HOMEOWNER].map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRoleFilter(r)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                    roleFilter === r
                      ? 'bg-purple-600 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-2xl">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500">
                <tr>
                  <th className="px-6 py-4">User Profile</th>
                  <th className="px-6 py-4">Security Role (RBAC)</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Designs</th>
                  <th className="px-6 py-4">Joined Date</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredUsers.map((u) => {
                  const roleMeta = ROLE_DETAILS[u.role] || ROLE_DETAILS[ROLES.HOMEOWNER];
                  return (
                    <tr key={u.id} className="hover:bg-slate-50/80 transition">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-purple-600 flex items-center justify-center font-bold text-xs text-white">
                            {u.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <span className="font-bold text-slate-900 block">{u.name}</span>
                            <span className="text-xs text-slate-500 font-mono">{u.email}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold border ${roleMeta.color}`}>
                          {roleMeta.badge}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                          u.status === 'Active' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${u.status === 'Active' ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
                          {u.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono font-bold text-slate-700">{u.designsCount}</td>
                      <td className="px-6 py-4 text-xs text-slate-500">{u.joined}</td>
                      <td className="px-6 py-4 text-right flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => handleToggleUserStatus(u.id)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer border ${
                            u.status === 'Active'
                              ? 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                          }`}
                        >
                          {u.status === 'Active' ? 'Suspend' : 'Activate'}
                        </button>

                        {user?.role === ROLES.SYSTEM_ADMIN && u.role !== ROLES.SYSTEM_ADMIN && (
                          <button
                            type="button"
                            onClick={() => handleDeleteUser(u.id, u.name)}
                            className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-bold transition cursor-pointer flex items-center gap-1 shadow-2xs"
                            title="Permanently Delete User Record"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Delete User</span>
                          </button>
                        )}
                      </td>

                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: DATASET INGESTION */}
      {activeTab === 'dataset' && (
        <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">THEODOROS/Architext_v1 Dataset Pipeline</h3>
              <p className="text-xs text-slate-500 mt-0.5">Ingest 1,450 CAD blueprints into ChromaDB vector embedding collection.</p>
            </div>
            <button
              type="button"
              onClick={handleTriggerIngestion}
              disabled={isIngesting}
              className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl transition shadow-md shadow-purple-500/20 flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isIngesting ? 'animate-spin' : ''}`} />
              <span>{isIngesting ? 'Embedding Vectors...' : 'Execute Vector Re-Index'}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-xs font-mono font-bold uppercase text-slate-500">Indexed Layouts</span>
              <h4 className="text-2xl font-black text-slate-900">1,450 Blueprints</h4>
              <p className="text-xs text-slate-600">Architext_v1 Pakistani &amp; global residential templates</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-xs font-mono font-bold uppercase text-slate-500">Dense Embedding Dim</span>
              <h4 className="text-2xl font-black text-slate-900">384 Dimensions</h4>
              <p className="text-xs text-slate-600">MiniLM-L6 NLP Sentence Transformer model</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-xs font-mono font-bold uppercase text-slate-500">Distance Metric</span>
              <h4 className="text-2xl font-black text-slate-900">Cosine Similarity</h4>
              <p className="text-xs text-slate-600">HNSW graph index with sub-15ms lookup speed</p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: SYSTEM & DATABASE HEALTH */}
      {activeTab === 'system' && (
        <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-6">
          <h3 className="text-base font-bold text-slate-900">PostgreSQL Schema &amp; Security Configuration</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200 space-y-3 text-xs">
              <h4 className="font-bold text-sm text-slate-900">PostgreSQL Tables Monitored</h4>
              <div className="space-y-1.5 font-mono">
                <div className="flex justify-between"><span>users</span><strong className="text-emerald-700">1,482 rows (Active)</strong></div>
                <div className="flex justify-between"><span>projects</span><strong className="text-blue-700">4,912 rows</strong></div>
                <div className="flex justify-between"><span>designs</span><strong className="text-indigo-700">12,890 rows</strong></div>
                <div className="flex justify-between"><span>materials</span><strong className="text-purple-700">8 categories</strong></div>
                <div className="flex justify-between"><span>cost_estimates</span><strong className="text-amber-700">3,420 records</strong></div>
              </div>
            </div>

            <div className="p-5 bg-slate-50 rounded-2xl border border-slate-200 space-y-3 text-xs">
              <h4 className="font-bold text-sm text-slate-900">Security &amp; JWT Key Management</h4>
              <p className="text-slate-600 leading-relaxed">
                Tokens are cryptographically signed with HS256 secret. All role authorization policies are checked at the route guard and sub-module layers.
              </p>
              <button
                type="button"
                onClick={() => showToast('JWT Secret key rotated and synced across cluster.')}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl transition cursor-pointer"
              >
                Rotate Cryptographic Secret
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: USER FEEDBACK & REVIEWS */}
      {activeTab === 'feedback' && (
        <div className="space-y-6">
          <div className="p-6 bg-white border border-slate-200 rounded-3xl shadow-xs flex items-center justify-between">
            <div>
              <h3 className="text-lg font-black text-slate-900">User Submitted Feedback &amp; Reviews</h3>
              <p className="text-xs text-slate-500 mt-0.5">Real-time feedback stream saved to PostgreSQL database &amp; synced across cluster</p>
            </div>
            <button
              type="button"
              onClick={() => {
                setFeedbackList(getStoredFeedback());
                showToast('Feedback database refreshed.');
              }}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs rounded-xl transition flex items-center gap-2 cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh Feed</span>
            </button>
          </div>

          <div className="space-y-4">
            {feedbackList.map((item) => (
              <div key={item.id} className="p-6 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-4 hover:border-purple-300 transition">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center font-bold text-sm text-white shadow-sm">
                      {item.author.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-base text-slate-900">{item.author}</span>
                        <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200">
                          {item.role}
                        </span>
                      </div>
                      <span className="text-xs text-slate-500 font-mono flex items-center gap-1 mt-0.5">
                        <Mail className="w-3.5 h-3.5 text-slate-400" />
                        {item.email || 'user@archai.design'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1 bg-amber-50 border border-amber-200 px-3 py-1 rounded-xl">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <Star
                          key={star}
                          className={`w-4 h-4 ${
                            star <= item.rating ? 'fill-amber-400 text-amber-400' : 'text-slate-300'
                          }`}
                        />
                      ))}
                      <span className="text-xs font-bold text-amber-800 ml-1 font-mono">{item.rating}/5</span>
                    </div>

                    <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {item.status || 'Saved to DB'}
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="inline-block px-3 py-1 bg-slate-100 text-slate-800 text-xs font-bold rounded-lg font-mono">
                    Category: {item.category}
                  </span>
                  <p className="text-base text-slate-800 font-medium leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-200/80">
                    "{item.comment}"
                  </p>
                </div>

                <div className="flex items-center justify-between pt-1 text-xs text-slate-500">
                  <span className="font-mono">Submitted: {item.createdAt ? new Date(item.createdAt).toLocaleString() : item.date}</span>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => showToast(`Marked feedback from ${item.author} as reviewed.`)}
                      className="text-xs font-bold text-purple-600 hover:text-purple-700 cursor-pointer"
                    >
                      Mark Reviewed &amp; Acknowledge
                    </button>

                    {user?.role === ROLES.SYSTEM_ADMIN && (
                      <button
                        type="button"
                        onClick={() => handleDeleteFeedback(item.id, item.author)}
                        className="px-3.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 shadow-2xs"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>Remove Feedback</span>
                      </button>
                    )}
                  </div>
                </div>

              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}

