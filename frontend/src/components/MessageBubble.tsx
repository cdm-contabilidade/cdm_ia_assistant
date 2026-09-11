import { Check, Copy, UserRound } from 'lucide-react'
import { useState } from 'react'
import type { Message, SourceCitation } from '../types'
import { MarkdownRenderer } from './MarkdownRenderer'
import { RagTag } from './RagTag'

function safeSourceUri(uri: string | null | undefined): string | null {
  if (!uri) return null
  try { const url = new URL(uri); return url.protocol === 'http:' || url.protocol === 'https:' ? uri : null } catch { return null }
}

function Sources({ sources }: { sources: SourceCitation[] }) {
  if (!sources.length) return null
  return <section className="mt-4 border-t border-border pt-3 dark:border-dark-border" aria-label="Fontes consultadas"><h3 className="text-xs font-semibold uppercase tracking-wide text-secondary dark:text-slate-400">Fontes consultadas</h3><ul className="mt-2 space-y-1 text-sm">{sources.map((source, index) => { const uri = safeSourceUri(source.uri); return <li key={`${source.title}-${source.uri || index}`}><span className="text-charcoal dark:text-slate-200">{source.title}{source.pageNumber ? ` · p. ${source.pageNumber}` : ''}</span>{uri && <>{' '}<a href={uri} target="_blank" rel="noopener noreferrer" className="text-wine underline underline-offset-2 hover:text-wine-dark">{'Abrir fonte'}</a></>}</li> })}</ul></section>
}

function CatalogMeta({ message }: { message: Message }) {
  if (!message.modelName && !message.modelId && !message.knowledgeBaseName && !message.knowledgeBaseId) return null
  return <p className="mt-3 border-t border-border pt-2 text-xs text-secondary dark:border-dark-border dark:text-slate-400">{message.modelName || message.modelId ? `Modelo: ${message.modelName || message.modelId}` : ''}{message.knowledgeBaseName || message.knowledgeBaseId ? ` · RAG: ${message.knowledgeBaseName || message.knowledgeBaseId}` : ''}</p>
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  const imageUrls = message.imageUrls?.length ? message.imageUrls : (message.imageUrl ? [message.imageUrl] : [])
  const [copied, setCopied] = useState(false)

  async function copyResponse() {
    try {
      if (!navigator.clipboard?.writeText) return
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  return <article className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`} aria-label={isUser ? 'Sua mensagem' : 'Resposta do assistente'}><div className={`max-w-[min(768px,88%)] rounded-container border px-5 py-4 shadow-sm ${isUser ? 'border-wine/20 bg-[#FBF1F0] dark:border-wine-soft/40 dark:bg-[#351F29]' : 'border-border bg-white dark:border-dark-border dark:bg-dark-surface'}`}><RagTag label={message.knowledgeBaseName || message.knowledgeBaseId || undefined} className="mb-3" />{imageUrls.length > 0 && <div className="mb-3 grid max-w-full grid-cols-2 gap-1.5 sm:grid-cols-4" aria-label={`${imageUrls.length} ${imageUrls.length === 1 ? 'imagem anexada' : 'imagens anexadas'}`}>{imageUrls.slice(0, 4).map((url, index) => <img key={`${url}-${index}`} src={url} alt={`Imagem anexada ${index + 1}`} className="aspect-square max-h-36 w-full rounded-control object-cover" onError={(event) => { event.currentTarget.style.display = 'none' }} />)}</div>}{isUser ? <p className="whitespace-pre-wrap text-[15px] leading-7 text-charcoal dark:text-slate-100">{message.content}</p> : <MarkdownRenderer content={message.content} />}{!isUser && <Sources sources={message.sources || []} />}<CatalogMeta message={message} />{!isUser && <div className="mt-3 flex justify-end"><button type="button" onClick={() => void copyResponse()} className="inline-flex items-center gap-1.5 rounded-control border border-border px-2 py-1 text-xs font-medium text-secondary transition hover:border-blue hover:text-navy focus:outline-none focus:ring-2 focus:ring-blue/40 dark:border-dark-border dark:text-slate-300 dark:hover:text-slate-100" aria-label={copied ? 'Resposta copiada' : 'Copiar resposta'} title={copied ? 'Resposta copiada' : 'Copiar resposta'}>{copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}{copied ? 'Copiado' : 'Copiar resposta'}</button></div>}<time className="mt-2 block text-right text-xs text-secondary dark:text-slate-400 tabular" dateTime={message.created_at}>{new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' }).format(new Date(message.created_at))}</time></div>{isUser && <span className="mt-2 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-wine text-white" aria-hidden="true"><UserRound size={16} /></span>}</article>
}
