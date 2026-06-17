import { BrowserRouter, Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Login from './auth/Login'
import Register from './auth/Register'
import ForgotPassword from './auth/ForgotPassword'
import ResetPassword from './auth/ResetPassword'
import EventsPage from './auth/Events'
import Dashboard from './dashboard/Dashboard'
import UserTimeline from './dashboard/UserTimeline'
import AdminGuard from './dashboard/AdminGuard'
import { getAuthToken, isAdmin } from './lib/api'

function ProtectedRoute({ children }) {
  const [hasToken, setHasToken] = useState(getAuthToken())

  useEffect(() => {
    setHasToken(getAuthToken())
    const handler = () => setHasToken(getAuthToken())
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [])

  return hasToken ? children : <Navigate to="/login" replace />
}

function UserTimelineRoute() {
  const navigate = useNavigate()
  const { userId } = useParams()

  return (
    <ProtectedRoute>
      <AdminGuard>
        <UserTimeline
          mode="page"
          userId={userId}
          onClose={() => navigate('/dashboard', { replace: true })}
        />
      </AdminGuard>
    </ProtectedRoute>
  )
}

function RootRedirect() {
  if (!getAuthToken()) return <Navigate to="/login" replace />
  return isAdmin() ? <Navigate to="/dashboard" replace /> : <Navigate to="/events" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route
          path="/events"
          element={
            <ProtectedRoute>
              <EventsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <AdminGuard>
                <Dashboard />
              </AdminGuard>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/users/:userId/timeline"
          element={<UserTimelineRoute />}
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
