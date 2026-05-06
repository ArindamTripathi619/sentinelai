import axios from 'axios'
import { supabase } from './supabase'

const isVercelHost = typeof window !== 'undefined' && window.location.hostname.endsWith('.vercel.app')
const renderApiBase = 'https://sentinelai-e1zs.onrender.com/api'
const baseURL = import.meta.env.VITE_API_BASE_URL || (isVercelHost ? renderApiBase : '/api')

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
