import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProjectProvider } from './context/ProjectContext';
import { PublicLayout } from './components/layout/PublicLayout';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { RoleGuard } from './components/auth/RoleGuard';

// Public Pages
import { LandingPage } from './pages/public/LandingPage';
import { TemplatesPage } from './pages/public/TemplatesPage';
import { CostEstimationPreviewPage } from './pages/public/CostEstimationPreviewPage';
import { AboutPage } from './pages/public/AboutPage';
import { HelpPage } from './pages/public/HelpPage';

// Auth Pages
import { LoginPage } from './pages/auth/LoginPage';
import { SignUpPage } from './pages/auth/SignUpPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { AccessDeniedPage } from './pages/auth/AccessDeniedPage';
import { NotFoundPage } from './pages/auth/NotFoundPage';

// Authenticated Core Pages
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { NewDesignPage } from './pages/designs/NewDesignPage';
import { SavedDesignsPage } from './pages/designs/SavedDesignsPage';
import { DesignDetailsPage } from './pages/designs/DesignDetailsPage';
import { CompareDesignsPage } from './pages/designs/CompareDesignsPage';
import { CostEstimationPage } from './pages/cost/CostEstimationPage';
import { FavoritesPage } from './pages/favorites/FavoritesPage';
import { NotificationsPage } from './pages/notifications/NotificationsPage';
import { ProfileSettingsPage } from './pages/profile/ProfileSettingsPage';
import { HelpSupportPage } from './pages/help/HelpSupportPage';

// Architect Pages
import { ArchitectProjectsPage } from './pages/architect/ArchitectProjectsPage';
import { ArchitectReviewsPage } from './pages/architect/ArchitectReviewsPage';
import { ArchitectRevisionsPage } from './pages/architect/ArchitectRevisionsPage';
import { ArchitectReportsPage } from './pages/architect/ArchitectReportsPage';

// Admin Pages
import { UserManagementPage } from './pages/admin/UserManagementPage';
import { RolesManagementPage } from './pages/admin/RolesManagementPage';
import { AdminProjectsPage } from './pages/admin/AdminProjectsPage';
import { TemplateManagementPage } from './pages/admin/TemplateManagementPage';
import { CostSettingsPage } from './pages/admin/CostSettingsPage';
import { AdminReportsPage } from './pages/admin/AdminReportsPage';
import { AuditLogsPage } from './pages/admin/AuditLogsPage';
import { SystemSettingsPage } from './pages/admin/SystemSettingsPage';

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ProjectProvider>
          <Routes>
            {/* Public Layout Routes */}
            <Route element={<PublicLayout />}>
              <Route path="/" element={<LandingPage />} />
              <Route path="/templates" element={<TemplatesPage />} />
              <Route path="/cost-estimation-preview" element={<CostEstimationPreviewPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/help" element={<HelpPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignUpPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
            </Route>

            {/* Authenticated Dashboard Layout Routes */}
            <Route path="/app" element={<DashboardLayout />}>
              {/* Common Authenticated Routes */}
              <Route index element={<Navigate to="/app/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="designs/new" element={<NewDesignPage />} />
              <Route path="designs" element={<SavedDesignsPage />} />
              <Route path="designs/:designId" element={<DesignDetailsPage />} />
              <Route path="templates" element={<TemplatesPage />} />
              <Route path="favorites" element={<FavoritesPage />} />
              <Route path="compare" element={<CompareDesignsPage />} />
              <Route path="cost-estimation" element={<CostEstimationPage />} />
              <Route path="notifications" element={<NotificationsPage />} />
              <Route path="profile" element={<ProfileSettingsPage />} />
              <Route path="settings" element={<ProfileSettingsPage />} />
              <Route path="help-support" element={<HelpSupportPage />} />
              <Route path="access-denied" element={<AccessDeniedPage />} />

              {/* Architect-Protected Routes */}
              <Route
                path="architect/projects"
                element={
                  <RoleGuard allowedRoles={['architect', 'admin']}>
                    <ArchitectProjectsPage />
                  </RoleGuard>
                }
              />
              <Route
                path="architect/reviews"
                element={
                  <RoleGuard allowedRoles={['architect', 'admin']}>
                    <ArchitectReviewsPage />
                  </RoleGuard>
                }
              />
              <Route
                path="architect/revisions"
                element={
                  <RoleGuard allowedRoles={['architect', 'admin']}>
                    <ArchitectRevisionsPage />
                  </RoleGuard>
                }
              />
              <Route
                path="architect/reports"
                element={
                  <RoleGuard allowedRoles={['architect', 'admin']}>
                    <ArchitectReportsPage />
                  </RoleGuard>
                }
              />

              {/* Administrator-Protected Routes */}
              <Route
                path="admin"
                element={
                  <RoleGuard allowedRoles={['admin']}>
                    <DashboardPage />
                  </RoleGuard>
                }
              />
              <Route
                path="admin/users"
                element={
                  <RoleGuard allowedRoles={['admin']}>
                    <UserManagementPage />
                  </RoleGuard>
                }
              />
              <Route
                path="admin/roles"
                element={
                  <RoleGuard allowedRoles={['admin']}>
                    <RolesManagementPage />
                  </RoleGuard>
                }
              />
              <Route
                path="admin/projects"
                element={
                  <RoleGuard allowedRoles={['admin']}>
                    <AdminProjectsPage />
                  </RoleGuard>
                }
              />
              <Route
                path="admin/templates"
                element={
                  <RoleGuard allowedRoles={['admin']}>
                    <TemplateManagementPage />
                  </RoleGuard>
                }
              />
              <Route
                path="admin/cost-settings"
                element={
                  <RoleGuard allowedRoles={['admin', 'contractor']}>
                    <CostSettingsPage />
                  </RoleGuard>
                }
              />
              <Route
                path="admin/reports"
                element={
                  <RoleGuard allowedRoles={['admin']}>
                    <AdminReportsPage />
                  </RoleGuard>
                }
              />
              <Route
                path="admin/audit-logs"
                element={
                  <RoleGuard allowedRoles={['admin']}>
                    <AuditLogsPage />
                  </RoleGuard>
                }
              />
              <Route
                path="admin/settings"
                element={
                  <RoleGuard allowedRoles={['admin']}>
                    <SystemSettingsPage />
                  </RoleGuard>
                }
              />
            </Route>

            {/* 404 Catch-All */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </ProjectProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
