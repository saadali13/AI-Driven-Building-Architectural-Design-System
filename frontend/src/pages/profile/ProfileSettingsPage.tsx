import React, { useState } from 'react';
import {
  User,
  Mail,
  Phone,
  Shield,
  KeyRound,
  CheckCircle2,
  Lock,
  Building,
  Save,
  LogOut,
  AlertCircle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export const ProfileSettingsPage: React.FC = () => {
  const { currentUser, updateProfile, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'security'>('profile');

  // Profile Form
  const [name, setName] = useState(currentUser?.name || '');
  const [email, setEmail] = useState(currentUser?.email || '');
  const [phone, setPhone] = useState(currentUser?.phone || '');
  const [firmName, setFirmName] = useState(currentUser?.firmName || '');
  const [profileSaved, setProfileSaved] = useState(false);

  // Preferences Form
  const [measurementUnit, setMeasurementUnit] = useState<'feet' | 'meters' | 'yards'>('feet');
  const [defaultCurrency, setDefaultCurrency] = useState<'PKR' | 'USD'>('PKR');
  const [prefSaved, setPrefSaved] = useState(false);

  // Security Form
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState('');

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({
      name,
      email,
      phone,
      firmName,
    });
    setProfileSaved(true);
    setTimeout(() => setProfileSaved(false), 2500);
  };

  const handlePreferencesSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPrefSaved(true);
    setTimeout(() => setPrefSaved(false), 2500);
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');

    if (newPassword.length < 6) {
      setPasswordError('New password must be at least 6 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match.');
      return;
    }

    setPasswordSuccess(true);
    setOldPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setTimeout(() => setPasswordSuccess(false), 3000);
  };

  return (
    <div className="space-y-6 pb-16 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-[#E2E7E1] pb-5">
        <h1 className="text-2xl sm:text-3xl font-bold text-[#202923] font-heading">
          Profile & Application Settings
        </h1>
        <p className="text-xs text-[#68736C] mt-1">
          Manage your personal details, architectural measurement units, and security credentials.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-[#E2E7E1] pb-2 text-xs">
        {[
          { id: 'profile', label: 'Profile Information' },
          { id: 'preferences', label: 'Units & Defaults' },
          { id: 'security', label: 'Account Security' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-xl font-semibold transition-all ${
              activeTab === tab.id
                ? 'bg-[#23483D] text-white shadow-xs'
                : 'text-[#68736C] hover:text-[#202923] hover:bg-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: PROFILE */}
      {activeTab === 'profile' && (
        <form onSubmit={handleProfileSubmit} className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-8 shadow-xs space-y-5 text-xs">
          {profileSaved && (
            <div className="p-3.5 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] text-[#23483D] flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              <span>Profile details updated successfully.</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[#68736C] font-semibold mb-1">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
              />
            </div>

            <div>
              <label className="block text-[#68736C] font-semibold mb-1">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
              />
            </div>

            <div>
              <label className="block text-[#68736C] font-semibold mb-1">Phone Number</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
              />
            </div>

            <div>
              <label className="block text-[#68736C] font-semibold mb-1">Firm / Organization</label>
              <input
                type="text"
                value={firmName}
                onChange={(e) => setFirmName(e.target.value)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
                placeholder="e.g. Studio Mansoor Architects"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white font-semibold flex items-center gap-2 shadow-xs"
            >
              <Save className="h-4 w-4" />
              <span>Save Profile Changes</span>
            </button>
          </div>
        </form>
      )}

      {/* TAB 2: PREFERENCES */}
      {activeTab === 'preferences' && (
        <form onSubmit={handlePreferencesSubmit} className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-8 shadow-xs space-y-5 text-xs">
          {prefSaved && (
            <div className="p-3.5 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] text-[#23483D] flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              <span>Preferences saved.</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[#68736C] font-semibold mb-1">Measurement System</label>
              <select
                value={measurementUnit}
                onChange={(e) => setMeasurementUnit(e.target.value as any)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
              >
                <option value="feet">Imperial Feet (Standard in Pakistan: 25x45 ft)</option>
                <option value="meters">Metric Meters (MKS)</option>
                <option value="yards">Square Yards (Guz)</option>
              </select>
            </div>

            <div>
              <label className="block text-[#68736C] font-semibold mb-1">Default Currency</label>
              <select
                value={defaultCurrency}
                onChange={(e) => setDefaultCurrency(e.target.value as any)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
              >
                <option value="PKR">PKR (Pakistani Rupee - Lakhs/Crores)</option>
                <option value="USD">USD (US Dollar)</option>
              </select>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white font-semibold flex items-center gap-2 shadow-xs"
            >
              <Save className="h-4 w-4" />
              <span>Save Defaults</span>
            </button>
          </div>
        </form>
      )}

      {/* TAB 3: SECURITY */}
      {activeTab === 'security' && (
        <form onSubmit={handlePasswordSubmit} className="bg-white border border-[#E2E7E1] rounded-2xl p-6 sm:p-8 shadow-xs space-y-5 text-xs max-w-lg">
          {passwordSuccess && (
            <div className="p-3.5 rounded-xl bg-[#EEF4F0] border border-[#DCE7DE] text-[#23483D] flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              <span>Password updated successfully.</span>
            </div>
          )}

          {passwordError && (
            <div className="p-3.5 rounded-xl bg-[#FEF2F2] border border-[#FCA5A5] text-[#DC2626] flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              <span>{passwordError}</span>
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-[#68736C] font-semibold mb-1">Current Password</label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
              />
            </div>

            <div>
              <label className="block text-[#68736C] font-semibold mb-1">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
              />
            </div>

            <div>
              <label className="block text-[#68736C] font-semibold mb-1">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-[#F7F7F2] border border-[#E2E7E1] rounded-xl px-3 py-2 text-[#202923] focus:outline-none focus:border-[#23483D]"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-[#23483D] hover:bg-[#1A372E] text-white font-semibold flex items-center gap-2 shadow-xs"
            >
              <Lock className="h-4 w-4" />
              <span>Change Password</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
