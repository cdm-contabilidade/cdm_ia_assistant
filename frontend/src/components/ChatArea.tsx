import { Bot, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useChat } from '../contexts/ChatContext'
import { InputBox } from './InputBox'
import { MessageBubble } from './MessageBubble'

export function ThinkingIndicator() {
  return <div className="flex justify-start" role="status" aria-label="O assistente está pensando"><div className="rounded-container border border-border bg-white px-5 py-4 shadow-sm dark:border-dark-border dark:bg-dark-surface"><span className="sr-only">O assistente está pensando</span><span className="thinking-dots" aria-hidden="true"><span className="thinking-dot" /><span className="thinking-dot" /><span className="thinking-dot" /></span></div></div>
}

export function ChatArea() {
  const { messages, status, error, isSending, catalogsLoading, sendMessage, aiModels, modelId, knowledgeBaseId, setModelId } = useChat()
  const wasNearBottom = useRef(true)
  const scrollRef = useRef<HTMLElement>(null)
  const composerRef = useRef<HTMLDivElement>(null)
  const [composerCollapsed, setComposerCollapsed] = useState(false)

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'auto') => {
    const node = scrollRef.current
    if (!node) return
    node.scrollTo({ top: node.scrollHeight, behavior })
  }, [])

  useEffect(() => {
    if (!wasNearBottom.current) return
    const frame = requestAnimationFrame(() => scrollToBottom('smooth'))
    return () => cancelAnimationFrame(frame)
  }, [messages.length, scrollToBottom])

  // Sending clears/resizes the composer while the panel is being laid out. Keep
  // the panel anchored only when the user was already reading its end.
  useEffect(() => {
    const composer = composerRef.current
    if (!composer || typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(() => {
      if (wasNearBottom.current) scrollToBottom()
    })
    observer.observe(composer)
    return () => observer.disconnect()
  }, [scrollToBottom])

  function trackScroll() {
    const node = scrollRef.current
    if (!node) return
    wasNearBottom.current = node.scrollHeight - node.scrollTop - node.clientHeight < 120
  }

  return (
    <main className="flex min-h-0 min-w-0 flex-1 flex-col bg-canvas dark:bg-dark-canvas">
      <section ref={scrollRef} onScroll={trackScroll} className="chat-scroll-panel flex-1 overflow-y-auto px-3 py-4 md:px-6 md:py-6">
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
          {status === 'loading' && <div className="rounded-container border border-border bg-white p-4 text-center text-secondary dark:border-dark-border dark:bg-dark-surface dark:text-slate-300">Carregando conversas...</div>}
          {status === 'ready' && messages.length === 0 && <div className="flex min-h-[32vh] flex-col items-center justify-center text-center"><span className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-wine text-white"><Bot size={28} /></span><h2 className="text-2xl font-semibold text-navy dark:text-slate-100">Como posso ajudar na sua contabilidade?</h2><p className="mt-2 max-w-md text-secondary dark:text-slate-300">Tire dúvidas sobre tributos, folha de pagamento, obrigações acessórias e rotinas contábeis. Você também pode anexar uma imagem para compartilhar mais contexto.</p></div>}
          {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
          {isSending && <ThinkingIndicator />}
          {error && <div role="alert" className="flex items-center justify-between gap-3 rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/70 dark:bg-red-950/40 dark:text-red-200"><span>{error}</span><button type="button" onClick={() => window.location.reload()} className="inline-flex items-center gap-1 font-medium underline transition hover:no-underline focus:outline-none focus:ring-2 focus:ring-red-500/50 active:scale-[.98]"><RefreshCw size={14} />Tentar novamente</button></div>}
        </div>
      </section>
      <div ref={composerRef} className="shrink-0 border-t border-border bg-canvas px-3 pb-3 pt-2 dark:border-dark-border dark:bg-dark-canvas md:px-6 md:pb-4">
        <div className={`mx-auto flex w-full max-w-5xl items-end gap-2 ${composerCollapsed ? 'justify-end' : ''}`}>
          {!composerCollapsed && <div className="min-w-0 flex-1"><InputBox disabled={isSending || status !== 'ready'} catalogsLoading={catalogsLoading} onSend={sendMessage} aiModels={aiModels} modelId={modelId} knowledgeBaseId={knowledgeBaseId} onModelChange={setModelId} /></div>}
          <button type="button" onClick={() => setComposerCollapsed((collapsed) => !collapsed)} className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-control border border-border bg-white text-secondary shadow-sm transition hover:border-blue/60 hover:text-navy focus:outline-none focus:ring-2 focus:ring-blue/40 dark:border-dark-border dark:bg-dark-surface dark:text-slate-300 dark:hover:text-white" aria-label={composerCollapsed ? 'Expandir área de entrada' : 'Recolher área de entrada'} title={composerCollapsed ? 'Expandir área de entrada' : 'Recolher área de entrada'}>
            {composerCollapsed ? <ChevronUp size={18} aria-hidden="true" /> : <ChevronDown size={18} aria-hidden="true" />}
          </button>
        </div>
      </div>
    </main>
  )
}
