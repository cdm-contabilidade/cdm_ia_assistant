import { useEffect, useRef, useState, type FormEvent } from 'react'
import { getApiError } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

type ChangePasswordModalProps = {
  onClose: () => void
}

export function ChangePasswordModal({ onClose }: ChangePasswordModalProps) {
  const { changePassword } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const closeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    closeRef.current?.focus()
    const handleKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape' && !busy) onClose() }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [busy, onClose])

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (newPassword !== confirmation) { setError('A confirmação da senha não confere.'); return }
    setBusy(true)
    setError(null)
    try { await changePassword(currentPassword, newPassword); onClose() }
    catch (cause) { setError(getApiError(cause)) }
    finally { setBusy(false) }
  }

  function handleBackdropMouseDown(event: React.MouseEvent<HTMLDivElement>) {
    if (!busy && event.target === event.currentTarget) onClose()
  }

  return <div className="fixed inset-0 z-30 flex items-center justify-center bg-navy/55 p-4 dark:bg-black/70" role="presentation" onMouseDown={handleBackdropMouseDown}>
    <section role="dialog" aria-modal="true" aria-labelledby="change-password-title" className="w-full max-w-md rounded-container border border-border bg-white p-6 shadow-[0_20px_50px_rgba(10,31,68,0.22)] dark:border-dark-border dark:bg-dark-surface">
      <div className="flex items-start justify-between gap-4">
        <div><h2 id="change-password-title" className="text-xl font-semibold text-navy dark:text-slate-100">Trocar senha</h2><p className="mt-2 text-sm text-secondary dark:text-slate-300">Informe sua senha atual e escolha uma nova senha.</p></div>
        <button ref={closeRef} type="button" onClick={onClose} disabled={busy} aria-label="Fechar troca de senha" className="rounded-control px-2 py-1 text-secondary hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue/50 disabled:opacity-50 dark:hover:bg-white/10">Fechar</button>
      </div>
      <form onSubmit={submit} className="mt-5 space-y-4">
        <label className="block text-sm font-medium text-charcoal dark:text-slate-200">Senha atual<input required type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 font-normal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
        <label className="block text-sm font-medium text-charcoal dark:text-slate-200">Nova senha<input required minLength={8} type="password" autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 font-normal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
        <label className="block text-sm font-medium text-charcoal dark:text-slate-200">Confirmar nova senha<input required minLength={8} type="password" autoComplete="new-password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 font-normal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
        {error && <p role="alert" className="rounded-control bg-red-50 px-3 py-2 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-200">{error}</p>}
        <div className="flex justify-end gap-3 pt-2"><button type="button" onClick={onClose} disabled={busy} className="h-11 rounded-control border border-border px-4 text-sm font-medium text-charcoal hover:bg-slate-50 disabled:opacity-50 dark:border-dark-border dark:text-slate-100 dark:hover:bg-white/10">Cancelar</button><button type="submit" disabled={busy} className="h-11 rounded-control bg-blue px-4 text-sm font-medium text-white hover:bg-navy disabled:opacity-50">{busy ? 'Salvando...' : 'Salvar nova senha'}</button></div>
      </form>
    </section>
  </div>
}
