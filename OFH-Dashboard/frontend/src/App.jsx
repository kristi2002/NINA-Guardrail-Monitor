import { useState, useEffect, lazy, Suspense } from 'react'
// --- IMPROVEMENT ---
// Import NavLink instead of Link and remove useLocation
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { NotificationProvider, useNotifications } from './contexts/NotificationContext'
import ProtectedRoute from './components/ProtectedRoute'
import { UserInfo } from './components/UserProfile'
import UserProfile from './components/UserProfile'
import NotificationPreferences from './components/NotificationPreferences'
import NotificationCenter from './components/NotificationCenter'
import ErrorBoundary from './components/ErrorBoundary'
import Login from './pages/Login'
import './App.css'

// Lazy load page components for code splitting and better performance
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Security = lazy(() => import('./pages/Security'))

function Navbar() {
  // const location = useLocation() // --- IMPROVEMENT ---: No longer needed
  const { isAuthenticated, user } = useAuth()
  
  // --- IMPROVEMENT ---
  // Use a single state to manage which modal is open.
  // This prevents multiple modals from being open at once.
  const [openModal, setOpenModal] = useState(null) // null, 'profile', 'preferences', 'center'

  const notificationData = useNotifications()
  const unreadCount = notificationData?.unreadCount || 0
  
  if (!isAuthenticated) return null
  
  return (
    <nav className="navbar">
      <div className="navbar-content">
        <div className="navbar-brand">
          <div className="brand-icon">
            <img src="/favicon.svg" alt="NINA Logo" className="logo-icon" />
          </div>
          <div className="brand-text">
            <h1>NINA Guardrail Monitor</h1>
            <p className="subtitle">Real-Time Safety Monitoring Dashboard</p>
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
                Dashboard
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/analytics" 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">📈</span>
                Analytics
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/security" 
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">🔒</span>
                Security
              </NavLink>
            </li>
          </ul>
        </div>

        <div className="navbar-user">
          <div className="navbar-controls">
            <button 
              className="btn-notifications-nav"
              // --- IMPROVEMENT ---: Set modal state by name
              onClick={() => setOpenModal('center')}
              title="Notifications"
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
              title="Notification Preferences"
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
  
  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Initializing NINA Security Dashboard...</p>
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
                      <p>Loading Dashboard...</p>
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
                      <p>Loading Analytics...</p>
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
                      <p>Loading Security...</p>
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