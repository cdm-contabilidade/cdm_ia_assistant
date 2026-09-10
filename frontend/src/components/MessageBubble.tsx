import { UserRound } from 'lucide-react'
import type { Message, SourceCitation } from '../types'
import { MarkdownRenderer } from './MarkdownRenderer'

function safeSourceUri(uri: string | null | undefined): string | null {
  if (!uri) return null
  try {
    const url = new URL(uri)
    return url.protocol === 'http:' || url.protocol === 'https:' ? uri : null
  } catch {
    return null
  }
}

function Sources({ sources }: { sources: SourceCitation[] }) {
  if (!sources.length) return null
  return <section className="mt-4 border-t border-border pt-3 dark:border-dark-border" aria-label="Fontes consultadas"><h3 className="text-xs font-semibold uppercase tracking-wide text-secondary dark:text-slate-400">Fontes consultadas</h3><ul className="mt-2 space-y-1 text-sm">{sources.map((source, index) => { const uri = safeSourceUri(source.uri); return <li key={`${source.title}-${source.uri || index}`}><span className="text-charcoal dark:text-slate-200">{source.title}{source.pageNumber ? ` · p. ${source.pageNumber}` : ''}</span>{uri && <>{' '}<a href={uri} target="_blank" rel="noopener noreferrer" className="text-wine underline underline-offset-2 hover:text-wine-dark">{'Abrir fonte'}</a></>}</li> })}</ul></section>
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return <article className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`} aria-label={isUser ? 'Sua mensagem' : 'Resposta do assistente'}><div className={`max-w-[min(768px,88%)] rounded-container border px-5 py-4 shadow-sm ${isUser ? 'border-wine/20 bg-[#FBF1F0] dark:border-wine-soft/40 dark:bg-[#351F29]' : 'border-border bg-white dark:border-dark-border dark:bg-dark-surface'}`}>{message.imageUrl && <img src={message.imageUrl} alt="Imagem anexada à mensagem" className="mb-3 max-h-56 max-w-full rounded-control object-contain" onError={(event) => { event.currentTarget.style.display = 'none' }} />}{isUser ? <p className="whitespace-pre-wrap text-[15px] leading-7 text-charcoal dark:text-slate-100">{message.content}</p> : <MarkdownRenderer content={message.content} />}{!isUser && <Sources sources={message.sources || []} />}<time className="mt-2 block text-right text-xs text-secondary dark:text-slate-400 tabular" dateTime={message.created_at}>{new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' }).format(new Date(message.created_at))}</time></div>{isUser && <span className="mt-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-wine text-white" aria-hidden="true"><UserRound size={16} /></span>}</article>
}
