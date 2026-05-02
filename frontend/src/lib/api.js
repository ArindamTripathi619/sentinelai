import axios from 'axios'
import { supabase } from './supabase'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

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
