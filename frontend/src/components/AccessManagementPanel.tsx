import { Database, Globe, Plus, Save, Shield, Trash2, Users, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { adminApi, catalogsApi, getApiError } from '../services/api'
import type { AccessGroup, AdminUser, KnowledgeBase, PermissionOverride } from '../types'

type Props = { users: AdminUser[] }
const inputClass = 'h-10 rounded-control border border-border bg-white px-3 text-sm focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100'
const buttonClass = 'inline-flex items-center justify-center gap-2 rounded-control px-3 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-blue/30 disabled:cursor-not-allowed disabled:opacity-50'

export function AccessManagementPanel({ users }: Props) {
  const [groups, setGroups] = useState<AccessGroup[]>([])
  const [bases, setBases] = useState<KnowledgeBase[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [draftUsers, setDraftUsers] = useState<string[]>([])
  const [draftBases, setDraftBases] = useState<string[]>([])
  const [draftWeb, setDraftWeb] = useState(false)
  const [newName, setNewName] = useState('')
  const [expandedUser, setExpandedUser] = useState<string | null>(null)
  const [overrides, setOverrides] = useState<Record<string, PermissionOverride[]>>({})
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const selected = groups.find((group) => group.id === selectedId)
  const showError = (cause: unknown) => setError(getApiError(cause))

  async function load() {
    setError('')
    try {
      const [loadedGroups, loadedBases] = await Promise.all([adminApi.groups(), catalogsApi.knowledgeBases()])
      setGroups(loadedGroups); setBases(loadedBases)
      if (loadedGroups.length && !selectedId) setSelectedId(loadedGroups[0].id)
    } catch (cause) { showError(cause) }
  }
  useEffect(() => { void load() }, [])
  useEffect(() => {
    if (!selected) return
    setDraftUsers(selected.userIds || []); setDraftBases(selected.knowledgeBaseIds || []); setDraftWeb(selected.webSearch === true)
  }, [selectedId, groups])

  async function createGroup(event: React.FormEvent) {
    event.preventDefault(); if (!newName.trim()) return
    setBusy('new'); setError('')
    try { const group = await adminApi.createGroup({ name: newName.trim() }); setGroups((current) => [...current, group]); setSelectedId(group.id); setNewName('') }
    catch (cause) { showError(cause) } finally { setBusy('') }
  }
  async function saveMembers() {
    if (!selected) return; setBusy('members'); setError('')
    try { const group = await adminApi.replaceGroupMembers(selected.id, draftUsers); setGroups((current) => current.map((item) => item.id === group.id ? group : item)) }
    catch (cause) { showError(cause) } finally { setBusy('') }
  }
  async function saveGrants() {
    if (!selected) return; setBusy('grants'); setError('')
    try { const group = await adminApi.replaceGroupGrants(selected.id, { knowledgeBaseIds: draftBases, webSearch: draftWeb }); setGroups((current) => current.map((item) => item.id === group.id ? group : item)) }
    catch (cause) { showError(cause) } finally { setBusy('') }
  }
  async function deleteGroup() {
    if (!selected || selected.userIds.length || selected.knowledgeBaseIds.length || selected.webSearch) return
    setBusy('delete'); setError('')
    try { await adminApi.removeGroup(selected.id); const remaining = groups.filter((item) => item.id !== selected.id); setGroups(remaining); setSelectedId(remaining[0]?.id || '') }
    catch (cause) { showError(cause) } finally { setBusy('') }
  }
  async function toggleUser(userId: string) {
    setExpandedUser((current) => current === userId ? null : userId)
    if (overrides[userId]) return
    try { const loaded = await adminApi.permissionOverrides(userId); setOverrides((current) => ({ ...current, [userId]: loaded })) }
    catch (cause) { showError(cause) }
  }
  async function saveOverrides(userId: string) {
    setBusy(`override-${userId}`); setError('')
    try { const saved = await adminApi.replacePermissionOverrides(userId, overrides[userId] || []); setOverrides((current) => ({ ...current, [userId]: saved })) }
    catch (cause) { showError(cause) } finally { setBusy('') }
  }

  return <section className="mt-8" aria-labelledby="access-title">
    <div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[.16em] text-wine">Controle de acesso</p><h2 id="access-title" className="mt-1 text-xl font-semibold text-navy dark:text-slate-100">Grupos e exceções individuais</h2><p className="mt-1 max-w-3xl text-sm text-secondary dark:text-slate-400">Grupos definem as regras padrão. Exceções individuais permitem liberar ou negar um recurso para uma pessoa sem alterar o grupo.</p></div>
    {error && <div role="alert" className="mb-4 flex items-center justify-between gap-3 rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200"><span>{error}</span><button type="button" onClick={() => void load()} className="font-semibold underline">Tentar novamente</button></div>}
    <div className="grid gap-5 lg:grid-cols-[minmax(220px,.7fr)_minmax(0,1.6fr)]">
      <article className="rounded-container border border-border bg-white p-4 shadow-panel dark:border-dark-border dark:bg-dark-surface">
        <div className="flex items-center gap-2"><Shield size={18} className="text-wine" /><h3 className="font-semibold text-navy dark:text-slate-100">Grupos</h3></div>
        <form onSubmit={createGroup} className="mt-4 flex gap-2"><label className="sr-only" htmlFor="new-group">Nome do grupo</label><input id="new-group" required maxLength={120} value={newName} onChange={(event) => setNewName(event.target.value)} placeholder="Ex.: Comercial" className={`${inputClass} min-w-0 flex-1`} /><button className={`${buttonClass} bg-blue text-white hover:bg-navy`} disabled={busy === 'new'} aria-label="Criar grupo"><Plus size={16} />Criar</button></form>
        <div className="mt-4 space-y-2" role="list" aria-label="Grupos cadastrados">{groups.length === 0 ? <p className="rounded-control border border-dashed border-border p-4 text-sm text-secondary dark:border-dark-border dark:text-slate-400">Nenhum grupo criado.</p> : groups.map((group) => <button type="button" role="listitem" key={group.id} onClick={() => setSelectedId(group.id)} className={`w-full rounded-control border px-3 py-3 text-left transition ${selectedId === group.id ? 'border-blue bg-blue/5' : 'border-border hover:border-blue/50 dark:border-dark-border'}`}><span className="block font-semibold text-navy dark:text-slate-100">{group.name}</span><span className="mt-1 block text-xs text-secondary dark:text-slate-400">{group.userIds.length} membro{group.userIds.length === 1 ? '' : 's'} · {group.knowledgeBaseIds.length} base{group.knowledgeBaseIds.length === 1 ? '' : 's'}{group.webSearch ? ' · web' : ''}</span></button>)}</div>
      </article>
      <article className="rounded-container border border-border bg-white p-5 shadow-panel dark:border-dark-border dark:bg-dark-surface">{!selected ? <p className="py-8 text-center text-sm text-secondary dark:text-slate-400">Crie ou selecione um grupo para editar suas regras.</p> : <><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[.12em] text-blue">Regra do grupo</p><h3 className="mt-1 text-lg font-semibold text-navy dark:text-slate-100">{selected.name}</h3><p className="mt-1 text-sm text-secondary dark:text-slate-400">As alterações só entram em vigor ao salvar cada seção.</p></div><button type="button" onClick={() => void deleteGroup()} disabled={busy === 'delete' || !!selected.userIds.length || !!selected.knowledgeBaseIds.length || selected.webSearch} className={`${buttonClass} border border-red-200 text-red-700 hover:bg-red-50 dark:border-red-900 dark:text-red-200`} title={selected.userIds.length || selected.knowledgeBaseIds.length || selected.webSearch ? 'Remova membros e permissões antes de excluir' : 'Excluir grupo'}><Trash2 size={15} />Excluir</button></div>
        <div className="mt-5 grid gap-5 xl:grid-cols-2">
          <div><div className="flex items-center gap-2"><Users size={17} className="text-blue" /><h4 className="font-semibold text-navy dark:text-slate-100">Membros</h4></div><p className="mt-1 text-xs text-secondary dark:text-slate-400">Escolha quem recebe as regras deste grupo.</p><div className="mt-3 max-h-56 space-y-2 overflow-y-auto rounded-control border border-border p-3 dark:border-dark-border">{users.map((user) => <label key={user.id} className="flex items-center gap-3 text-sm text-charcoal dark:text-slate-200"><input type="checkbox" checked={draftUsers.includes(user.id)} onChange={() => setDraftUsers((current) => current.includes(user.id) ? current.filter((id) => id !== user.id) : [...current, user.id])} className="h-4 w-4 accent-blue" />{user.name}<span className="ml-auto text-xs text-secondary">{user.email}</span></label>)}</div><button type="button" onClick={() => void saveMembers()} disabled={busy === 'members'} className={`${buttonClass} mt-3 bg-blue text-white hover:bg-navy`}><Save size={15} />{busy === 'members' ? 'Salvando...' : 'Salvar membros'}</button></div>
          <div><div className="flex items-center gap-2"><Database size={17} className="text-wine" /><h4 className="font-semibold text-navy dark:text-slate-100">Recursos permitidos</h4></div><p className="mt-1 text-xs text-secondary dark:text-slate-400">Estas permissões são a base para todos os membros.</p><div className="mt-3 max-h-56 space-y-2 overflow-y-auto rounded-control border border-border p-3 dark:border-dark-border">{bases.map((base) => <label key={base.id} className="flex items-center gap-3 text-sm text-charcoal dark:text-slate-200"><input type="checkbox" checked={draftBases.includes(base.id)} onChange={() => setDraftBases((current) => current.includes(base.id) ? current.filter((id) => id !== base.id) : [...current, base.id])} className="h-4 w-4 accent-wine" />{base.name}</label>)}{bases.length === 0 && <p className="text-sm text-secondary">Nenhuma base disponível.</p>}<label className="flex items-center gap-3 border-t border-border pt-2 text-sm font-medium text-charcoal dark:border-dark-border dark:text-slate-200"><input type="checkbox" checked={draftWeb} onChange={(event) => setDraftWeb(event.target.checked)} className="h-4 w-4 accent-wine" /><Globe size={15} />Permitir pesquisa na web</label></div><button type="button" onClick={() => void saveGrants()} disabled={busy === 'grants'} className={`${buttonClass} mt-3 bg-wine text-white hover:bg-wine-soft`}><Save size={15} />{busy === 'grants' ? 'Salvando...' : 'Salvar permissões'}</button></div>
        </div></>}
      </article>
    </div>
    <div className="mt-6 rounded-container border border-border bg-white p-5 shadow-panel dark:border-dark-border dark:bg-dark-surface"><div className="flex items-start gap-3"><Shield size={18} className="mt-0.5 text-gold" /><div><h3 className="font-semibold text-navy dark:text-slate-100">Exceções por colaborador</h3><p className="mt-1 text-sm text-secondary dark:text-slate-400">Use somente para casos específicos. Uma exceção substitui a regra herdada do grupo.</p></div></div><div className="mt-4 divide-y divide-border dark:divide-dark-border">{users.map((user) => <UserOverride key={user.id} user={user} expanded={expandedUser === user.id} items={overrides[user.id]} busy={busy === `override-${user.id}`} onToggle={() => void toggleUser(user.id)} onChange={(items) => setOverrides((current) => ({ ...current, [user.id]: items }))} onSave={() => void saveOverrides(user.id)} bases={bases} />)}</div></div>
  </section>
}

function UserOverride({ user, expanded, items = [], busy, onToggle, onChange, onSave, bases }: { user: AdminUser; expanded: boolean; items?: PermissionOverride[]; busy: boolean; onToggle: () => void; onChange: (items: PermissionOverride[]) => void; onSave: () => void; bases: KnowledgeBase[] }) {
  const [target, setTarget] = useState('web_search')
  const exists = items.some((item) => (item.capability === 'web_search' && target === 'web_search') || (item.capability === 'knowledge_base' && item.knowledgeBaseId === target))
  const add = () => { if (exists) return; onChange([...items, target === 'web_search' ? { capability: 'web_search', allowed: true } : { capability: 'knowledge_base', knowledgeBaseId: target, allowed: true }]) }
  return <div className="py-3"><button type="button" onClick={onToggle} aria-expanded={expanded} className="flex w-full items-center justify-between gap-3 text-left"><span><span className="font-medium text-navy dark:text-slate-100">{user.name}</span><span className="ml-2 text-xs text-secondary dark:text-slate-400">{items.length} exceção{items.length === 1 ? '' : 'ões'}</span></span><span className="text-sm font-semibold text-blue">{expanded ? 'Recolher' : 'Editar'}</span></button>{expanded && <div className="mt-3 rounded-control bg-canvas p-3 dark:bg-dark-canvas"><div className="flex flex-wrap gap-2"><label className="sr-only" htmlFor={`override-target-${user.id}`}>Recurso da exceção</label><select id={`override-target-${user.id}`} value={target} onChange={(event) => setTarget(event.target.value)} className={`${inputClass} min-w-0 flex-1`}><option value="web_search">Pesquisa na web</option>{bases.map((base) => <option key={base.id} value={base.id}>{base.name}</option>)}</select><button type="button" onClick={add} disabled={exists} className={`${buttonClass} border border-border bg-white text-navy hover:border-blue dark:border-dark-border dark:bg-dark-surface dark:text-slate-100`}><Plus size={15} />Adicionar</button></div>{items.length > 0 && <div className="mt-3 space-y-2">{items.map((item, index) => <div key={`${item.capability}-${item.knowledgeBaseId || 'web'}`} className="flex flex-wrap items-center gap-2 rounded-control border border-border bg-white px-3 py-2 text-sm dark:border-dark-border dark:bg-dark-surface"><span className="min-w-0 flex-1 text-charcoal dark:text-slate-200">{item.capability === 'web_search' ? 'Pesquisa na web' : bases.find((base) => base.id === item.knowledgeBaseId)?.name || 'Base removida'}</span><select aria-label={`Efeito da exceção ${index + 1}`} value={item.allowed ? 'allow' : 'deny'} onChange={(event) => onChange(items.map((current, currentIndex) => currentIndex === index ? { ...current, allowed: event.target.value === 'allow' } : current))} className="h-9 rounded-control border border-border bg-white px-2 text-sm dark:border-dark-border dark:bg-dark-surface dark:text-slate-100"><option value="allow">Permitir</option><option value="deny">Negar</option></select><button type="button" aria-label="Remover exceção" onClick={() => onChange(items.filter((_, currentIndex) => currentIndex !== index))} className="p-2 text-secondary hover:text-red-700"><X size={16} /></button></div>)}</div>}<button type="button" onClick={onSave} disabled={busy} className={`${buttonClass} mt-3 bg-blue text-white hover:bg-navy`}><Save size={15} />{busy ? 'Salvando...' : 'Salvar exceções'}</button></div>}</div>
}
