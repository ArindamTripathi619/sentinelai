import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './auth/Login'
import Register from './auth/Register'
import Dashboard from './dashboard/Dashboard'
import UserTimeline from './dashboard/UserTimeline'
import { getAuthToken } from './lib/api'
import { useNavigate, useParams } from 'react-router-dom'

function ProtectedRoute({ children }) {
  return getAuthToken() ? children : <Navigate to="/login" replace />
}

function UserTimelineRoute() {
  const navigate = useNavigate()
  const { userId } = useParams()

  return (
    <ProtectedRoute>
      <UserTimeline
        mode="page"
        userId={userId}
        onClose={() => navigate('/dashboard', { replace: true })}
      />
    </ProtectedRoute>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
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
