import { X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import logoColor from '../../logo/logo_color.png'
import { useAuth } from '../contexts/AuthContext'

export function AuthModal({ onClose }: { onClose: () => void }) {
  const { login, error } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const firstRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    firstRef.current?.focus()
    function onKeyDown(event: KeyboardEvent) { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)
    try { await login(email, password); onClose() }
    catch { /* AuthContext exposes the safe message. */ }
    finally { setBusy(false) }
  }

  return <div className="fixed inset-0 z-30 flex items-center justify-center bg-navy/55 p-4 dark:bg-black/70" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <section role="dialog" aria-modal="true" aria-labelledby="auth-title" className="w-full max-w-md rounded-container border border-border bg-white p-6 shadow-2xl dark:border-dark-border dark:bg-dark-surface">
      <div className="flex items-start justify-between"><div><img src={logoColor} alt="CDM Contabilidade" className="h-10 w-auto object-contain object-left" /><h2 id="auth-title" className="mt-4 text-2xl font-semibold text-navy dark:text-slate-100">Entrar na sua conta</h2></div><button type="button" onClick={onClose} className="rounded-control p-2 text-secondary hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/10" aria-label="Fechar"><X size={18} /></button></div>
      <form onSubmit={submit} className="mt-6 space-y-4">
        <label className="block text-sm font-medium text-charcoal dark:text-slate-200">Email<input ref={firstRef} type="email" value={email} onChange={(event) => setEmail(event.target.value)} required className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 text-charcoal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
        <label className="block text-sm font-medium text-charcoal dark:text-slate-200">Senha<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 text-charcoal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
        {error && <p role="alert" className="rounded-control bg-red-50 px-3 py-2 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-200">{error}</p>}
        <button disabled={busy} className="h-11 w-full rounded-control bg-blue font-medium text-white hover:bg-navy disabled:opacity-50">{busy ? 'Aguarde...' : 'Entrar'}</button>
      </form>
    </section>
  </div>
}
