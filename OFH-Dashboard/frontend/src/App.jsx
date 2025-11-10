import { useState, useEffect, lazy, Suspense } from 'react'
// --- IMPROVEMENT ---
// Import NavLink instead of Link and remove useLocation
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { NotificationProvider, useNotifications } from './contexts/NotificationContext'
import { ProtectedRoute, UserProfile, UserInfo, ErrorBoundary } from './components/common'
import { NotificationPreferences, NotificationCenter } from './components/notifications'
import Login from './pages/Login'
import './App.css'
import { useTranslation } from 'react-i18next'

// Lazy load page components for code splitting and better performance
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Security = lazy(() => import('./pages/Security'))

function Navbar() {
  // const location = useLocation() // --- IMPROVEMENT ---: No longer needed
  const { isAuthenticated, user } = useAuth()
  const { t, i18n } = useTranslation()
  
  // --- IMPROVEMENT ---
  // Use a single state to manage which modal is open.
  // This prevents multiple modals from being open at once.
  const [openModal, setOpenModal] = useState(null) // null, 'profile', 'preferences', 'center'

  const notificationData = useNotifications()
  const unreadCount = notificationData?.unreadCount || 0
  
  if (!isAuthenticated) return null
  
  const changeLanguage = (language) => {
    if (i18n.resolvedLanguage !== language) {
      i18n.changeLanguage(language)
    }
  }

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <div className="navbar-brand">
          <div className="brand-icon">
            <img src="/favicon.svg" alt="NINA Logo" className="logo-icon" />
          </div>
          <div className="brand-text">
            <h1>{t('app.title')}</h1>
            <p className="subtitle">{t('app.subtitle')}</p>
          </div>
        </div>
        
        <div className="navbar-center">
          <ul className="nav-links">
            <li>
              {/* --- IMPROVEMENT ---
                - Use NavLink instead of Link
                - Use the `className` function prop to get `isActive`
                - Removed redundant onClick
              */}
              <NavLink 
                to="/" 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">📊</span>
                {t('nav.dashboard')}
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/analytics" 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">📈</span>
                {t('nav.analytics')}
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/security" 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">🔒</span>
                {t('nav.security')}
              </NavLink>
            </li>
          </ul>
        </div>

        <div className="navbar-user">
          <div className="navbar-controls">
            <div
              className="language-switcher"
              style={{ '--language-active-index': i18n.resolvedLanguage === 'it' ? 1 : 0 }}
            >
              <button
                type="button"
                className={`language-button ${i18n.resolvedLanguage === 'en' ? 'active' : ''}`}
                onClick={() => changeLanguage('en')}
                aria-label={t('language.switchToEnglish')}
                aria-pressed={i18n.resolvedLanguage === 'en'}
              >
                EN
              </button>
              <button
                type="button"
                className={`language-button ${i18n.resolvedLanguage === 'it' ? 'active' : ''}`}
                onClick={() => changeLanguage('it')}
                aria-label={t('language.switchToItalian')}
                aria-pressed={i18n.resolvedLanguage === 'it'}
              >
                IT
              </button>
            </div>
            <button 
              className="btn-notifications-nav"
              // --- IMPROVEMENT ---: Set modal state by name
              onClick={() => setOpenModal('center')}
              title={t('navbar.notifications')}
            >
              <span className="notification-icon">🔔</span>
              {unreadCount > 0 && (
                <span className="notification-badge">{unreadCount}</span>
              )}
            </button>
            
            <button 
              className="btn-notification-preferences"
              // --- IMPROVEMENT ---: Set modal state by name
              onClick={() => setOpenModal('preferences')}
              title={t('navbar.preferences')}
            >
              <span className="preferences-icon">⚙️</span>
            </button>
            
          </div>
          <div className="user-section">
            {/* --- IMPROVEMENT ---: Toggle logic for profile modal */}
            <UserInfo onClick={() => setOpenModal(openModal === 'profile' ? null : 'profile')} />
            <UserProfile 
              // --- IMPROVEMENT ---: Pass boolean based on state
              isDropdownOpen={openModal === 'profile'}
              onClose={() => setOpenModal(null)}
            />
          </div>
        </div>
      </div>
      
      {/* --- IMPROVEMENT ---: Render modal based on state name */}
      {openModal === 'preferences' && (
        <NotificationPreferences 
          isOpen={true} // It's only rendered when open
          onClose={() => setOpenModal(null)}
          user={user}
        />
      )}
      
      {/* --- IMPROVEMENT ---: Render modal based on state name */}
      {openModal === 'center' && (
        <NotificationCenter 
          isOpen={true} // It's only rendered when open
          onClose={() => setOpenModal(null)}
        />
      )}
    </nav>
  )
}

// ... No changes to AppContent or App ...

function AppContent() {
  const { isAuthenticated, loading } = useAuth()
  const { t } = useTranslation()
  
  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>{t('app.loading')}</p>
      </div>
    )
  }
  
  return (
    <ErrorBoundary>
      <div className="app">
        <Navbar />
        
        <main className="main-content">
          <Routes>
            {/* Public route */}
            <Route path="/login" element={<Login />} />
            
            {/* Protected routes with lazy loading */}
            <Route path="/" element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <Suspense fallback={
                    <div className="app-loading">
                      <div className="loading-spinner"></div>
                      <p>{t('app.loadingDashboard')}</p>
                    </div>
                  }>
                    <Dashboard />
                  </Suspense>
                </ErrorBoundary>
              </ProtectedRoute>
            } />
            
            <Route path="/analytics" element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <Suspense fallback={
                    <div className="app-loading">
                      <div className="loading-spinner"></div>
                      <p>{t('app.loadingAnalytics')}</p>
                    </div>
                  }>
                    <Analytics />
                  </Suspense>
                </ErrorBoundary>
              </ProtectedRoute>
            } />
            
            <Route path="/security" element={
              <ProtectedRoute requiredPermission="view_security">
                <ErrorBoundary>
                  <Suspense fallback={
                    <div className="app-loading">
                      <div className="loading-spinner"></div>
                      <p>{t('app.loadingSecurity')}</p>
                    </div>
                  }>
                    <Security />
                  </Suspense>
                </ErrorBoundary>
              </ProtectedRoute>
            } />
            
            {/* Catch-all redirect */}
            <Route path="*" element={
              isAuthenticated ? <Navigate to="/" replace /> : <Navigate to="/login" replace />
            } />
          </Routes>
        </main>
      </div>
    </ErrorBoundary>
  )
}


function App() {
  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <AuthProvider>
        <NotificationProvider>
          <AppContent />
        </NotificationProvider>
      </AuthProvider>
    </Router>
  )
}

export default App