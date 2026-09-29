import { useEffect, useRef, useState, type FormEvent } from 'react'
import logoColor from '../../logo/logo_color.png'
import { authApi, getApiError } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

type LoginPageProps = { redirectTarget: string }

export function LoginPage({ redirectTarget }: LoginPageProps) {
  const { login, error } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [forgotMode, setForgotMode] = useState(false)
  const [recoveryEmail, setRecoveryEmail] = useState('')
  const [recoveryBusy, setRecoveryBusy] = useState(false)
  const [recoveryMessage, setRecoveryMessage] = useState<string | null>(null)
  const [recoveryError, setRecoveryError] = useState<string | null>(null)
  const firstRef = useRef<HTMLInputElement>(null)

  useEffect(() => { firstRef.current?.focus() }, [forgotMode])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    try { await login(email, password); window.history.replaceState(null, '', redirectTarget) }
    catch { /* AuthContext exposes the safe message. */ }
    finally { setBusy(false) }
  }

  async function requestRecovery(event: FormEvent) {
    event.preventDefault()
    setRecoveryBusy(true)
    setRecoveryMessage(null)
    setRecoveryError(null)
    try {
      const result = await authApi.requestPasswordReset(recoveryEmail)
      setRecoveryMessage(result.message)
    } catch (cause) { setRecoveryError(getApiError(cause)) }
    finally { setRecoveryBusy(false) }
  }

  return <main className="flex min-h-[100dvh] items-center justify-center bg-canvas p-4 text-charcoal dark:bg-dark-canvas dark:text-slate-100" aria-labelledby="auth-title">
    <section className="w-full max-w-md rounded-container border border-border bg-white p-6 shadow-2xl dark:border-dark-border dark:bg-dark-surface">
      <div><img src={logoColor} alt="CDM Contabilidade" className="h-10 w-auto object-contain object-left" /><h1 id="auth-title" className="mt-4 text-2xl font-semibold text-navy dark:text-slate-100">{forgotMode ? 'Recuperar senha' : 'Entrar na sua conta'}</h1></div>
      {!forgotMode ? <form onSubmit={submit} className="mt-6 space-y-4">
        <label htmlFor="login-email" className="block text-sm font-medium text-charcoal dark:text-slate-200">Email<input id="login-email" ref={firstRef} autoComplete="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 text-charcoal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
        <label htmlFor="login-password" className="block text-sm font-medium text-charcoal dark:text-slate-200">Senha<input id="login-password" autoComplete="current-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 text-charcoal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
        {error && <p role="alert" className="rounded-control bg-red-50 px-3 py-2 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-200">{error}</p>}
        <button type="submit" disabled={busy} className="h-11 w-full rounded-control bg-blue font-medium text-white hover:bg-navy disabled:opacity-50">{busy ? 'Aguarde...' : 'Entrar'}</button>
        <button type="button" onClick={() => { setForgotMode(true); setRecoveryEmail(email) }} className="w-full text-sm font-medium text-blue underline underline-offset-2 hover:text-navy">Esqueci minha senha</button>
      </form> : <form onSubmit={requestRecovery} className="mt-6 space-y-4">
        <p className="text-sm leading-6 text-secondary dark:text-slate-300">Informe seu email de acesso. Se ele estiver cadastrado, o administrador será notificado.</p>
        <label htmlFor="recovery-email" className="block text-sm font-medium text-charcoal dark:text-slate-200">Email<input id="recovery-email" ref={firstRef} autoComplete="email" type="email" value={recoveryEmail} onChange={(event) => setRecoveryEmail(event.target.value)} required className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 text-charcoal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
        {recoveryError && <p role="alert" className="rounded-control bg-red-50 px-3 py-2 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-200">{recoveryError}</p>}
        {recoveryMessage && <p role="status" className="rounded-control bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200">{recoveryMessage}</p>}
        <button type="submit" disabled={recoveryBusy} className="h-11 w-full rounded-control bg-blue font-medium text-white hover:bg-navy disabled:opacity-50">{recoveryBusy ? 'Enviando...' : 'Solicitar recuperação'}</button>
        <button type="button" onClick={() => { setForgotMode(false); setRecoveryMessage(null); setRecoveryError(null) }} className="w-full text-sm font-medium text-blue underline underline-offset-2 hover:text-navy">Voltar para o login</button>
      </form>}
    </section>
  </main>
}
