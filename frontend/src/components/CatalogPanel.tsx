import { Cpu, Database } from 'lucide-react'
import { useEffect, useState } from 'react'
import { adminApi, catalogsApi, getApiError } from '../services/api'
import type { AiModel, KnowledgeBase } from '../types'

export function CatalogPanel() {
  const [models, setModels] = useState<AiModel[]>([])
  const [bases, setBases] = useState<KnowledgeBase[]>([])
  const [error, setError] = useState('')
  const [model, setModel] = useState({ provider: '', name: '', model_id: '' })
  const [base, setBase] = useState({ name: '', store_id: '' })

  const active = (item: AiModel | KnowledgeBase) => item.is_active !== false && item.isActive !== false

  useEffect(() => {
    void Promise.all([catalogsApi.aiModels(), catalogsApi.knowledgeBases()])
      .then(([loadedModels, loadedBases]) => { setModels(loadedModels); setBases(loadedBases) })
      .catch((cause) => setError(getApiError(cause)))
  }, [])

  async function createModel(event: React.FormEvent) {
    event.preventDefault()
    try {
      const created = await adminApi.createAiModel(model)
      setModels((current) => [...current, created])
      setModel({ provider: '', name: '', model_id: '' })
    } catch (cause) { setError(getApiError(cause)) }
  }

  async function createBase(event: React.FormEvent) {
    event.preventDefault()
    try {
      const created = await adminApi.createKnowledgeBase(base)
      setBases((current) => [...current, created])
      setBase({ name: '', store_id: '' })
    } catch (cause) { setError(getApiError(cause)) }
  }

  async function toggleModel(item: AiModel) {
    try {
      const updated = await adminApi.updateAiModel(item.id, { is_active: !active(item) })
      setModels((current) => current.map((modelItem) => modelItem.id === item.id ? updated : modelItem))
    } catch (cause) { setError(getApiError(cause)) }
  }

  async function toggleBase(item: KnowledgeBase) {
    try {
      const updated = await adminApi.updateKnowledgeBase(item.id, { is_active: !active(item) })
      setBases((current) => current.map((baseItem) => baseItem.id === item.id ? updated : baseItem))
    } catch (cause) { setError(getApiError(cause)) }
  }

  return <section className="mt-8" aria-labelledby="catalog-title">
    <div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[.16em] text-blue">Configuração da plataforma</p><h2 id="catalog-title" className="mt-1 text-xl font-semibold text-navy dark:text-slate-100">Catálogos de IA</h2><p className="mt-1 text-sm text-secondary dark:text-slate-400">Cadastre os modelos e as bases de conhecimento disponíveis para a equipe.</p></div>
    {error && <p role="alert" className="mb-4 rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/70 dark:bg-red-950/30 dark:text-red-200">{error}</p>}
    <div className="grid gap-5 lg:grid-cols-2">
      <article className="rounded-container border border-border bg-white p-5 shadow-panel dark:border-dark-border dark:bg-dark-surface">
        <div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control bg-blue/10 text-blue dark:bg-blue/20 dark:text-slate-100"><Cpu size={20} /></span><div><h3 className="text-base font-semibold text-navy dark:text-slate-100">Novo modelo</h3><p className="mt-1 text-sm text-secondary dark:text-slate-400">Conecte um provedor de inteligência artificial.</p></div></div>
        <form onSubmit={createModel} className="mt-5 space-y-3">
          <label className="block text-sm font-medium text-charcoal dark:text-slate-200"><span>Provedor</span><input required placeholder="Ex.: OpenAI" aria-label="Provider" value={model.provider} onChange={(event) => setModel({ ...model, provider: event.target.value })} className="mt-1 h-10 w-full rounded-control border border-border bg-white px-3 text-sm font-normal text-charcoal placeholder:text-secondary/60 focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
          <label className="block text-sm font-medium text-charcoal dark:text-slate-200"><span>Nome exibido</span><input required placeholder="Ex.: GPT-4o" aria-label="Nome do modelo" value={model.name} onChange={(event) => setModel({ ...model, name: event.target.value })} className="mt-1 h-10 w-full rounded-control border border-border bg-white px-3 text-sm font-normal text-charcoal placeholder:text-secondary/60 focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
          <label className="block text-sm font-medium text-charcoal dark:text-slate-200"><span>Model ID</span><input required placeholder="Ex.: gpt-4o" aria-label="Model ID" value={model.model_id} onChange={(event) => setModel({ ...model, model_id: event.target.value })} className="mt-1 h-10 w-full rounded-control border border-border bg-white px-3 text-sm font-normal text-charcoal placeholder:text-secondary/60 focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
          <button type="submit" className="inline-flex h-10 items-center justify-center rounded-control bg-blue px-4 text-sm font-semibold text-white transition hover:bg-navy focus:outline-none focus:ring-2 focus:ring-blue/40 active:scale-[.98]">Cadastrar modelo</button>
        </form>
        <div className="mt-6 border-t border-border pt-4 dark:border-dark-border">
          <div className="flex items-center justify-between gap-3"><h4 className="text-sm font-semibold text-navy dark:text-slate-100">Modelos cadastrados</h4><span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-secondary dark:bg-slate-800 dark:text-slate-300">{models.length}</span></div>
          {models.length === 0 ? <p className="mt-3 rounded-control border border-dashed border-border px-3 py-4 text-sm text-secondary dark:border-dark-border dark:text-slate-400">Nenhum modelo cadastrado.</p> : <div className="mt-3 space-y-2">{models.map((item) => <article key={item.id} className="flex items-center justify-between gap-3 rounded-control border border-border bg-canvas/70 px-3 py-3 dark:border-dark-border dark:bg-dark-canvas"><div className="min-w-0"><p className="truncate text-sm font-semibold text-navy dark:text-slate-100">{item.name}</p><p className="mt-0.5 truncate text-xs text-secondary dark:text-slate-400">{item.provider} <span aria-hidden="true">·</span> {item.model_id || item.modelId || 'ID não informado'}</p></div><div className="flex shrink-0 items-center gap-2"><span className={`hidden rounded-full px-2 py-1 text-[11px] font-semibold sm:inline-flex ${active(item) ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'}`}>{active(item) ? 'Ativo' : 'Inativo'}</span><button type="button" onClick={() => void toggleModel(item)} className="text-xs font-semibold text-blue underline-offset-2 transition hover:underline dark:text-slate-200">{active(item) ? 'Desativar' : 'Ativar'}</button></div></article>)}</div>}
        </div>
      </article>

      <article className="rounded-container border border-border bg-white p-5 shadow-panel dark:border-dark-border dark:bg-dark-surface">
        <div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control bg-wine/10 text-wine dark:bg-wine/20 dark:text-slate-100"><Database size={20} /></span><div><h3 className="text-base font-semibold text-navy dark:text-slate-100">Nova base RAG</h3><p className="mt-1 text-sm text-secondary dark:text-slate-400">Adicione uma fonte para consultas contextualizadas.</p></div></div>
        <form onSubmit={createBase} className="mt-5 space-y-3">
          <label className="block text-sm font-medium text-charcoal dark:text-slate-200"><span>Nome da base</span><input required placeholder="Ex.: Reforma Tributária" aria-label="Nome da RAG" value={base.name} onChange={(event) => setBase({ ...base, name: event.target.value })} className="mt-1 h-10 w-full rounded-control border border-border bg-white px-3 text-sm font-normal text-charcoal placeholder:text-secondary/60 focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
          <label className="block text-sm font-medium text-charcoal dark:text-slate-200"><span>Google File Search Store ID</span><input required placeholder="Ex.: fileSearchStores/..." aria-label="Google File Search Store ID" value={base.store_id} onChange={(event) => setBase({ ...base, store_id: event.target.value })} className="mt-1 h-10 w-full rounded-control border border-border bg-white px-3 text-sm font-normal text-charcoal placeholder:text-secondary/60 focus:border-blue focus:outline-none dark:border-dark-border dark:bg-slate-900 dark:text-slate-100" /></label>
          <button type="submit" className="inline-flex h-10 items-center justify-center rounded-control bg-blue px-4 text-sm font-semibold text-white transition hover:bg-navy focus:outline-none focus:ring-2 focus:ring-blue/40 active:scale-[.98]">Cadastrar RAG</button>
        </form>
        <div className="mt-6 border-t border-border pt-4 dark:border-dark-border">
          <div className="flex items-center justify-between gap-3"><h4 className="text-sm font-semibold text-navy dark:text-slate-100">Bases cadastradas</h4><span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-secondary dark:bg-slate-800 dark:text-slate-300">{bases.length}</span></div>
          {bases.length === 0 ? <p className="mt-3 rounded-control border border-dashed border-border px-3 py-4 text-sm text-secondary dark:border-dark-border dark:text-slate-400">Nenhuma base cadastrada.</p> : <div className="mt-3 space-y-2">{bases.map((item) => <article key={item.id} className="flex items-center justify-between gap-3 rounded-control border border-border bg-canvas/70 px-3 py-3 dark:border-dark-border dark:bg-dark-canvas"><div className="min-w-0"><p className="truncate text-sm font-semibold text-navy dark:text-slate-100">{item.name}</p><p className="mt-0.5 truncate text-xs text-secondary dark:text-slate-400">{item.store_id || item.storeId || item.fileSearchStoreId || 'Store ID não informado'}</p></div><div className="flex shrink-0 items-center gap-2"><span className={`hidden rounded-full px-2 py-1 text-[11px] font-semibold sm:inline-flex ${active(item) ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'}`}>{active(item) ? 'Ativa' : 'Inativa'}</span><button type="button" onClick={() => void toggleBase(item)} className="text-xs font-semibold text-blue underline-offset-2 transition hover:underline dark:text-slate-200">{active(item) ? 'Desativar' : 'Ativar'}</button></div></article>)}</div>}
        </div>
      </article>
    </div>
  </section>
}
