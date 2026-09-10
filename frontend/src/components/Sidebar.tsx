import { LogIn, LogOut, MessageSquare, Moon, MoreHorizontal, PanelLeftClose, PanelLeftOpen, Plus, ShieldCheck, Sun, Trash2, X } from 'lucide-react'
import { useState } from 'react'
import logoWhite from '../../logo/logo_white.png'
import { useAuth } from '../contexts/AuthContext'
import { useChat } from '../contexts/ChatContext'
import { useTheme } from '../contexts/ThemeContext'

type SidebarProps = { open: boolean; collapsed: boolean; onClose: () => void; onToggle: () => void; onLogin: () => void; onAdmin: () => void }

export function Sidebar({ open, collapsed, onClose, onToggle, onLogin, onAdmin }: SidebarProps) {
  const { user, logout } = useAuth()
  const { chats, activeChatId, selectChat, createChat, renameChat, deleteChat } = useChat()
  const { theme, toggleTheme } = useTheme()
  const [editing, setEditing] = useState<string | null>(null)
  const [title, setTitle] = useState('')

  async function rename(id: string) {
    if (title.trim()) await renameChat(id, title.trim())
    setEditing(null)
  }

  const labelClass = collapsed ? 'md:hidden' : ''
  return <aside className={`fixed inset-y-0 left-0 z-20 flex w-[272px] shrink-0 flex-col bg-navy text-white shadow-xl transition-[width,transform] duration-200 md:static md:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'} ${collapsed ? 'md:w-[76px]' : 'md:w-[272px]'}`}>
    <div className={`flex h-16 items-center border-b border-white/10 ${collapsed ? 'md:justify-center md:px-3' : 'justify-between px-5'}`}>
      <img src={logoWhite} alt="CDM Contabilidade" className={`object-contain object-left ${collapsed ? 'h-9 w-10 md:object-cover' : 'h-11 w-[185px]'}`} />
      <div className="flex items-center gap-1">
        <button type="button" onClick={onToggle} className="hidden rounded p-2 text-white/70 hover:bg-white/10 hover:text-white md:block" title={collapsed ? 'Expandir barra lateral' : 'Recolher barra lateral'} aria-label={collapsed ? 'Expandir barra lateral' : 'Recolher barra lateral'}>{collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}</button>
        <button type="button" onClick={onClose} className="rounded p-2 text-white/70 hover:bg-white/10 md:hidden" aria-label="Fechar menu"><X size={18} /></button>
      </div>
    </div>
    <div className={`p-4 ${collapsed ? 'md:px-3' : ''}`}><button type="button" onClick={() => { void createChat(); onClose() }} className={`flex w-full items-center justify-center gap-2 rounded-control bg-wine px-4 py-3 text-sm font-medium text-white transition hover:bg-wine-soft ${collapsed ? 'md:px-2' : ''}`} title="Nova Consulta" aria-label="Nova Consulta"><Plus size={17} /><span className={labelClass}>Nova Consulta</span></button></div>
    <nav aria-label="Conversas" className={`min-h-0 flex-1 overflow-y-auto px-3 ${collapsed ? 'md:px-2' : ''}`}>
      <p className={`px-2 pb-2 text-xs font-medium uppercase tracking-[.15em] text-white/45 ${labelClass}`}>Conversas</p>
      {chats.length === 0 && <p className={`px-2 py-4 text-sm text-white/55 ${labelClass}`}>Suas conversas aparecerão aqui.</p>}
      {chats.map((chat) => <div key={chat.id} className={`group mb-1 flex items-center gap-1 rounded-control ${activeChatId === chat.id ? 'bg-white/12' : 'hover:bg-white/8'}`}>
        <button type="button" onClick={() => { void selectChat(chat.id); onClose() }} className={`flex min-w-0 flex-1 items-center gap-2 px-2.5 py-2.5 text-left text-sm ${collapsed ? 'md:justify-center md:px-1' : ''}`} title={collapsed ? chat.title : undefined}>
          <MessageSquare size={15} className="shrink-0 text-white/55" />
          {editing === chat.id ? <input autoFocus value={title} onChange={(event) => setTitle(event.target.value)} onBlur={() => void rename(chat.id)} onKeyDown={(event) => { if (event.key === 'Enter') void rename(chat.id); if (event.key === 'Escape') setEditing(null) }} className={`min-w-0 flex-1 rounded bg-white/10 px-1 text-white outline-none ${labelClass}`} aria-label="Renomear conversa" /> : <span className={`truncate ${labelClass}`}>{chat.title}</span>}
        </button>
        <div className={`hidden items-center gap-0.5 group-hover:flex ${collapsed ? 'md:hidden' : ''}`}><button type="button" onClick={() => { setEditing(chat.id); setTitle(chat.title) }} className="rounded p-1.5 text-white/45 hover:bg-white/10 hover:text-white" aria-label={`Renomear ${chat.title}`}><MoreHorizontal size={16} /></button><button type="button" onClick={() => { if (window.confirm('Excluir esta conversa?')) void deleteChat(chat.id) }} className="rounded p-1.5 text-white/45 hover:bg-white/10 hover:text-white" aria-label={`Excluir ${chat.title}`}><Trash2 size={14} /></button></div>
      </div>)}
    </nav>
    <footer className={`border-t border-white/10 p-4 ${collapsed ? 'md:px-3' : ''}`}>
      <button type="button" onClick={toggleTheme} className={`mb-3 flex w-full items-center gap-2 rounded-control px-3 py-2 text-sm text-white/75 hover:bg-white/10 hover:text-white ${collapsed ? 'md:justify-center md:px-2' : ''}`} title={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'} aria-label={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'}>{theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}<span className={labelClass}>{theme === 'dark' ? 'Tema claro' : 'Tema escuro'}</span></button>
      {user?.role === 'admin' && <button type="button" onClick={() => { onAdmin(); onClose() }} className={`mb-3 flex w-full items-center gap-2 rounded-control px-3 py-2 text-sm text-white/75 hover:bg-white/10 hover:text-white ${collapsed ? 'md:justify-center md:px-2' : ''}`} title="Administração" aria-label="Administração"><ShieldCheck size={17} /><span className={labelClass}>Administração</span></button>}
      {user ? <div className={`flex items-center gap-2 ${collapsed ? 'md:justify-center' : 'justify-between'}`}><div className={`min-w-0 ${labelClass}`}><p className="truncate text-sm font-medium">{user.name}</p><p className="truncate text-xs text-white/55">{user.email}</p></div><button type="button" onClick={() => void logout()} className="rounded p-2 text-white/60 hover:bg-white/10 hover:text-white" aria-label="Sair" title="Sair"><LogOut size={17} /></button></div> : <button type="button" onClick={onLogin} className={`flex w-full items-center justify-center gap-2 rounded-control border border-white/20 px-3 py-2.5 text-sm text-white/85 hover:bg-white/10 ${collapsed ? 'md:px-2' : ''}`} title="Entrar" aria-label="Entrar"><LogIn size={17} /><span className={labelClass}>Entrar</span></button>}
    </footer>
  </aside>
}
