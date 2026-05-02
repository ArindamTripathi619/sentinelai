import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  // Failing fast here makes misconfiguration obvious in dev and preview builds.
  console.warn('Supabase environment variables are not configured.')
}

export const supabase = createClient(supabaseUrl || '', supabaseAnonKey || '')

export async function getAccessToken() {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token || null
}

export async function getSession() {
  const { data } = await supabase.auth.getSession()
  return data.session || null
}

export async function getCurrentUser() {
  const { data } = await supabase.auth.getUser()
  return data.user || null
}

export async function signOut() {
  return supabase.auth.signOut()
}