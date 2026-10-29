import React, { useState } from 'react';
import Navbar from './components/common/Navbar';
import Footer from './components/common/Footer';
import StudioModal from './components/common/StudioModal';
import ProtectedRoute from './components/common/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import WorkspacePage from './pages/WorkspacePage';
import CostEstimatorPage from './pages/CostEstimatorPage';
import AuthPage from './pages/AuthPage';
import ProfileSettingsPage from './pages/ProfileSettingsPage';
import { AuthProvider, useAuth } from './context/AuthContext';

function MainAppContent() {
  const { user, isAuthenticated } = useAuth();
  
  // If user has an active session, default to 'workspace' (Dashboard), otherwise 'landing'
  const [activeTab, setActiveTab] = useState(() => {
    try {
      const savedUser = localStorage.getItem('archai_user');
      const savedToken = localStorage.getItem('archai_token') || localStorage.getItem('jwt_token');
      if (savedUser && savedToken) {
        return 'workspace'; // Logged-in users start directly on their Dashboard
      }
    } catch (e) {}
    return 'landing';
  });

  const [workspaceNav, setWorkspaceNav] = useState('dashboard');
  const [studioOpen, setStudioOpen] = useState(false);
  const [initialStudioModel, setInitialStudioModel] = useState('5marla');

  // Ensure scroll is reset to top whenever tab changes
  React.useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [activeTab]);

  const handleOpenStudio = (model = '5marla') => {
    setInitialStudioModel(model);
    setStudioOpen(true);
  };

  // Safe tab navigation guard
  const handleTabChange = (newTab, subNav = 'dashboard') => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    if ((newTab === 'workspace' || newTab === 'profile-settings') && !isAuthenticated) {
      setActiveTab('auth');
      return;
    }
    if (newTab === 'workspace' && subNav) {
      setWorkspaceNav(subNav);
    }
    setActiveTab(newTab);
  };

  const isFullAppView = (activeTab === 'workspace' && isAuthenticated) || activeTab === 'auth' || (activeTab === 'profile-settings' && isAuthenticated);

  return (
    <div className="min-h-screen flex flex-col justify-between bg-slate-50 text-slate-900 font-sans select-none">
      
      {/* Top Navbar */}
      {!isFullAppView && (
        <Navbar 
          activeTab={activeTab} 
          setActiveTab={handleTabChange} 
          onOpenStudio={() => handleOpenStudio('5marla')} 
        />
      )}

      {/* Main View Router */}
      <main className="flex-1">
        {activeTab === 'landing' && (
          <LandingPage 
            setActiveTab={handleTabChange} 
            onOpenStudio={() => handleOpenStudio('5marla')} 
          />
        )}

        {activeTab === 'auth' && (
          <AuthPage 
            setActiveTab={setActiveTab} 
          />
        )}

        {activeTab === 'workspace' && (
          <ProtectedRoute onNavigateToAuth={() => setActiveTab('auth')}>
            <WorkspacePage 
              setActiveTab={handleTabChange} 
              onOpenStudio={() => handleOpenStudio('5marla')} 
              initialNav={workspaceNav}
            />
          </ProtectedRoute>
        )}

        {activeTab === 'profile-settings' && (
          <ProtectedRoute onNavigateToAuth={() => setActiveTab('auth')}>
            <ProfileSettingsPage setActiveTab={handleTabChange} />
          </ProtectedRoute>
        )}

        {activeTab === 'cost-estimator' && (
          <CostEstimatorPage 
            setActiveTab={handleTabChange}
            onOpenStudio={() => handleOpenStudio('5marla')} 
          />
        )}
      </main>


      {/* Interactive 3D Studio Modal */}
      <StudioModal 
        isOpen={studioOpen} 
        onClose={() => setStudioOpen(false)} 
        initialModel={initialStudioModel} 
      />

      {/* Architectural Footer */}
      {!isFullAppView && (
        <Footer setActiveTab={handleTabChange} />
      )}
    </div>
  );
}

import { ThemeProvider } from './context/ThemeContext';

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <MainAppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}
