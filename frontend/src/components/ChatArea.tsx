import { Bot, RefreshCw } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { useChat } from '../contexts/ChatContext'
import { InputBox } from './InputBox'
import { MessageBubble } from './MessageBubble'

export function ChatArea() {
  const { messages, status, error, isSending, catalogsLoading, sendMessage, aiModels, modelId, knowledgeBaseId, setModelId } = useChat()
  const endRef = useRef<HTMLDivElement>(null)
  const wasNearBottom = useRef(true)
  const scrollRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (wasNearBottom.current) endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  function trackScroll() {
    const node = scrollRef.current
    if (!node) return
    wasNearBottom.current = node.scrollHeight - node.scrollTop - node.clientHeight < 120
  }

  return (
    <main className="flex min-h-0 min-w-0 flex-1 flex-col bg-canvas dark:bg-dark-canvas">
      <section ref={scrollRef} onScroll={trackScroll} className="flex-1 overflow-y-auto px-4 py-6 md:px-10 md:py-10">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-5">
          {status === 'loading' && <div className="rounded-container border border-border bg-white p-6 text-center text-secondary dark:border-dark-border dark:bg-dark-surface dark:text-slate-300">Carregando conversas...</div>}
          {status === 'ready' && messages.length === 0 && <div className="flex min-h-[45vh] flex-col items-center justify-center text-center"><span className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-wine text-white"><Bot size={30} /></span><h2 className="text-2xl font-semibold text-navy dark:text-slate-100">Como posso ajudar na sua contabilidade?</h2><p className="mt-2 max-w-md text-secondary dark:text-slate-300">Tire dúvidas sobre tributos, folha de pagamento, obrigações acessórias e rotinas contábeis. Você também pode anexar uma imagem para compartilhar mais contexto.</p></div>}
          {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
          {isSending && <div className="rounded-container border border-border bg-white px-5 py-4 text-sm text-secondary dark:border-dark-border dark:bg-dark-surface dark:text-slate-300">Consultando a base de conhecimento...</div>}
          {error && <div role="alert" className="flex items-center justify-between gap-3 rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/70 dark:bg-red-950/40 dark:text-red-200"><span>{error}</span><button type="button" onClick={() => window.location.reload()} className="inline-flex items-center gap-1 font-medium underline transition hover:no-underline focus:outline-none focus:ring-2 focus:ring-red-500/50 active:scale-[.98]"><RefreshCw size={14} />Tentar novamente</button></div>}
          <div ref={endRef} />
        </div>
      </section>
      <div className="shrink-0 border-t border-border bg-canvas px-4 pb-5 pt-4 dark:border-dark-border dark:bg-dark-canvas md:px-10 md:pb-6">
        <div className="mx-auto max-w-3xl"><InputBox disabled={isSending || status !== 'ready'} catalogsLoading={catalogsLoading} onSend={sendMessage} aiModels={aiModels} modelId={modelId} knowledgeBaseId={knowledgeBaseId} onModelChange={setModelId} /></div>
      </div>
    </main>
  )
}
