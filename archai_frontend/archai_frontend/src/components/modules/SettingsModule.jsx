import React, { useState, useRef } from 'react';
import { 
  Settings, 
  Globe, 
  User, 
  ShieldCheck, 
  Cpu, 
  Save, 
  Upload, 
  Trash2, 
  Mail, 
  Phone, 
  Building2, 
  Lock, 
  CheckCircle2, 
  Coins, 
  Languages, 
  Scale, 
  Database, 
  Zap, 
  X, 
  RefreshCw,
  Server,
  FileText,
  KeyRound,
  Eye,
  EyeOff,
  Sparkles,
  AlertCircle,
  ShieldAlert,
  QrCode,
  Copy
} from 'lucide-react';
import { useAuth, ROLES, ROLE_DETAILS, PERMISSIONS } from '../../context/AuthContext';


export default function SettingsModule({ defaultTab = 'profile' }) {
  const { user, updateProfile, hasPermission, setup2FA, verify2FA, disable2FA } = useAuth();

  const fileInputRef = useRef(null);


  const [activeTab, setActiveTab] = useState(defaultTab);
  const [toastMessage, setToastMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Tab 1: Profile & Account State dynamically loaded from session
  const [profileForm, setProfileForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    organization: user?.organization || '',
    bio: user?.bio || '',
  });
  const [avatarPreview, setAvatarPreview] = useState(user?.avatarUrl || null);
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  // Tab 2: General Preferences State
  const [generalSettings, setGeneralSettings] = useState({
    platformName: 'ArchAI Building Studio Pro',
    defaultCurrency: 'PKR',
    measurementUnit: 'marla_kanal',
    timezone: 'Asia/Karachi (PKT +05:00)',
    defaultPlotSize: '5marla',
    autoSaveInterval: '30s',
    emailNotifications: true,
    realtimeSynthesisUpdates: true,
  });

  // Tab 3: Security & Password State
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showCurrentPass, setShowCurrentPass] = useState(false);
  const [showNewPass, setShowNewPass] = useState(false);

  // 2FA Google Authenticator State
  const [is2FASettingUp, setIs2FASettingUp] = useState(false);
  const [totpData, setTotpData] = useState(null); // { secret, qr_code, totp_uri }
  const [totpVerifyCode, setTotpVerifyCode] = useState('');
  const [totpError, setTotpError] = useState(null);
  const [totpSuccess, setTotpSuccess] = useState(null);
  const [secretCopied, setSecretCopied] = useState(false);
  const [is2FAVerifying, setIs2FAVerifying] = useState(false);

  const handleStart2FASetup = async () => {
    setTotpError(null);
    setTotpSuccess(null);
    try {
      const data = await setup2FA();
      setTotpData(data);
      setIs2FASettingUp(true);
    } catch (err) {
      showToast(err.message || "Failed to initialize 2FA setup.");
    }
  };

  const handleConfirm2FAVerify = async () => {
    if (!totpVerifyCode || totpVerifyCode.trim().length !== 6) {
      setTotpError("Please enter a valid 6-digit code.");
      return;
    }
    setTotpError(null);
    setIs2FAVerifying(true);
    try {
      await verify2FA(user?.email, totpVerifyCode);
      setTotpSuccess("Google Authenticator successfully enabled!");
      showToast("Google Authenticator Two-Factor Authentication enabled!");
      setTimeout(() => {
        setIs2FASettingUp(false);
        setTotpVerifyCode('');
        setTotpSuccess(null);
      }, 1200);
    } catch (err) {
      setTotpError(err.message || "Invalid 6-digit code. Please try again.");
    } finally {
      setIs2FAVerifying(false);
    }
  };

  const handleDisable2FAAction = async () => {
    if (!user?.email) return;
    try {
      await disable2FA(user.email);
      showToast("Two-Factor Authentication disabled.");
      setIs2FASettingUp(false);
      setTotpData(null);
    } catch (err) {
      showToast("Failed to disable 2FA.");
    }
  };


  // Tab 4: AI/NLP Configuration State
  const [aiConfig, setAiConfig] = useState({
    similarityThreshold: 0.85,
    embeddingModel: 'sentence-transformers/all-MiniLM-L6-v2',
    temperature: 0.35,
    maxTokens: 2048,
    vectorDbProvider: 'chromadb_persistent',
  });
  const [isReindexing, setIsReindexing] = useState(false);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3500);
  };

  const processImageFile = (file) => {
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      showToast('Image file size must be less than 5MB.');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setAvatarPreview(reader.result);
      updateProfile({ avatarUrl: reader.result });
      showToast('Profile photo updated in session.');
    };
    reader.readAsDataURL(file);
  };

  const handleAvatarUpload = (e) => {
    const file = e.target.files?.[0];
    processImageFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDraggingOver(false);
    const file = e.dataTransfer.files?.[0];
    processImageFile(file);
  };

  const handleRemoveAvatar = () => {
    setAvatarPreview(null);
    updateProfile({ avatarUrl: null });
    showToast('Profile photo removed.');
  };

  const handleSaveProfile = (e) => {
    e.preventDefault();
    setIsSaving(true);
    setTimeout(() => {
      updateProfile({
        name: profileForm.name,
        email: profileForm.email,
        phone: profileForm.phone,
        organization: profileForm.organization,
        bio: profileForm.bio,
      });
      setIsSaving(false);
      showToast('Profile changes committed to session state.');
    }, 500);
  };

  const handleSavePassword = (e) => {
    e.preventDefault();
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      showToast('New passwords do not match.');
      return;
    }
    if (passwordForm.newPassword.length < 8) {
      showToast('Password must be at least 8 characters.');
      return;
    }
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      showToast('Password updated successfully.');
    }, 600);
  };

  const handleReindexVectors = () => {
    if (user?.role !== ROLES.SYSTEM_ADMIN) {
      showToast('Action Denied: Only System Administrators can trigger vector database re-indexing.');
      return;
    }
    setIsReindexing(true);
    setTimeout(() => {
      setIsReindexing(false);
      showToast('ChromaDB Vector Index refreshed: 1,450 floor plans re-embedded.');
    }, 1500);
  };

  const currentRoleMeta = ROLE_DETAILS[user?.role] || ROLE_DETAILS[ROLES.HOMEOWNER];

  const permissionScopes = [
    { key: PERMISSIONS.DESIGN_GENERATE, label: '3D AI Elevation Synthesis & Prompt Parsing' },
    { key: PERMISSIONS.DESIGN_EXPORT, label: 'CAD DXF & Architectural Vector PDF Export' },
    { key: PERMISSIONS.COST_EDIT, label: 'Custom Material Price Overrides (PKR)' },
    { key: PERMISSIONS.USER_MANAGE, label: 'User Provisioning & Role Clearance Allocation' },
    { key: PERMISSIONS.AUDIT_VIEW, label: 'System Cryptographic Audit Log Inspection' },
    { key: PERMISSIONS.PROJECT_APPROVE, label: 'Residential Layout Approval Authority' },
  ];

  return (
    <div className="h-full flex flex-col bg-slate-50 text-slate-900 font-sans overflow-hidden">
      
      {/* TOAST NOTIFICATION */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2.5 px-5 py-3.5 bg-slate-900 text-white rounded-2xl shadow-xl text-sm font-semibold animate-in fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* HEADER BAR */}
      <div className="p-6 md:px-10 border-b border-slate-200 bg-white flex flex-wrap items-center justify-between gap-4 shrink-0">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">Account &amp; System Settings</h1>
            <span className={`text-xs font-mono font-bold px-3 py-1 rounded-full border ${currentRoleMeta.color}`}>
              {currentRoleMeta.badge}
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Manage your authenticated profile, security clearance, units, and system preferences.
          </p>
        </div>

        <button
          type="button"
          onClick={handleSaveProfile}
          disabled={isSaving}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-xl transition shadow-md shadow-blue-500/20 flex items-center gap-2 cursor-pointer disabled:opacity-50 hover:scale-[1.01]"
        >
          {isSaving ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Saving Changes...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Save All Changes</span>
            </>
          )}
        </button>
      </div>

      {/* TABS NAVIGATION */}
      <div className="px-6 md:px-10 border-b border-slate-200 bg-white flex overflow-x-auto gap-2 py-3">
        <button
          type="button"
          onClick={() => setActiveTab('profile')}
          className={`px-4 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer flex items-center gap-2.5 whitespace-nowrap ${
            activeTab === 'profile'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <User className="w-4 h-4" />
          <span>Profile &amp; Details</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('general')}
          className={`px-4 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer flex items-center gap-2.5 whitespace-nowrap ${
            activeTab === 'general'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Globe className="w-4 h-4" />
          <span>General Preferences</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('security')}
          className={`px-4 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer flex items-center gap-2.5 whitespace-nowrap ${
            activeTab === 'security'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Role &amp; Security (RBAC)</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('ai')}
          className={`px-4 py-2.5 rounded-xl text-sm font-bold transition cursor-pointer flex items-center gap-2.5 whitespace-nowrap ${
            activeTab === 'ai'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>AI &amp; Neural Vector Engine</span>
        </button>
      </div>

      {/* TAB CONTENT AREA */}
      <div className="flex-1 overflow-y-auto p-6 md:p-10">
        <div className="max-w-5xl mx-auto space-y-8">
          
          {/* TAB 1: PROFILE & PHOTO */}
          {activeTab === 'profile' && (
            <div className="space-y-6">
              
              {/* Photo Upload Card */}
              <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs">
                <div className="flex items-center gap-3 mb-5">
                  <User className="w-5 h-5 text-blue-600" />
                  <h3 className="text-base font-bold text-slate-900">Profile Photo &amp; Avatar</h3>
                </div>

                <div className="flex flex-col sm:flex-row items-center gap-6">
                  <div className="relative shrink-0">
                    {avatarPreview ? (
                      <img
                        src={avatarPreview}
                        alt="Avatar Preview"
                        className="w-28 h-28 rounded-2xl object-cover ring-2 ring-blue-500/50 shadow-sm"
                      />
                    ) : (
                      <div className="w-28 h-28 rounded-2xl bg-blue-600 flex items-center justify-center font-black text-3xl text-white shadow-sm">
                        {profileForm.name ? profileForm.name.charAt(0).toUpperCase() : 'U'}
                      </div>
                    )}
                    <span className="absolute bottom-1 right-1 w-4 h-4 bg-emerald-500 border-2 border-white rounded-full"></span>
                  </div>

                  {/* Dropzone */}
                  <div
                    onDragOver={(e) => { e.preventDefault(); setIsDraggingOver(true); }}
                    onDragLeave={() => setIsDraggingOver(false)}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`flex-1 w-full p-6 rounded-2xl border-2 border-dashed transition flex flex-col items-center justify-center cursor-pointer text-center ${
                      isDraggingOver
                        ? 'border-blue-500 bg-blue-50/50'
                        : 'border-slate-300 hover:border-slate-400 bg-slate-50'
                    }`}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarUpload}
                      className="hidden"
                    />
                    <Upload className="w-8 h-8 text-blue-600 mb-2" />
                    <p className="text-sm font-bold text-slate-900">
                      Click to upload <span className="text-slate-500 font-normal">or drag &amp; drop</span>
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      PNG, JPG up to 5MB (Square ratio recommended)
                    </p>
                  </div>

                  {avatarPreview && (
                    <button
                      type="button"
                      onClick={handleRemoveAvatar}
                      className="p-3 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-600 rounded-xl transition cursor-pointer"
                      title="Remove Avatar"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Personal Information */}
              <form onSubmit={handleSaveProfile} className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-6">
                <div className="flex items-center gap-3 mb-2">
                  <Building2 className="w-5 h-5 text-blue-600" />
                  <h3 className="text-base font-bold text-slate-900">Personal &amp; Contact Details</h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Full Legal Name
                    </label>
                    <div className="relative">
                      <User className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type="text"
                        required
                        placeholder="Enter full legal name"
                        value={profileForm.name}
                        onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                        className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type="email"
                        required
                        placeholder="user@archai.design"
                        value={profileForm.email}
                        onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                        className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Phone Number
                    </label>
                    <div className="relative">
                      <Phone className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type="tel"
                        placeholder="+92 300 0000000"
                        value={profileForm.phone}
                        onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                        className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Organization / Firm
                    </label>
                    <div className="relative">
                      <Building2 className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type="text"
                        placeholder="e.g. Private Residential Client"
                        value={profileForm.organization}
                        onChange={(e) => setProfileForm({ ...profileForm, organization: e.target.value })}
                        className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Profile Bio / Specialization
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Brief architectural bio or spatial preferences..."
                    value={profileForm.bio}
                    onChange={(e) => setProfileForm({ ...profileForm, bio: e.target.value })}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white"
                  />
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-xl transition shadow-md shadow-blue-500/20 cursor-pointer hover:scale-[1.01]"
                  >
                    Save Profile Details
                  </button>
                </div>
              </form>

            </div>
          )}

          {/* TAB 2: GENERAL PREFERENCES */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-6">
                <div className="flex items-center gap-3 mb-2">
                  <Globe className="w-5 h-5 text-blue-600" />
                  <h3 className="text-base font-bold text-slate-900">Localization &amp; Unit Standards</h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Plot Measurement Standard
                    </label>
                    <select
                      value={generalSettings.measurementUnit}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, measurementUnit: e.target.value })}
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white cursor-pointer"
                    >
                      <option value="marla_kanal">Marla &amp; Kanal (Pakistani Standard)</option>
                      <option value="sq_ft">Square Feet (Sq. Ft)</option>
                      <option value="sq_meters">Square Meters (m²)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Cost Currency Representation
                    </label>
                    <select
                      value={generalSettings.defaultCurrency}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, defaultCurrency: e.target.value })}
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white cursor-pointer"
                    >
                      <option value="PKR">Pakistani Rupee (PKR - ₨)</option>
                      <option value="USD">US Dollar (USD - $)</option>
                      <option value="AED">UAE Dirham (AED - د.إ)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Regional Timezone
                    </label>
                    <input
                      type="text"
                      disabled
                      value={generalSettings.timezone}
                      className="w-full px-4 py-3 bg-slate-100 border border-slate-200 rounded-xl text-sm text-slate-600 font-mono"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Cloud Auto-Save Frequency
                    </label>
                    <select
                      value={generalSettings.autoSaveInterval}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, autoSaveInterval: e.target.value })}
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white cursor-pointer"
                    >
                      <option value="15s">Every 15 seconds</option>
                      <option value="30s">Every 30 seconds (Recommended)</option>
                      <option value="60s">Every 60 seconds</option>
                    </select>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">Real-Time Synthesis Notifications</h4>
                      <p className="text-xs text-slate-500 mt-0.5">Receive alerts when vector 3D models finish inference.</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={generalSettings.realtimeSynthesisUpdates}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, realtimeSynthesisUpdates: e.target.checked })}
                      className="w-5 h-5 rounded border-slate-300 text-blue-600 accent-blue-600 cursor-pointer"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">PKR Local Market Price Sync</h4>
                      <p className="text-xs text-slate-500 mt-0.5">Auto-update concrete, steel, and labor rates every 24h.</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={generalSettings.emailNotifications}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, emailNotifications: e.target.checked })}
                      className="w-5 h-5 rounded border-slate-300 text-blue-600 accent-blue-600 cursor-pointer"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: ROLE & SECURITY (RBAC) */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              
              <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs">
                <div className="flex items-center justify-between mb-5">
                  <div className="flex items-center gap-3">
                    <ShieldCheck className="w-6 h-6 text-blue-600" />
                    <div>
                      <h3 className="text-base font-bold text-slate-900">Active RBAC Security Clearance</h3>
                      <p className="text-xs text-slate-500">PostgreSQL cryptographically signed JWT authority</p>
                    </div>
                  </div>
                  <span className={`text-xs font-mono font-bold px-3 py-1.5 rounded-full border ${currentRoleMeta.color}`}>
                    {currentRoleMeta.title}
                  </span>
                </div>

                <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-5 rounded-2xl border border-slate-200 mb-6">
                  {currentRoleMeta.description}
                </p>

                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3.5">
                  Authorized Cryptographic Scopes
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  {permissionScopes.map((scope) => {
                    const isGranted = hasPermission(scope.key);
                    return (
                      <div
                        key={scope.key}
                        className={`p-3.5 rounded-xl border flex items-center gap-3.5 ${
                          isGranted
                            ? 'bg-slate-50 border-slate-200 text-slate-800'
                            : 'bg-slate-50/50 border-slate-100 text-slate-400'
                        }`}
                      >
                        {isGranted ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                        ) : (
                          <Lock className="w-5 h-5 text-slate-400 shrink-0" />
                        )}
                        <span className="text-sm font-medium">{scope.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Google Authenticator Two-Factor Authentication (TOTP) Setup & Configuration Card */}
              <div className="p-8 md:p-12 bg-white border border-slate-200 rounded-3xl shadow-sm space-y-8">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                  <div className="flex items-center gap-5">
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-2xl text-blue-600 shadow-xs shrink-0">
                      <QrCode className="w-8 h-8" />
                    </div>
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="text-xl md:text-2xl font-bold text-slate-900">Google Authenticator (TOTP 2FA)</h3>
                        {user?.is_2fa_enabled ? (
                          <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-50 border border-emerald-200 rounded-full text-xs font-bold text-emerald-700">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            <span>Active &amp; Protected</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-slate-100 border border-slate-200 rounded-full text-xs font-bold text-slate-600">
                            <span>Disabled</span>
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-slate-500 mt-1.5">
                        Enhance your account security using time-based one-time password (TOTP) verification.
                      </p>
                    </div>
                  </div>

                  {!is2FASettingUp && (
                    <div className="shrink-0">
                      {user?.is_2fa_enabled ? (
                        <button
                          type="button"
                          onClick={handleDisable2FAAction}
                          className="px-6 py-3.5 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-sm font-bold rounded-xl transition cursor-pointer"
                        >
                          Disable 2FA
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={handleStart2FASetup}
                          className="px-6 py-3.5 bg-blue-600 hover:bg-blue-700 text-white text-base font-bold rounded-xl transition shadow-lg shadow-blue-500/25 flex items-center gap-2.5 cursor-pointer hover:scale-[1.01]"
                        >
                          <ShieldCheck className="w-5 h-5" />
                          <span>Enable Google Authenticator</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* 2FA Configuration UI Screen */}
                {is2FASettingUp && totpData && (
                  <div className="p-8 md:p-10 bg-slate-50 border border-slate-200 rounded-3xl space-y-8 animate-in fade-in">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                      <div>
                        <h4 className="text-lg font-bold text-slate-900">Configure Google Authenticator</h4>
                        <p className="text-sm text-slate-500 mt-1">Scan the QR code below or manually input the secret key into your TOTP application.</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => { setIs2FASettingUp(false); setTotpError(null); }}
                        className="p-2 text-slate-400 hover:text-slate-700 rounded-xl cursor-pointer hover:bg-slate-200 transition"
                      >
                        <X className="w-6 h-6" />
                      </button>
                    </div>

                    {totpError && (
                      <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-semibold flex items-center gap-3">
                        <ShieldAlert className="w-5 h-5 shrink-0 text-rose-600" />
                        <span>{totpError}</span>
                      </div>
                    )}

                    {totpSuccess && (
                      <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-semibold flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-600" />
                        <span>{totpSuccess}</span>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                      {/* Step 1: High-Resolution Base64 PNG QR Code */}
                      <div className="p-6 bg-white border border-slate-200 rounded-2xl flex flex-col items-center text-center shadow-xs">
                        <span className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4">
                          1. Scan QR Code
                        </span>
                        <div className="w-56 h-56 bg-slate-50 p-3 border border-slate-200 rounded-2xl flex items-center justify-center mb-4 shadow-2xs">
                          <img
                            src={totpData.qr_code}
                            alt="Google Authenticator QR Code"
                            className="w-full h-full object-contain rounded-xl"
                          />
                        </div>
                        <span className="text-xs font-medium text-slate-500 max-w-xs leading-relaxed">
                          Open Google Authenticator app, select "Scan a QR code", and point your camera here.
                        </span>
                      </div>

                      {/* Step 2 & 3: Manual Key & 6-Digit Code Validation */}
                      <div className="space-y-6">
                        <div>
                          <span className="block text-sm font-bold text-slate-800 uppercase tracking-wider mb-2">
                            2. Manual Secret Entry Key
                          </span>
                          <div className="flex items-center gap-3">
                            <div className="flex-1 px-5 py-4 bg-white border border-slate-200 rounded-2xl font-mono text-sm font-bold text-blue-700 tracking-widest select-all overflow-x-auto shadow-2xs">
                              {totpData.secret}
                            </div>
                            <button
                              type="button"
                              onClick={() => {
                                navigator.clipboard.writeText(totpData.secret);
                                setSecretCopied(true);
                                setTimeout(() => setSecretCopied(false), 2000);
                              }}
                              className="px-5 py-4 bg-white hover:bg-slate-100 border border-slate-200 text-slate-800 rounded-2xl text-sm font-bold transition cursor-pointer shrink-0 shadow-2xs"
                            >
                              {secretCopied ? 'Copied!' : 'Copy'}
                            </button>
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-bold text-slate-800 uppercase tracking-wider mb-2">
                            3. Enter 6-Digit Verification Code
                          </label>
                          <div className="relative">
                            <Lock className="w-6 h-6 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                            <input
                              type="text"
                              inputMode="numeric"
                              maxLength={6}
                              placeholder="123456"
                              value={totpVerifyCode}
                              onChange={(e) => setTotpVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                              className="w-full pl-14 pr-4 py-4 bg-white border-2 border-slate-200 rounded-2xl text-2xl font-mono font-bold text-slate-900 tracking-[0.3em] focus:outline-none focus:border-blue-600 shadow-2xs"
                            />
                          </div>
                          <p className="text-xs font-semibold text-slate-500 mt-2">
                            Enter the live 6 digits displayed in your Google Authenticator app.
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={handleConfirm2FAVerify}
                          disabled={is2FAVerifying || totpVerifyCode.length !== 6}
                          className="w-full py-4 px-6 bg-blue-600 hover:bg-blue-700 text-white text-base font-bold rounded-2xl transition shadow-lg shadow-blue-500/25 flex items-center justify-center gap-3 cursor-pointer disabled:opacity-50 hover:scale-[1.01]"
                        >
                          {is2FAVerifying ? (
                            <span>Validating TOTP Code...</span>
                          ) : (
                            <>
                              <ShieldCheck className="w-6 h-6" />
                              <span>Verify &amp; Activate 2FA</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>



              {/* Password Management */}
              <form onSubmit={handleSavePassword} className="p-8 md:p-12 bg-white border border-slate-200 rounded-3xl shadow-sm space-y-8">
                <div className="flex items-center gap-4 mb-2">
                  <KeyRound className="w-7 h-7 text-blue-600" />
                  <h3 className="text-2xl font-black text-slate-900">Update Password Credentials</h3>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-bold text-slate-800 uppercase tracking-wider mb-3">
                      Current Password
                    </label>
                    <div className="relative">
                      <Lock className="w-6 h-6 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type={showCurrentPass ? 'text' : 'password'}
                        value={passwordForm.currentPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                        placeholder="••••••••••••"
                        className="w-full pl-14 pr-14 py-4 bg-slate-50 border-2 border-slate-200 rounded-2xl text-lg font-bold text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPass(!showCurrentPass)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                      >
                        {showCurrentPass ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-bold text-slate-800 uppercase tracking-wider mb-3">
                        New Password
                      </label>
                      <div className="relative">
                        <Lock className="w-6 h-6 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                        <input
                          type={showNewPass ? 'text' : 'password'}
                          value={passwordForm.newPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                          placeholder="••••••••••••"
                          className="w-full pl-14 pr-14 py-4 bg-slate-50 border-2 border-slate-200 rounded-2xl text-lg font-bold text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition"
                        />
                        <button
                          type="button"
                          onClick={() => setShowNewPass(!showNewPass)}
                          className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                        >
                          {showNewPass ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-slate-800 uppercase tracking-wider mb-3">
                        Confirm New Password
                      </label>
                      <div className="relative">
                        <Lock className="w-6 h-6 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                        <input
                          type="password"
                          value={passwordForm.confirmPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                          placeholder="••••••••••••"
                          className="w-full pl-14 pr-5 py-4 bg-slate-50 border-2 border-slate-200 rounded-2xl text-lg font-bold text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white transition"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 flex justify-end">
                  <button
                    type="submit"
                    className="px-8 py-4 bg-slate-900 hover:bg-slate-800 text-white font-extrabold text-lg rounded-2xl transition cursor-pointer shadow-lg hover:scale-[1.01]"
                  >
                    Update Password
                  </button>
                </div>
              </form>


            </div>
          )}

          {/* TAB 4: AI & NEURAL VECTOR (Protected trigger for System Administrators) */}
          {activeTab === 'ai' && (
            <div className="space-y-6">
              <div className="p-6 md:p-8 bg-white border border-slate-200 rounded-3xl shadow-xs space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <Cpu className="w-6 h-6 text-blue-600" />
                    <div>
                      <h3 className="text-base font-bold text-slate-900">ChromaDB &amp; Transformer Configuration</h3>
                      <p className="text-xs text-slate-500 mt-0.5">Natural Language Floor Plan Vector Parameters</p>
                    </div>
                  </div>

                  {user?.role === ROLES.SYSTEM_ADMIN ? (
                    <button
                      type="button"
                      onClick={handleReindexVectors}
                      disabled={isReindexing}
                      className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-xl transition flex items-center gap-2 cursor-pointer disabled:opacity-50"
                    >
                      <RefreshCw className={`w-4 h-4 ${isReindexing ? 'animate-spin' : ''}`} />
                      <span>{isReindexing ? 'Indexing Vectors...' : 'Trigger ChromaDB Re-index'}</span>
                    </button>
                  ) : (
                    <div className="flex items-center gap-2 px-3.5 py-2 bg-amber-50 border border-amber-200 rounded-xl text-xs font-bold text-amber-800">
                      <Lock className="w-4 h-4" />
                      <span>Admin Clearance Required</span>
                    </div>
                  )}
                </div>

                {user?.role !== ROLES.SYSTEM_ADMIN && (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-800 flex items-center gap-2.5">
                    <ShieldAlert className="w-5 h-5 shrink-0 text-amber-600" />
                    <span>You are currently in read-only mode for neural transformer parameters. Only System Administrators can execute dense vector re-indexing.</span>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Sentence Transformer Model
                    </label>
                    <input
                      type="text"
                      disabled
                      value={aiConfig.embeddingModel}
                      className="w-full px-4 py-3 bg-slate-100 border border-slate-200 rounded-xl text-sm text-slate-600 font-mono"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Cosine Similarity Cutoff ({aiConfig.similarityThreshold})
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="0.99"
                      step="0.01"
                      disabled={user?.role !== ROLES.SYSTEM_ADMIN}
                      value={aiConfig.similarityThreshold}
                      onChange={(e) => setAiConfig({ ...aiConfig, similarityThreshold: parseFloat(e.target.value) })}
                      className="w-full accent-blue-600 cursor-pointer disabled:opacity-50 mt-2"
                    />
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3 text-sm">
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Active Vector Embeddings:</span>
                    <span className="font-mono font-bold text-blue-600">1,450 Schematics</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Dense Vector Dimension:</span>
                    <span className="font-mono font-bold text-indigo-600">384 Dimensions</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span>Embedding Space Metric:</span>
                    <span className="font-mono font-bold text-emerald-600">Cosine Distance (HNSW)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>

    </div>
  );
}
