import React, { useState, useRef } from 'react';
import { 
  ArrowLeft, 
  Mail, 
  Lock, 
  User, 
  UserPlus,
  Eye, 
  EyeOff, 
  Sparkles, 
  ShieldCheck, 
  ArrowRight, 
  CheckCircle2, 
  Building2, 
  Layers, 
  Cpu, 
  ShieldAlert, 
  Check, 
  KeyRound,
  Compass,
  Globe,
  Phone,
  Upload,
  Camera,
  Trash2,
  HardHat,
  Briefcase,
  Palette,
  Ruler,
  DollarSign,
  AlertCircle,
  QrCode
} from 'lucide-react';
import { useAuth, ROLES, ROLE_DETAILS } from '../context/AuthContext';
import { LOGO_URL } from '../components/common/BrandLogo';

import loginBrandImg from '../assets/login_brand.png';
import { validateFullName, sanitizeInput } from '../utils/sanitization';

export default function AuthSuite({ setActiveTab }) {
  const { login, signup, verify2FA } = useAuth();
  const fileInputRef = useRef(null);
  
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'signup' | '2fa_prompt'
  const [pending2FAEmail, setPending2FAEmail] = useState(null);
  const [otpCode, setOtpCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  
  // Form Fields
  const [name, setName] = useState('');
  const [nameError, setNameError] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState(ROLES.HOMEOWNER);
  const [country, setCountry] = useState('Pakistan');
  const [phone, setPhone] = useState('');
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [rememberMe, setRememberMe] = useState(true);

  
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Real-time Name Validation
  const handleNameChange = (e) => {
    const rawVal = e.target.value;
    setName(rawVal);
    
    if (rawVal.trim()) {
      const validation = validateFullName(rawVal);
      if (!validation.isValid) {
        setNameError(validation.error);
      } else {
        setNameError(null);
      }
    } else {
      setNameError(null);
    }
  };

  // Avatar Upload Handler
  const handleAvatarChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg('Profile photo must be less than 5MB.');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setAvatarPreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);

    try {
      if (authMode === 'signup') {
        // Strict Full Name Validation (Format & Vulgarity Filter)
        const nameValidation = validateFullName(name);
        if (!nameValidation.isValid) {
          setNameError(nameValidation.error);
          throw new Error(nameValidation.error);
        }

        if (!phone.trim()) throw new Error('Please enter your contact phone number.');
        if (password.length < 6) throw new Error('Password must be at least 6 characters.');
        
        // Registration with selected standard role (excluding SYSTEM_ADMIN)
        const signupRes = await signup(name, email, password, { phone, country, role: selectedRole, avatarUrl: avatarPreview });
        
        if (signupRes && signupRes.requiresEmailVerification) {
          setSuccessMsg(signupRes.message);
          setAuthMode('login'); // Switch to login view with success notification
        } else {
          setSuccessMsg('Account registered successfully! Opening your AI workspace...');
          setTimeout(() => {
            setActiveTab('workspace');
          }, 500);
        }
      } else if (authMode === '2fa_prompt') {
        if (!otpCode || otpCode.trim().length !== 6) {
          throw new Error('Please enter a valid 6-digit verification code.');
        }
        const targetEmail = pending2FAEmail || email;
        await verify2FA(targetEmail, otpCode);
        setSuccessMsg('Two-Factor Authentication verified successfully! Opening workspace...');
        setTimeout(() => {
          setActiveTab('workspace');
        }, 400);
      } else {
        const loginRes = await login(email, password);
        if (loginRes && loginRes.requires2FA) {
          setPending2FAEmail(loginRes.email || email);
          setAuthMode('2fa_prompt');
          setSuccessMsg('Password verified. Please enter your 6-digit Google Authenticator code.');
        } else {
          setSuccessMsg(`Welcome back, ${loginRes.name || 'User'}!`);
          setTimeout(() => {
            setActiveTab('workspace');
          }, 400);
        }
      }
    } catch (err) {
      setErrorMsg(err.message || 'Invalid email or password. Please sign up first.');
    } finally {
      setIsLoading(false);
    }
  };


  // Auto-fills registered test credentials into the input fields (does NOT bypass authentication!)
  const handleQuickPreset = (roleType) => {
    setErrorMsg(null);
    setNameError(null);
    setSuccessMsg('Auto-filled credentials. Click "Sign In to Workspace" to verify.');
    setAuthMode('login');
    if (roleType === ROLES.ARCHITECT) {
      setEmail('architect@archai.design');
      setPassword('architectSecure2026!');
      setName('Lead Architect');
    } else if (roleType === ROLES.SYSTEM_ADMIN) {
      setEmail('usamarajput2426@gmail.com');
      setPassword('Pakistan');
      setName('Usama Rajput');
    } else if (roleType === ROLES.DESIGNER) {
      setEmail('designer@archai.design');
      setPassword('designerPass2026!');
      setName('Spatial Designer');
    } else if (roleType === ROLES.CONSTRUCTION_PRO) {
      setEmail('engineer@archai.design');
      setPassword('engineerPass2026!');
      setName('Construction Engineer');
    } else if (roleType === ROLES.REAL_ESTATE_DEV) {
      setEmail('developer@archai.design');
      setPassword('developerPass2026!');
      setName('Real Estate Developer');
    } else {
      setEmail('client.homeowner@archai.pk');
      setPassword('homeownerPass2026!');
      setName('Homeowner Client');
      setPhone('+92 300 8521470');
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-50 text-slate-900 font-sans flex relative select-none overflow-x-hidden">
      
      {/* Top Floating Return Button */}
      <div className="absolute top-6 left-6 z-50">
        <button
          type="button"
          onClick={() => setActiveTab('landing')}
          className="flex items-center gap-2.5 px-4.5 py-2.5 bg-white/95 hover:bg-white backdrop-blur-md border border-slate-200 rounded-full text-xs font-bold text-slate-700 hover:text-slate-900 transition shadow-sm cursor-pointer hover:scale-[1.02]"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Landing</span>
        </button>
      </div>

      {/* Main Split-Screen Container */}
      <div className="w-full flex flex-col lg:flex-row min-h-screen">
        
        {/* LEFT PANEL: Sleek Dark Brand & 3D Artwork Showcase */}
        <div className="lg:w-1/2 w-full bg-slate-950 relative flex flex-col justify-between p-8 sm:p-12 lg:p-14 border-b lg:border-b-0 lg:border-r border-slate-800 overflow-hidden text-white">
          
          {/* Subtle Ambient Background Lighting */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(37,99,235,0.22),transparent_70%)] pointer-events-none"></div>
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:3.5rem_3.5rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-25 pointer-events-none"></div>

          {/* Top Brand Pill */}
          <div className="relative z-10 pt-14 lg:pt-0 flex items-center justify-between">
            <div className="inline-flex items-center gap-2.5 px-4 py-1.5 bg-slate-900/90 border border-blue-500/30 rounded-full text-xs font-mono font-bold text-blue-400 shadow-sm backdrop-blur-xs">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span>Generative Spatial Intelligence • ArchAI</span>
            </div>
          </div>

          {/* Center 3D Brand Artwork & Value Proposition */}
          <div className="relative z-10 my-auto py-6 flex flex-col items-center text-center">
            
            {/* User's 3D Metallic ArchAI Artwork Showcase */}
            <div className="relative group mb-6">
              <div className="absolute -inset-2 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-3xl blur-xl opacity-30 group-hover:opacity-50 transition duration-500"></div>
              <div className="relative w-64 h-64 sm:w-72 sm:h-72 lg:w-80 lg:h-80 rounded-3xl overflow-hidden border border-slate-700/80 bg-slate-900 shadow-2xl flex items-center justify-center p-2">
                <img 
                  src={loginBrandImg} 
                  alt="ArchAI 3D Metallic Brand Logo" 
                  className="w-full h-full object-contain rounded-2xl group-hover:scale-105 transition-transform duration-500"
                />
              </div>
            </div>

            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-white tracking-tight leading-tight mb-3 max-w-lg">
              Design Your Dream House <br />
              <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent">
                with Artificial Intelligence
              </span> in Minutes.
            </h1>

            <p className="text-xs sm:text-sm text-slate-300 max-w-md leading-relaxed mb-6">
              Synthesizing 5-Marla, 10-Marla &amp; 1-Kanal floor plans with instant 3D elevations, CAD exports, and localized PKR construction estimates.
            </p>

            {/* 3 Value Badges */}
            <div className="grid grid-cols-3 gap-2.5 w-full max-w-lg">
              <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800/90 text-center">
                <Ruler className="w-4 h-4 text-blue-400 mx-auto mb-1" />
                <span className="block text-xs font-bold text-white">2D &amp; 3D BIM</span>
                <span className="text-[10px] text-slate-400">Parametric CAD</span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800/90 text-center">
                <Building2 className="w-4 h-4 text-cyan-400 mx-auto mb-1" />
                <span className="block text-xs font-bold text-white">Bylaws Check</span>
                <span className="text-[10px] text-slate-400">CDA / RDA / LDA</span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800/90 text-center">
                <DollarSign className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
                <span className="block text-xs font-bold text-white">PKR Cost Model</span>
                <span className="text-[10px] text-slate-400">Material BOQ</span>
              </div>
            </div>
          </div>

          {/* Footer Academic Attribution */}
          <div className="relative z-10 pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400 text-center sm:text-left">
            <span>Department of Computer Science • CUST AI Lab</span>
            <span className="font-semibold text-slate-300">Supervised by Dr. Aamer Nadeem</span>
          </div>
        </div>

        {/* RIGHT PANEL: Crisp Clean White Authentication Form */}
        <div className="lg:w-1/2 w-full bg-slate-50 flex flex-col justify-center items-center p-8 sm:p-12 lg:p-16 overflow-y-auto">
          <div className="w-full max-w-xl my-auto bg-white border border-slate-200 rounded-3xl p-10 sm:p-12 md:p-14 shadow-xl">
            
            {authMode === '2fa_prompt' ? (
              <div className="space-y-7">
                <div className="text-center py-2">
                  <div className="w-16 h-16 bg-blue-50 border border-blue-200 rounded-2xl flex items-center justify-center mx-auto mb-4 text-blue-600 shadow-xs">
                    <ShieldCheck className="w-8 h-8" />
                  </div>
                  <h2 className="text-3xl font-black text-slate-900 tracking-tight">Two-Factor Authentication</h2>
                  <p className="text-sm font-medium text-slate-500 mt-2 max-w-sm mx-auto leading-relaxed">
                    Enter the 6-digit verification code from your <strong className="text-slate-800 font-bold">Google Authenticator</strong> app for <span className="font-mono font-bold text-blue-600">{pending2FAEmail || email}</span>.
                  </p>
                </div>

                {errorMsg && (
                  <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-base font-semibold flex items-center gap-3 animate-in fade-in">
                    <ShieldAlert className="w-6 h-6 shrink-0 text-rose-600" />
                    <span>{errorMsg}</span>
                  </div>
                )}

                {successMsg && (
                  <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-base font-medium flex items-center gap-3 animate-in fade-in">
                    <CheckCircle2 className="w-6 h-6 shrink-0 text-emerald-500" />
                    <span>{successMsg}</span>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label className="block text-sm font-bold text-slate-800 uppercase tracking-wider mb-3 text-center">
                      6-Digit Security Code *
                    </label>
                    <div className="relative max-w-sm mx-auto">
                      <Lock className="w-6 h-6 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type="text"
                        inputMode="numeric"
                        maxLength={6}
                        required
                        autoFocus
                        placeholder="123456"
                        value={otpCode}
                        onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        className="w-full pl-14 pr-4 py-5 bg-slate-50 border-2 border-slate-200 focus:border-blue-600 focus:bg-white rounded-2xl text-center text-3xl font-mono font-black text-slate-900 tracking-[0.35em] placeholder:tracking-normal placeholder:text-slate-300 focus:outline-none transition-all shadow-xs"
                      />
                    </div>
                    <p className="text-xs text-slate-500 text-center mt-3 font-semibold">
                      Enter the 6-digit code generated by your Google Authenticator app.
                    </p>
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading || otpCode.length !== 6}
                    className="w-full py-4.5 px-8 bg-blue-600 hover:bg-blue-700 text-white font-bold text-base rounded-2xl transition-all shadow-xl shadow-blue-500/25 flex items-center justify-center gap-3 cursor-pointer disabled:opacity-60 hover:scale-[1.01]"
                  >
                    {isLoading ? (
                      <span>Verifying Security Token...</span>
                    ) : (
                      <>
                        <ShieldCheck className="w-6 h-6" />
                        <span>Verify &amp; Sign In</span>
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode('login');
                      setPending2FAEmail(null);
                      setOtpCode('');
                      setErrorMsg(null);
                      setSuccessMsg(null);
                    }}
                    className="w-full py-3 text-sm font-bold text-slate-500 hover:text-slate-800 transition cursor-pointer text-center"
                  >
                    ← Cancel and Return to Sign In
                  </button>
                </form>
              </div>
            ) : (
              <>
                {/* Header Tabs Toggle: Sign In vs Register */}
                <div className="bg-slate-100 p-2 rounded-2xl border border-slate-200/80 mb-8 flex">
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode('login');
                      setErrorMsg(null);
                      setNameError(null);
                      setSuccessMsg(null);
                    }}

                    className={`flex-1 py-3 rounded-xl text-sm font-bold transition cursor-pointer flex items-center justify-center gap-2 ${
                      authMode === 'login'
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <KeyRound className="w-4 h-4 text-blue-600" />
                    <span>Sign In</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode('signup');
                      setErrorMsg(null);
                      setNameError(null);
                      setSuccessMsg(null);
                    }}
                    className={`flex-1 py-3 rounded-xl text-sm font-bold transition cursor-pointer flex items-center justify-center gap-2 ${
                      authMode === 'signup'
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <UserPlus className="w-4 h-4 text-blue-600" />
                    <span>Register Account</span>
                  </button>
                </div>

                {/* Form Title & Subtitle */}
                <div className="mb-6">
                  <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                    {authMode === 'login' ? 'Sign in to ArchAI Studio' : 'Create Your Homeowner Account'}
                  </h2>
                  <p className="text-sm text-slate-600 mt-1.5 leading-relaxed">
                    {authMode === 'login'
                      ? 'Access your saved blueprints, 3D WebGL models, and cost estimates.'
                      : 'Start designing your customized residential layout and exploring 3D elevations.'}
                  </p>
                </div>


            {/* Error Feedback Banner (High-Impact Red) */}
            {errorMsg && (
              <div className="mb-5 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-semibold flex items-center gap-3 animate-in fade-in">
                <ShieldAlert className="w-5 h-5 shrink-0 text-rose-600" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Success Feedback Banner */}
            {successMsg && (
              <div className="mb-5 p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-medium flex items-center gap-3 animate-in fade-in">
                <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-500" />
                <span>{successMsg}</span>
              </div>
            )}

            {/* Main Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              
              {/* Registration Extra Fields */}
              {authMode === 'signup' && (
                <>
                  {/* Photo Upload Box with Live Preview */}
                  <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex items-center gap-4">
                    <div className="relative shrink-0">
                      {avatarPreview ? (
                        <img
                          src={avatarPreview}
                          alt="Avatar Preview"
                          className="w-14 h-14 rounded-2xl object-cover ring-2 ring-blue-500/50 shadow-xs"
                        />
                      ) : (
                        <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200 flex items-center justify-center text-slate-400 shadow-2xs">
                          <Camera className="w-6 h-6" />
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <span className="block text-sm font-bold text-slate-900">Profile Photo</span>
                      <p className="text-xs text-slate-500 truncate mt-0.5">PNG or JPG under 5MB</p>
                    </div>

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarChange}
                      className="hidden"
                    />

                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-2xs cursor-pointer"
                    >
                      <Upload className="w-3.5 h-3.5 text-blue-600" />
                      <span>{avatarPreview ? 'Change' : 'Upload'}</span>
                    </button>
                  </div>

                  {/* Full Name Input with Real-time Vulgarity & Format Validation */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Full Legal Name *
                    </label>
                    <div className="relative">
                      <User className={`w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none ${nameError ? 'text-rose-500' : 'text-slate-400'}`} />
                      <input
                        type="text"
                        required
                        placeholder="e.g. Tariq Mehmood"
                        value={name}
                        onChange={handleNameChange}
                        className={`w-full pl-12 pr-4 py-3.5 border rounded-2xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none transition-all shadow-2xs ${
                          nameError
                            ? 'border-rose-400 bg-rose-50/20 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/10'
                            : 'bg-slate-50 border-slate-200 focus:border-blue-600 focus:bg-white'
                        }`}
                      />
                    </div>
                    {nameError && (
                      <p className="text-xs font-semibold text-rose-600 mt-2 flex items-center gap-1.5 animate-in fade-in">
                        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                        <span>{nameError}</span>
                      </p>
                    )}
                    <span className="text-[11px] text-slate-400 mt-1 block">
                      Letters, spaces, hyphens, and apostrophes only (2–50 characters).
                    </span>
                  </div>

                  {/* Account Role Selection (Excludes System Admin) */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                      Account Type / Professional Role *
                    </label>
                    <div className="relative">
                      <Briefcase className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <select
                        value={selectedRole}
                        onChange={(e) => setSelectedRole(e.target.value)}
                        className="w-full pl-12 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-semibold text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white cursor-pointer shadow-2xs"
                      >
                        <option value={ROLES.HOMEOWNER}>Homeowner / Customer Client</option>
                        <option value={ROLES.ARCHITECT}>Lead Architect</option>
                        <option value={ROLES.DESIGNER}>Spatial Designer</option>
                        <option value={ROLES.CONSTRUCTION_PRO}>Construction Professional</option>
                        <option value={ROLES.REAL_ESTATE_DEV}>Real Estate Developer</option>
                      </select>
                    </div>
                    <span className="text-[11px] text-slate-400 mt-1 block">
                      Select your platform role (System Admin accounts cannot be created publicly).
                    </span>
                  </div>


                  {/* Country & Phone Number Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                        Country *
                      </label>
                      <div className="relative">
                        <Globe className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                        <select
                          value={country}
                          onChange={(e) => setCountry(e.target.value)}
                          className="w-full pl-12 pr-3 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-sm text-slate-900 focus:outline-none focus:border-blue-600 focus:bg-white cursor-pointer shadow-2xs"
                        >
                          <option value="Pakistan">Pakistan</option>
                          <option value="United Arab Emirates">UAE</option>
                          <option value="United Kingdom">United Kingdom</option>
                          <option value="United States">United States</option>
                          <option value="Saudi Arabia">Saudi Arabia</option>
                          <option value="Canada">Canada</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                        Phone Number *
                      </label>
                      <div className="relative">
                        <Phone className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                        <input
                          type="tel"
                          required
                          placeholder="+92 300 1234567"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          className="w-full pl-12 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white transition-all shadow-2xs"
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Email Address Input */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Email Address *
                </label>
                <div className="relative">
                  <Mail className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="email"
                    required
                    placeholder="user@archai.design"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-12 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white transition-all shadow-2xs"
                  />
                </div>
              </div>

              {/* Password Input */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Password *
                  </label>
                  {authMode === 'login' && (
                    <span className="text-xs text-blue-600 hover:text-blue-700 font-bold cursor-pointer hover:underline">
                      Forgot Password?
                    </span>
                  )}
                </div>
                <div className="relative">
                  <Lock className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-12 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-600 focus:bg-white transition-all shadow-2xs"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer p-1"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Remember Me Checkbox */}
              {authMode === 'login' && (
                <div className="flex items-center justify-between pt-1">
                  <label className="flex items-center gap-2.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 text-blue-600 accent-blue-600 cursor-pointer"
                    />
                    <span className="text-sm text-slate-600 font-medium">Keep me signed in</span>
                  </label>
                </div>
              )}

              {/* Primary Action Button */}
              <button
                type="submit"
                disabled={isLoading || (authMode === 'signup' && !!nameError)}
                className="w-full mt-3 py-4 px-6 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm sm:text-base rounded-2xl transition-all shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2.5 cursor-pointer disabled:opacity-60 hover:scale-[1.01]"
              >
                {isLoading ? (
                  <span>Verifying &amp; Registering Account...</span>
                ) : (
                  <>
                    <span>{authMode === 'login' ? 'Sign In to Workspace' : 'Complete Account Registration'}</span>
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>

            {/* Auto-fill Registered Credentials Section */}
            <div className="mt-8 pt-6 border-t border-slate-100">
              <span className="block text-xs font-mono font-bold uppercase text-slate-500 text-center mb-1">
                Auto-fill Registered Test Credentials
              </span>
              <p className="text-[11px] text-slate-400 text-center mb-3">
                Click a role to load registered PostgreSQL credentials into the fields above:
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                <button
                  type="button"
                  onClick={() => handleQuickPreset(ROLES.HOMEOWNER)}
                  className="p-2.5 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-xl text-xs font-bold text-emerald-800 transition cursor-pointer text-center shadow-2xs"
                >
                  🏠 Homeowner
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickPreset(ROLES.ARCHITECT)}
                  className="p-2.5 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-xl text-xs font-bold text-blue-800 transition cursor-pointer text-center shadow-2xs"
                >
                  📐 Lead Architect
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickPreset(ROLES.DESIGNER)}
                  className="p-2.5 bg-cyan-50 hover:bg-cyan-100 border border-cyan-200 rounded-xl text-xs font-bold text-cyan-800 transition cursor-pointer text-center shadow-2xs"
                >
                  🎨 Designer
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickPreset(ROLES.CONSTRUCTION_PRO)}
                  className="p-2.5 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-xl text-xs font-bold text-amber-800 transition cursor-pointer text-center shadow-2xs"
                >
                  🏗️ Construction Pro
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickPreset(ROLES.REAL_ESTATE_DEV)}
                  className="p-2.5 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-xl text-xs font-bold text-indigo-800 transition cursor-pointer text-center shadow-2xs"
                >
                  🏢 Real Estate Dev
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickPreset(ROLES.SYSTEM_ADMIN)}
                  className="p-2.5 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-xl text-xs font-bold text-purple-800 transition cursor-pointer text-center shadow-2xs"
                >
                  ⚡ System Admin
                </button>


              </div>
            </div>

            {/* Mode Switch Footnote */}
            <div className="mt-6 text-center text-sm text-slate-600">
              {authMode === 'login' ? "Don't have an account yet?" : 'Already registered?'}
              <button
                type="button"
                onClick={() => {
                  setAuthMode(authMode === 'login' ? 'signup' : 'login');
                  setErrorMsg(null);
                  setNameError(null);
                  setSuccessMsg(null);
                }}
                className="ml-2 font-bold text-blue-600 hover:text-blue-700 cursor-pointer hover:underline"
              >
                {authMode === 'login' ? 'Register here' : 'Sign in here'}
              </button>
            </div>
          </>
        )}


          </div>
        </div>

      </div>
    </div>
  );
}
