import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './auth/Login'
import Register from './auth/Register'
import Dashboard from './dashboard/Dashboard'
import UserTimeline from './dashboard/UserTimeline'
import { supabase } from './lib/supabase'
import { useNavigate, useParams } from 'react-router-dom'

function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true)
  const [session, setSession] = useState(null)

  useEffect(() => {
    let mounted = true

    const loadSession = async () => {
      const { data } = await supabase.auth.getSession()
      if (!mounted) {
        return
      }
      setSession(data.session || null)
      setLoading(false)
    }

    loadSession()

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
      setLoading(false)
    })

    return () => {
      mounted = false
      subscription.subscription.unsubscribe()
    }
  }, [])

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">Loading...</div>
  }

  return session ? children : <Navigate to="/login" replace />
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
