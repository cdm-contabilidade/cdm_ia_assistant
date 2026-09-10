import { ArrowLeft, RefreshCw, ShieldCheck, UserPlus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { adminApi, getApiError } from '../services/api'
import type { AdminUser } from '../types'

type AdminPanelProps = { onClose: () => void }

type NewUser = { name: string; email: string; password: string }

const emptyUser: NewUser = { name: '', email: '', password: '' }

export function AdminPanel({ onClose }: AdminPanelProps) {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [newUser, setNewUser] = useState<NewUser>(emptyUser)
  const [passwords, setPasswords] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function loadUsers() {
    setLoading(true)
    setError(null)
    try { setUsers(await adminApi.users()) }
    catch (cause) { setError(getApiError(cause)) }
    finally { setLoading(false) }
  }

  useEffect(() => { void loadUsers() }, [])

  async function createUser(event: React.FormEvent) {
    event.preventDefault()
    setBusy('create')
    setError(null)
    try {
      const created = await adminApi.createUser(newUser)
      setUsers((current) => [...current, created].sort((left, right) => left.name.localeCompare(right.name)))
      setNewUser(emptyUser)
    } catch (cause) { setError(getApiError(cause)) }
    finally { setBusy(null) }
  }

  async function updateUser(user: AdminUser, payload: { password?: string; is_active?: boolean; is_blacklisted?: boolean }) {
    setBusy(user.id)
    setError(null)
    try {
      const updated = await adminApi.updateUser(user.id, payload)
      setUsers((current) => current.map((item) => item.id === user.id ? updated : item))
      if (payload.password) setPasswords((current) => ({ ...current, [user.id]: '' }))
    } catch (cause) { setError(getApiError(cause)) }
    finally { setBusy(null) }
  }

  return <main className="min-w-0 flex-1 overflow-y-auto bg-canvas dark:bg-dark-canvas">
    <div className="mx-auto max-w-6xl px-5 py-8 md:px-10">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-6 dark:border-dark-border">
        <div><p className="text-sm font-medium text-blue">Administração</p><h1 className="mt-1 text-3xl font-semibold text-navy dark:text-slate-100">Colaboradores</h1><p className="mt-2 max-w-2xl text-sm text-secondary dark:text-slate-400">Gerencie acesso, senha e bloqueios. O consumo de tokens será adicionado em uma etapa futura.</p></div>
        <button type="button" onClick={onClose} className="inline-flex items-center gap-2 rounded-control border border-border bg-white px-3 py-2 text-sm font-medium text-navy hover:border-blue dark:border-dark-border dark:bg-dark-surface dark:text-slate-100"><ArrowLeft size={16} />Voltar ao chat</button>
      </header>

      {error && <div role="alert" className="mt-5 flex items-center justify-between rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200"><span>{error}</span><button type="button" onClick={() => void loadUsers()} className="inline-flex items-center gap-2 font-medium underline"><RefreshCw size={14} />Tentar novamente</button></div>}

      <section className="mt-6 rounded-container border border-border bg-white p-5 shadow-panel dark:border-dark-border dark:bg-dark-surface" aria-labelledby="new-collaborator-title">
        <div className="flex items-center gap-2"><UserPlus size={18} className="text-blue" /><h2 id="new-collaborator-title" className="text-lg font-semibold text-navy dark:text-slate-100">Novo colaborador</h2></div>
        <form onSubmit={createUser} className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_1fr_auto] md:items-end">
          <label className="text-sm font-medium text-charcoal dark:text-slate-200">Nome<input required minLength={1} maxLength={120} value={newUser.name} onChange={(event) => setNewUser({ ...newUser, name: event.target.value })} className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 font-normal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
          <label className="text-sm font-medium text-charcoal dark:text-slate-200">Email<input required type="email" value={newUser.email} onChange={(event) => setNewUser({ ...newUser, email: event.target.value })} className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 font-normal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
          <label className="text-sm font-medium text-charcoal dark:text-slate-200">Senha inicial<input required type="password" minLength={8} value={newUser.password} onChange={(event) => setNewUser({ ...newUser, password: event.target.value })} className="mt-1 h-11 w-full rounded-control border border-border bg-white px-3 font-normal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
          <button type="submit" disabled={busy === 'create'} className="inline-flex h-11 items-center justify-center gap-2 rounded-control bg-blue px-4 text-sm font-medium text-white hover:bg-navy disabled:opacity-50"><UserPlus size={16} />{busy === 'create' ? 'Criando...' : 'Criar'}</button>
        </form>
      </section>

      <section className="mt-6" aria-labelledby="collaborator-list-title"><div className="flex items-center justify-between gap-3"><h2 id="collaborator-list-title" className="text-lg font-semibold text-navy dark:text-slate-100">Usuários cadastrados</h2><span className="text-sm text-secondary dark:text-slate-400">{users.length} colaborador{users.length === 1 ? '' : 'es'}</span></div>{loading ? <div className="mt-4 rounded-container border border-border bg-white p-6 text-sm text-secondary dark:border-dark-border dark:bg-dark-surface dark:text-slate-400">Carregando colaboradores...</div> : users.length === 0 ? <div className="mt-4 rounded-container border border-dashed border-border bg-white p-8 text-center text-sm text-secondary dark:border-dark-border dark:bg-dark-surface dark:text-slate-400">Nenhum colaborador cadastrado.</div> : <div className="mt-4 overflow-hidden rounded-container border border-border bg-white dark:border-dark-border dark:bg-dark-surface"><div className="divide-y divide-border dark:divide-dark-border">{users.map((user) => <article key={user.id} className="p-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><h3 className="font-semibold text-navy dark:text-slate-100">{user.name}</h3><p className="text-sm text-secondary dark:text-slate-400">{user.email}</p></div><div className="flex flex-wrap items-center gap-2 text-xs font-medium"><span className={`rounded-full px-2.5 py-1 ${user.is_active ? 'bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-200' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'}`}>{user.is_active ? 'Ativo' : 'Desativado'}</span>{user.is_blacklisted && <span className="rounded-full bg-red-100 px-2.5 py-1 text-red-800 dark:bg-red-950/40 dark:text-red-200">Blacklist</span>}</div></div><div className="mt-4 flex flex-wrap items-end gap-2"><label className="min-w-[220px] flex-1 text-xs font-medium text-secondary dark:text-slate-400">Nova senha<input type="password" minLength={8} value={passwords[user.id] || ''} onChange={(event) => setPasswords((current) => ({ ...current, [user.id]: event.target.value }))} className="mt-1 h-10 w-full rounded-control border border-border bg-white px-3 text-sm text-charcoal focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label><button type="button" disabled={busy === user.id || (passwords[user.id] || '').length < 8} onClick={() => void updateUser(user, { password: passwords[user.id] })} className="h-10 rounded-control border border-border px-3 text-sm font-medium text-navy hover:border-blue disabled:opacity-50 dark:border-dark-border dark:text-slate-100">Trocar senha</button><button type="button" disabled={busy === user.id} onClick={() => void updateUser(user, { is_active: !user.is_active })} className="h-10 rounded-control border border-border px-3 text-sm font-medium text-navy hover:border-blue disabled:opacity-50 dark:border-dark-border dark:text-slate-100">{user.is_active ? 'Desativar' : 'Ativar'}</button><button type="button" disabled={busy === user.id} onClick={() => void updateUser(user, { is_blacklisted: !user.is_blacklisted })} className="inline-flex h-10 items-center gap-2 rounded-control border border-red-200 px-3 text-sm font-medium text-red-800 hover:bg-red-50 disabled:opacity-50 dark:border-red-900 dark:text-red-200 dark:hover:bg-red-950/30"><ShieldCheck size={15} />{user.is_blacklisted ? 'Remover blacklist' : 'Colocar em blacklist'}</button></div></article>)}</div></div>}</section>
    </div>
  </main>
}
