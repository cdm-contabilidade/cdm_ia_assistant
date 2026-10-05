import { ArrowLeft, LockKeyhole, Mail, Moon, ShieldCheck, Sun } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import logoColor from '../../logo/logo_color.png'
import logoWhite from '../../logo/logo_white.png'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { authApi, getApiError } from '../services/api'

type LoginPageProps = { redirectTarget: string }

const inputClassName = 'mt-2 h-12 w-full rounded-control border border-border bg-white px-4 pl-11 text-charcoal shadow-sm outline-none transition placeholder:text-secondary/60 hover:border-blue/50 focus:border-blue focus:ring-4 focus:ring-blue/10 dark:border-dark-border dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500'

export function LoginPage({ redirectTarget }: LoginPageProps) {
  const { login, error } = useAuth()
  const { theme, toggleTheme } = useTheme()
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

  function openRecovery() {
    setForgotMode(true)
    setRecoveryEmail(email)
    setRecoveryMessage(null)
    setRecoveryError(null)
  }

  function closeRecovery() {
    setForgotMode(false)
    setRecoveryMessage(null)
    setRecoveryError(null)
  }

  return (
    <main className="grid min-h-[100dvh] bg-canvas text-charcoal dark:bg-dark-canvas dark:text-slate-100 lg:grid-cols-[minmax(0,1.08fr)_minmax(420px,0.92fr)]" aria-labelledby="auth-title">
      <aside className="relative hidden min-h-[100dvh] overflow-hidden bg-navy px-10 py-10 text-white lg:flex lg:flex-col lg:justify-between xl:px-16">
        <div className="pointer-events-none absolute -right-24 -top-16 h-80 w-80 rounded-full border border-white/10" aria-hidden="true" />
        <div className="pointer-events-none absolute -bottom-36 -left-28 h-[28rem] w-[28rem] rounded-full border border-white/10" aria-hidden="true" />
        <div className="relative z-10">
          <img src={logoWhite} alt="CDM Contabilidade" className="h-14 w-auto max-w-[18rem] object-contain object-left" />
          <div className="mt-20 max-w-xl">
            <p className="text-sm font-medium uppercase tracking-[.2em] text-gold">CDM AI Assistant</p>
            <h2 className="mt-5 max-w-lg text-4xl font-semibold leading-[1.08] tracking-[-.035em] text-balance xl:text-5xl">Conhecimento contábil para decisões mais claras.</h2>
            <p className="mt-6 max-w-md text-base leading-7 text-white/75">Consulte bases internas, explore fontes e mantenha o contexto em cada conversa com o time CDM.</p>
          </div>
        </div>
        <div className="relative z-10 flex max-w-md items-start gap-3 border-t border-white/15 pt-5 text-sm leading-6 text-white/65">
          <ShieldCheck size={19} className="mt-1 shrink-0 text-gold" aria-hidden="true" />
          <p>Ambiente exclusivo para colaboradores autorizados.</p>
        </div>
      </aside>

      <section className="relative flex min-h-[100dvh] items-center justify-center px-4 py-8 sm:px-8 lg:px-12">
        <button type="button" onClick={toggleTheme} className="absolute right-4 top-4 inline-flex h-10 w-10 items-center justify-center rounded-control border border-border bg-white text-secondary shadow-sm transition hover:border-blue/50 hover:text-navy focus:outline-none focus:ring-4 focus:ring-blue/10 active:scale-[.97] dark:border-dark-border dark:bg-dark-surface dark:text-slate-300 dark:hover:text-white sm:right-8 sm:top-8" aria-label={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'} title={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'}>
          {theme === 'dark' ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
        </button>

        <div className="w-full max-w-[31rem]">
          <div className="mb-8 lg:hidden">
            <img src={logoColor} alt="CDM Contabilidade" className="h-11 w-auto object-contain object-left dark:hidden" />
            <img src={logoWhite} alt="CDM Contabilidade" className="hidden h-11 w-auto object-contain object-left dark:block" />
          </div>

          <div className="rounded-container border border-border bg-white p-6 shadow-panel dark:border-dark-border dark:bg-dark-surface sm:p-9">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[.18em] text-wine dark:text-wine-soft">Seu espaço de trabalho</p>
              <h1 id="auth-title" className="mt-3 text-3xl font-semibold leading-tight tracking-[-.03em] text-navy dark:text-slate-100">{forgotMode ? 'Recuperar senha' : 'Entrar na sua conta'}</h1>
              {!forgotMode && <p className="mt-3 max-w-[40ch] text-sm leading-6 text-secondary dark:text-slate-300">Acesse o assistente da CDM para consultar informações e trabalhar com mais contexto.</p>}
            </div>

            {!forgotMode ? (
              <form onSubmit={submit} className="mt-8 space-y-5">
                <label htmlFor="login-email" className="block text-sm font-medium text-charcoal dark:text-slate-200">
                  Email
                  <span className="relative block">
                    <Mail size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-secondary/70 dark:text-slate-500" aria-hidden="true" />
                    <input id="login-email" ref={firstRef} autoComplete="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required className={inputClassName} />
                  </span>
                </label>
                <label htmlFor="login-password" className="block text-sm font-medium text-charcoal dark:text-slate-200">
                  Senha
                  <span className="relative block">
                    <LockKeyhole size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-secondary/70 dark:text-slate-500" aria-hidden="true" />
                    <input id="login-password" autoComplete="current-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} className={inputClassName} />
                  </span>
                </label>
                {error && <p role="alert" className="rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm leading-5 text-red-800 dark:border-red-900/70 dark:bg-red-950/40 dark:text-red-200">{error}</p>}
                <button type="submit" disabled={busy} className="h-12 w-full rounded-control bg-blue font-semibold text-white shadow-[0_8px_18px_rgba(26,78,133,.2)] transition hover:bg-navy focus:outline-none focus:ring-4 focus:ring-blue/20 active:scale-[.99] disabled:cursor-not-allowed disabled:opacity-50">{busy ? 'Aguarde...' : 'Entrar'}</button>
                <button type="button" onClick={openRecovery} className="w-full text-sm font-semibold text-blue transition hover:text-navy hover:underline hover:underline-offset-4 focus:outline-none focus:ring-4 focus:ring-blue/10 dark:text-slate-200 dark:hover:text-white">Esqueci minha senha</button>
              </form>
            ) : (
              <form onSubmit={requestRecovery} className="mt-8 space-y-5">
                <p className="max-w-[42ch] text-sm leading-6 text-secondary dark:text-slate-300">Informe seu email de acesso. Se ele estiver cadastrado, o administrador será notificado.</p>
                <label htmlFor="recovery-email" className="block text-sm font-medium text-charcoal dark:text-slate-200">
                  Email
                  <span className="relative block">
                    <Mail size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-secondary/70 dark:text-slate-500" aria-hidden="true" />
                    <input id="recovery-email" ref={firstRef} autoComplete="email" type="email" value={recoveryEmail} onChange={(event) => setRecoveryEmail(event.target.value)} required className={inputClassName} />
                  </span>
                </label>
                {recoveryError && <p role="alert" className="rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm leading-5 text-red-800 dark:border-red-900/70 dark:bg-red-950/40 dark:text-red-200">{recoveryError}</p>}
                {recoveryMessage && <p role="status" className="rounded-control border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm leading-5 text-emerald-800 dark:border-emerald-900/70 dark:bg-emerald-950/40 dark:text-emerald-200">{recoveryMessage}</p>}
                <button type="submit" disabled={recoveryBusy} className="h-12 w-full rounded-control bg-blue font-semibold text-white shadow-[0_8px_18px_rgba(26,78,133,.2)] transition hover:bg-navy focus:outline-none focus:ring-4 focus:ring-blue/20 active:scale-[.99] disabled:cursor-not-allowed disabled:opacity-50">{recoveryBusy ? 'Enviando...' : 'Solicitar recuperação'}</button>
                <button type="button" onClick={closeRecovery} className="inline-flex w-full items-center justify-center gap-2 text-sm font-semibold text-blue transition hover:text-navy hover:underline hover:underline-offset-4 focus:outline-none focus:ring-4 focus:ring-blue/10 dark:text-slate-200 dark:hover:text-white"><ArrowLeft size={16} aria-hidden="true" />Voltar para o login</button>
              </form>
            )}
          </div>

          <p className="mt-6 text-center text-xs leading-5 text-secondary dark:text-slate-400">Use suas credenciais corporativas para entrar com segurança.</p>
        </div>
      </section>
    </main>
  )
}
