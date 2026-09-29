import { Check, ChevronLeft, ChevronRight, CircleOff, Database, MessageSquare, MoreHorizontal, Plus, ShieldCheck, Star, Trash2, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import logoWhite from '../../logo/logo_white.png'
import { ConfirmDeleteModal } from './ConfirmDeleteModal'
import { useAuth } from '../contexts/AuthContext'
import { useChat } from '../contexts/ChatContext'
import { getApiError } from '../services/api'
import type { ToastData } from './Toast'

type SidebarProps = { open: boolean; collapsed: boolean; onClose: () => void; onToggle: () => void; onAdmin: () => void; onNotify: (toast: ToastData) => void }

export function Sidebar({ open, collapsed, onClose, onToggle, onAdmin, onNotify }: SidebarProps) {
  const { user } = useAuth()
  const { chats, activeChatId, selectChat, createChat, renameChat, deleteChat, catalogsLoading, knowledgeBases, knowledgeBaseId, setKnowledgeBaseId } = useChat()
  const [editing, setEditing] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [menuChatId, setMenuChatId] = useState<string | null>(null)
  const [savingTitle, setSavingTitle] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const labelClass = collapsed ? 'md:hidden' : ''
  const orderedKnowledgeBases = [...knowledgeBases].sort((left, right) => Number(right.featured === true) - Number(left.featured === true))

  useEffect(() => {
    if (!menuChatId) return
    const close = (event: KeyboardEvent) => { if (event.key === 'Escape') setMenuChatId(null) }
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [menuChatId])

  function startRename(id: string, currentTitle: string) { setMenuChatId(null); setEditing(id); setTitle(currentTitle) }
  async function rename(id: string) {
    const nextTitle = title.trim()
    if (!nextTitle || savingTitle) return
    setSavingTitle(true)
    try { await renameChat(id, nextTitle); setEditing(null) }
    catch (cause) { onNotify({ tone: 'error', message: getApiError(cause) }) }
    finally { setSavingTitle(false) }
  }
  async function confirmDelete() {
    if (!deleteTarget || deletingId) return
    setDeletingId(deleteTarget.id)
    try { await deleteChat(deleteTarget.id); setDeleteTarget(null); onNotify({ tone: 'success', message: 'Conversa excluída.' }) }
    catch (cause) { onNotify({ tone: 'error', message: getApiError(cause) }) }
    finally { setDeletingId(null) }
  }

  return <>
    <aside className={`sidebar-shell fixed inset-y-0 left-0 z-20 flex w-[272px] shrink-0 flex-col bg-navy text-white transition-[width,transform] duration-200 md:static md:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'} ${collapsed ? 'md:w-[76px]' : 'md:w-[272px]'}`}>
      <div className="sidebar-brand relative flex h-20 shrink-0 items-center justify-center px-4"><img src={logoWhite} alt="CDM Contabilidade" className={`h-12 w-[230px] object-contain ${collapsed ? 'md:h-9 md:w-10 md:object-cover' : ''}`} /><div className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center gap-1"><button type="button" onClick={onToggle} className="hidden p-2 text-white/70 transition hover:text-white focus:outline-none focus:ring-2 focus:ring-white/50 md:block" title={collapsed ? 'Expandir barra lateral' : 'Recolher barra lateral'} aria-label={collapsed ? 'Expandir barra lateral' : 'Recolher barra lateral'}>{collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}</button><button type="button" onClick={onClose} className="p-2 text-white/70 transition hover:text-white focus:outline-none focus:ring-2 focus:ring-white/50 md:hidden" title="Fechar barra lateral" aria-label="Fechar barra lateral"><X size={18} /></button></div></div>
      <div className={`p-4 pb-3 ${collapsed ? 'md:px-3' : ''}`}><button type="button" onClick={() => { void createChat(); onClose() }} className={`sidebar-new-chat flex w-full items-center justify-center gap-2 rounded-control bg-wine px-4 py-3 text-sm font-medium text-white transition hover:bg-wine-soft focus:outline-none focus:ring-2 focus:ring-white/60 active:scale-[.99] ${collapsed ? 'md:px-2' : ''}`} title="Nova Consulta" aria-label="Nova Consulta"><Plus size={17} /><span className={labelClass}>Nova Consulta</span></button></div>
      {(user?.role === 'admin' || user?.can_web_search === true) && <div className={`px-3 pb-2 ${collapsed ? 'md:px-2' : ''}`}><button type="button" onClick={() => { setKnowledgeBaseId(''); onClose() }} className={`sidebar-knowledge-item flex w-full items-center gap-2 rounded-control px-2.5 py-2 text-left text-sm transition focus:outline-none focus:ring-2 focus:ring-gold/70 ${knowledgeBaseId === '' ? 'is-active' : ''} ${collapsed ? 'md:justify-center md:px-1' : ''}`} aria-pressed={knowledgeBaseId === ''} title="Pesquisar na Web"><CircleOff size={15} className="shrink-0" aria-hidden="true" /><span className={labelClass}>Pesquisar na Web</span></button></div>}
      <section aria-labelledby="knowledge-bases-title" className={`sidebar-knowledge mx-3 mb-3 px-2.5 pb-2.5 pt-3 ${collapsed ? 'md:mx-2 md:px-1.5' : ''}`}>
        <div className={`sidebar-section-heading mb-2 flex items-center gap-2 px-1.5 ${labelClass}`}><Database size={14} className="text-white/55" /><p id="knowledge-bases-title" className="text-xs font-semibold uppercase tracking-[.14em] text-white/60">Bases de conhecimento</p></div>
        {catalogsLoading ? <p className={`px-2 py-2 text-sm text-white/55 ${labelClass}`}>Carregando bases...</p> : knowledgeBases.length === 0 ? <p className={`px-2 py-2 text-sm text-white/55 ${labelClass}`}>Nenhum RAG disponível.</p> : <div className="space-y-1">
          {orderedKnowledgeBases.map((knowledgeBase) => <button key={knowledgeBase.id} type="button" onClick={() => { setKnowledgeBaseId(knowledgeBase.id); onClose() }} className={`sidebar-knowledge-item flex w-full items-center gap-2 rounded-control px-2.5 py-2 text-left text-sm transition focus:outline-none focus:ring-2 focus:ring-gold/70 ${knowledgeBaseId === knowledgeBase.id ? 'is-active' : ''} ${collapsed ? 'md:justify-center md:px-1' : ''}`} aria-pressed={knowledgeBaseId === knowledgeBase.id} title={collapsed ? knowledgeBase.name : undefined}><Database size={15} className="shrink-0" />{knowledgeBase.featured === true && <Star size={13} className="shrink-0 fill-gold text-gold" aria-label="RAG destacado" />}<span className={`truncate ${labelClass}`}>{knowledgeBase.name}</span></button>)}
        </div>}
      </section>
      <nav aria-label="Conversas" className={`sidebar-conversations min-h-0 flex-1 overflow-y-auto px-3 pb-3 ${collapsed ? 'md:px-2' : ''}`}><div className={`sidebar-section-heading mb-2 flex items-center gap-2 px-2 ${labelClass}`}><MessageSquare size={14} className="text-white/55" /><p className="text-xs font-semibold uppercase tracking-[.14em] text-white/60">Conversas</p></div>{chats.length === 0 && <p className={`px-2 py-4 text-sm text-white/55 ${labelClass}`}>Suas conversas aparecerão aqui.</p>}
        {chats.map((chat) => { const isDeleting = deletingId === chat.id; const isActive = activeChatId === chat.id; return <div key={chat.id} className={`sidebar-chat group relative mb-1 flex items-center gap-1 rounded-control ${isActive ? 'is-active' : ''}`}>
          {editing === chat.id ? <div className="flex min-w-0 flex-1 items-center gap-1 px-2 py-1.5"><input autoFocus value={title} onChange={(event) => setTitle(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void rename(chat.id); if (event.key === 'Escape') setEditing(null) }} className="min-w-0 flex-1 rounded bg-white/10 px-2 py-1.5 text-sm text-white outline-none focus:ring-2 focus:ring-wine" aria-label="Título da conversa" disabled={savingTitle} /><button type="button" onClick={() => void rename(chat.id)} disabled={savingTitle || !title.trim()} className="rounded-control p-1.5 text-white/70 hover:bg-white/10 disabled:opacity-50" aria-label="Salvar título"><Check size={15} /></button></div> : <button type="button" onClick={() => { void selectChat(chat.id); onClose() }} className={`flex min-w-0 flex-1 items-center gap-2 rounded-control px-2.5 py-2.5 text-left text-sm focus:outline-none focus:ring-2 focus:ring-gold/70 ${collapsed ? 'md:justify-center md:px-1' : ''}`} title={collapsed ? chat.title : undefined} aria-current={isActive ? 'page' : undefined}><MessageSquare size={15} className="shrink-0 text-white/55" /><span className={`truncate ${labelClass}`}>{chat.title}</span></button>}
          <div className={`relative hidden items-center gap-0.5 group-hover:flex group-focus-within:flex ${collapsed ? 'md:hidden' : ''} ${isDeleting || menuChatId === chat.id ? '!flex' : ''}`}><button type="button" onClick={() => setMenuChatId(menuChatId === chat.id ? null : chat.id)} className="rounded-control p-1.5 text-white/45 hover:bg-white/10 hover:text-white focus:outline-none focus:ring-2 focus:ring-white/50" aria-label={`Ações para ${chat.title}`} aria-haspopup="menu" aria-expanded={menuChatId === chat.id} title="Ações da conversa"><MoreHorizontal size={16} /></button>{menuChatId === chat.id && <div role="menu" aria-label={`Ações para ${chat.title}`} className="absolute right-1 top-9 z-30 min-w-[140px] rounded-control border border-white/10 bg-navy p-1 shadow-xl"><button type="button" role="menuitem" onClick={() => startRename(chat.id, chat.title)} className="flex w-full rounded px-3 py-2 text-left text-sm text-white/85 hover:bg-white/10 focus:outline-none focus:ring-1 focus:ring-white/50">Renomear</button></div>}<button type="button" onClick={() => setDeleteTarget({ id: chat.id, title: chat.title })} disabled={Boolean(deletingId)} className="rounded-control p-1.5 text-white/45 hover:bg-white/10 hover:text-white focus:outline-none focus:ring-2 focus:ring-white/50 disabled:opacity-50" aria-label={`Excluir ${chat.title}`} title={`Excluir ${chat.title}`} aria-busy={isDeleting}><Trash2 size={14} /></button></div>
        </div> })}
      </nav>
      {user?.role === 'admin' && <footer className={`sidebar-footer border-t border-white/10 p-4 pt-3 ${collapsed ? 'md:px-3' : ''}`}><button type="button" onClick={() => { onAdmin(); onClose() }} className={`flex w-full items-center gap-2 rounded-control px-3 py-2 text-sm text-white/75 transition hover:bg-white/10 hover:text-white focus:outline-none focus:ring-2 focus:ring-white/50 ${collapsed ? 'md:justify-center md:px-2' : ''}`} aria-label="Administração"><ShieldCheck size={17} /><span className={labelClass}>Administração</span></button></footer>}
    </aside>{deleteTarget && <ConfirmDeleteModal chatTitle={deleteTarget.title} busy={Boolean(deletingId)} onCancel={() => setDeleteTarget(null)} onConfirm={() => void confirmDelete()} />}
  </>
}
