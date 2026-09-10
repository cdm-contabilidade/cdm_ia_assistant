import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi, getApiError, setAccessToken } from '../services/api'
import type { AuthStatus, TokenResponse, User } from '../types'

type AuthContextValue = {
  user: User | null
  status: AuthStatus
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}
const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    authApi.refresh().then(async (token) => {
      if (!token) { setStatus('guest'); return }
      try { setUser(await authApi.me()); setStatus('authenticated') }
      catch { setAccessToken(null); setStatus('guest') }
    }).catch(() => setStatus('guest'))
  }, [])

  async function authenticate(action: () => Promise<TokenResponse>) {
    setError(null)
    try { const result = await action(); setAccessToken(result.access_token); setUser(result.user); setStatus('authenticated') }
    catch (cause) { setError(getApiError(cause)); throw cause }
  }
  const value = useMemo<AuthContextValue>(() => ({
    user, status, error,
    login: (email, password) => authenticate(() => authApi.login({ email, password })),
    logout: async () => { try { await authApi.logout() } finally { setAccessToken(null); setUser(null); setStatus('guest') } },
  }), [user, status, error])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
