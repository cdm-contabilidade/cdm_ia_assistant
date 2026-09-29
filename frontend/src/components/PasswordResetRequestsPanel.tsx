import { KeyRound, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import { adminApi, getApiError } from '../services/api'
import type { PasswordResetRequest } from '../types'

export function PasswordResetRequestsPanel() {
  const [requests, setRequests] = useState<PasswordResetRequest[]>([])
  const [passwords, setPasswords] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function loadRequests() {
    setLoading(true)
    setError(null)
    try { setRequests(await adminApi.passwordResetRequests()) }
    catch (cause) { setError(getApiError(cause)) }
    finally { setLoading(false) }
  }

  useEffect(() => { void loadRequests() }, [])

  async function resetPassword(request: PasswordResetRequest) {
    const password = passwords[request.id] || ''
    if (password.length < 8) { setError('A senha deve ter pelo menos 8 caracteres.'); return }
    setBusy(request.id)
    setError(null)
    setSuccess(null)
    try {
      await adminApi.resetPassword(request.id, password)
      setRequests((current) => current.filter((item) => item.id !== request.id))
      setPasswords((current) => ({ ...current, [request.id]: '' }))
      setSuccess(`Senha redefinida para ${request.email}.`)
    } catch (cause) { setError(getApiError(cause)) }
    finally { setBusy(null) }
  }

  return <section className="mt-6" aria-labelledby="password-reset-requests-title">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 id="password-reset-requests-title" className="text-lg font-semibold text-navy dark:text-slate-100">Solicitações de senha</h2><p className="mt-1 text-sm text-secondary dark:text-slate-400">Defina uma nova senha para cada solicitação pendente.</p></div><button type="button" onClick={() => void loadRequests()} className="inline-flex items-center gap-2 rounded-control border border-border px-3 py-2 text-sm font-medium text-navy hover:border-blue dark:border-dark-border dark:text-slate-100"><RefreshCw size={15} />Atualizar</button></div>
    {error && <div role="alert" className="mt-4 rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">{error}</div>}
    {success && <div role="status" className="mt-4 rounded-control border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200">{success}</div>}
    {loading ? <div className="mt-4 rounded-container border border-border bg-white p-6 text-sm text-secondary dark:border-dark-border dark:bg-dark-surface dark:text-slate-400">Carregando solicitações...</div> : requests.length === 0 ? <div className="mt-4 rounded-container border border-dashed border-border bg-white p-8 text-center text-sm text-secondary dark:border-dark-border dark:bg-dark-surface dark:text-slate-400">Nenhuma solicitação pendente.</div> : <div className="mt-4 space-y-3">{requests.map((request) => <article key={request.id} className="rounded-container border border-border bg-white p-4 shadow-panel dark:border-dark-border dark:bg-dark-surface"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-medium text-navy dark:text-slate-100">{request.name}</p><p className="text-sm text-secondary dark:text-slate-400">{request.email}</p><p className="mt-1 text-xs text-secondary dark:text-slate-500">Solicitada em {new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(request.created_at))}</p></div><KeyRound size={18} className="text-blue" aria-hidden="true" /></div><div className="mt-3 flex flex-col gap-2 sm:flex-row"><label className="flex-1 text-sm font-medium text-charcoal dark:text-slate-200"><span className="sr-only">Nova senha para {request.email}</span><input type="password" minLength={8} autoComplete="new-password" placeholder="Nova senha (mínimo 8 caracteres)" value={passwords[request.id] || ''} onChange={(event) => setPasswords((current) => ({ ...current, [request.id]: event.target.value }))} className="h-11 w-full rounded-control border border-border bg-white px-3 font-normal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label><button type="button" onClick={() => void resetPassword(request)} disabled={busy === request.id} className="h-11 rounded-control bg-blue px-4 text-sm font-medium text-white hover:bg-navy disabled:opacity-50">{busy === request.id ? 'Salvando...' : 'Redefinir senha'}</button></div></article>)}</div>}
  </section>
}
