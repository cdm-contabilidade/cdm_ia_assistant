import { CheckCircle2, KeyRound, RefreshCw, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { adminApi, getApiError } from '../services/api'
import type { ProviderName, ProviderStatus } from '../types'

const providers: Array<{ id: ProviderName; label: string; hint: string }> = [
  { id: 'gemini', label: 'Google Gemini', hint: 'Usado para respostas com Store/RAG.' },
  { id: 'openai', label: 'OpenAI', hint: 'Usado para conversa e pesquisa na web.' },
]
const field = 'h-10 w-full rounded-control border border-border bg-white px-3 text-sm focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100'
const action = 'inline-flex items-center justify-center gap-2 rounded-control px-3 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-blue/30 disabled:cursor-not-allowed disabled:opacity-50'

export function ProviderCredentialsPanel() {
  const [items, setItems] = useState<ProviderStatus[]>([])
  const [keys, setKeys] = useState<Record<ProviderName, string>>({ gemini: '', openai: '' })
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  async function load() {
    setLoading(true); setError('')
    try { setItems(await adminApi.providers()) } catch (cause) { setError(getApiError(cause)) } finally { setLoading(false) }
  }
  useEffect(() => { void load() }, [])
  const status = (provider: ProviderName) => items.find((item) => item.provider === provider)
  async function save(provider: ProviderName) {
    const apiKey = keys[provider].trim(); if (!apiKey) return
    setBusy(`save-${provider}`); setError('')
    try { const updated = await adminApi.saveProviderCredential(provider, apiKey); setItems((current) => [...current.filter((item) => item.provider !== provider), updated]); setKeys((current) => ({ ...current, [provider]: '' })) }
    catch (cause) { setError(getApiError(cause)) }
    finally { setKeys((current) => ({ ...current, [provider]: '' })); setBusy('') }
  }
  async function importEnv(provider: ProviderName) {
    setBusy(`import-${provider}`); setError('')
    try { const updated = await adminApi.importProviderCredential(provider); setItems((current) => [...current.filter((item) => item.provider !== provider), updated]) }
    catch (cause) { setError(getApiError(cause)) } finally { setKeys((current) => ({ ...current, [provider]: '' })); setBusy('') }
  }
  async function remove(provider: ProviderName) {
    setBusy(`delete-${provider}`); setError('')
    try { await adminApi.removeProviderCredential(provider); setItems(await adminApi.providers()) }
    catch (cause) { setError(getApiError(cause)) } finally { setBusy('') }
  }
  async function revertToEnv(provider: ProviderName) {
    setBusy(`revert-${provider}`); setError('')
    try { const updated = await adminApi.revertProviderToEnv(provider); setItems((current) => [...current.filter((item) => item.provider !== provider), updated]) }
    catch (cause) { setError(getApiError(cause)) } finally { setKeys((current) => ({ ...current, [provider]: '' })); setBusy('') }
  }

  return <section aria-labelledby="provider-credentials-title" className="rounded-container border border-border bg-white p-5 shadow-panel dark:border-dark-border dark:bg-dark-surface">
    <div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control bg-gold/15 text-gold"><KeyRound size={20} /></span><div><h2 id="provider-credentials-title" className="text-lg font-semibold text-navy dark:text-slate-100">Credenciais dos provedores</h2><p className="mt-1 text-sm text-secondary dark:text-slate-400">A chave nunca é exibida. Você verá apenas a origem e um sufixo mascarado.</p></div></div>
    {error && <div role="alert" className="mt-4 flex items-center justify-between gap-3 rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200"><span>{error}</span><button type="button" onClick={() => void load()} className="inline-flex items-center gap-2 font-semibold underline"><RefreshCw size={14} />Tentar novamente</button></div>}
    {loading ? <p className="mt-5 text-sm text-secondary dark:text-slate-400">Carregando status das credenciais...</p> : <div className="mt-5 grid gap-4 lg:grid-cols-2">{providers.map(({ id, label, hint }) => { const current = status(id); return <article key={id} className="rounded-control border border-border bg-canvas/60 p-4 dark:border-dark-border dark:bg-dark-canvas"><div className="flex items-start justify-between gap-3"><div><h3 className="font-semibold text-navy dark:text-slate-100">{label}</h3><p className="mt-1 text-xs text-secondary dark:text-slate-400">{hint}</p></div>{current?.configured ? <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-1 text-[11px] font-semibold text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200"><CheckCircle2 size={13} />Configurada</span> : <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-secondary dark:bg-slate-800 dark:text-slate-300">Não configurada</span>}</div><p className="mt-3 text-xs text-secondary dark:text-slate-400">Origem: <strong className="font-semibold text-charcoal dark:text-slate-200">{current?.source === 'database' ? 'banco de dados' : current?.source === 'environment' ? 'ambiente' : 'nenhuma'}{current?.maskedKey ? ` · ${current.maskedKey}` : ''}</strong></p><label className="mt-4 block text-xs font-medium text-secondary dark:text-slate-400">Nova chave<input type="password" autoComplete="new-password" value={keys[id]} onChange={(event) => setKeys((all) => ({ ...all, [id]: event.target.value }))} placeholder="Informe para substituir" className={`${field} mt-1`} /></label><div className="mt-3 flex flex-wrap gap-2"><button type="button" disabled={!keys[id].trim() || busy === `save-${id}`} onClick={() => void save(id)} className={`${action} bg-blue text-white hover:bg-navy`}>{busy === `save-${id}` ? 'Salvando...' : 'Salvar chave'}</button><button type="button" disabled={busy === `import-${id}`} onClick={() => void importEnv(id)} className={`${action} border border-border text-navy hover:border-blue dark:border-dark-border dark:text-slate-100`}>{busy === `import-${id}` ? 'Importando...' : 'Importar do ambiente'}</button><button type="button" disabled={busy === `revert-${id}`} onClick={() => void revertToEnv(id)} className={`${action} border border-border text-navy hover:border-blue dark:border-dark-border dark:text-slate-100`}>{busy === `revert-${id}` ? 'Aplicando...' : 'Usar configuração do ambiente'}</button>{current?.source === 'database' && <button type="button" disabled={busy === `delete-${id}`} onClick={() => void remove(id)} className={`${action} text-red-700 hover:bg-red-50 dark:text-red-200`}><Trash2 size={15} />Desativar chave salva</button>}</div></article> })}</div>}
  </section>
}
