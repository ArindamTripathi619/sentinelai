import { useNavigate } from 'react-router-dom'
import { clearUserSession } from '../lib/api'

export default function EventsPage() {
  const navigate = useNavigate()

  function handleLogout() {
    clearUserSession()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center text-gray-400">
      <p className="mb-8 text-lg">Event Platform — under construction</p>
      <button
        onClick={handleLogout}
        className="px-6 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors border border-gray-700"
      >
        Logout
      </button>
    </div>
  )
}
