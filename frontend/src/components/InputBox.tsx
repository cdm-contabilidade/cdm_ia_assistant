import { Send } from 'lucide-react'
import { useLayoutEffect, useRef, useState } from 'react'
import type { AiModel, ImageAttachment, KnowledgeBase } from '../types'
import { ImageUploader } from './ImageUploader'

type Props = { disabled: boolean; catalogsLoading?: boolean; onSend: (text: string, images: ImageAttachment[] | null) => Promise<void>; aiModels?: AiModel[]; modelId?: string; knowledgeBaseId?: string; onModelChange?: (id: string) => void }

export function InputBox({ disabled, catalogsLoading = false, onSend, aiModels = [], modelId = '', knowledgeBaseId = '', onModelChange = () => {} }: Props) {
  const [text, setText] = useState('')
  const [images, setImages] = useState<ImageAttachment[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const selectableModels = aiModels.filter((item) => item.provider.toLowerCase() === (knowledgeBaseId ? 'gemini' : 'openai'))
  const modelUnavailable = !catalogsLoading && (!selectableModels.length || !modelId)

  useLayoutEffect(() => {
    const node = textareaRef.current
    if (!node) return
    node.style.height = 'auto'
    node.style.height = `${Math.min(node.scrollHeight, 144)}px`
  }, [text])

  async function send() {
    if (!text.trim() || disabled || modelUnavailable) return
    const currentText = text
    const currentImages = images
    setText('')
    setImages([])
    try { await onSend(currentText, currentImages.length ? currentImages : null) } catch { setText(currentText); setImages(currentImages) }
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void send() }
  }

  return (
    <div className="rounded-container border border-border/90 bg-white/95 p-2.5 shadow-panel transition focus-within:border-blue/60 dark:border-dark-border dark:bg-dark-surface/95 sm:p-3">
      <div className="grid min-w-0 gap-2.5 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] md:gap-3">
        <textarea ref={textareaRef} value={text} onChange={(event) => setText(event.target.value)} onKeyDown={onKeyDown} disabled={disabled} rows={2} maxLength={10000} placeholder="Digite sua dúvida contábil..." aria-label="Mensagem" className="max-h-28 min-h-20 w-full resize-none border-0 bg-transparent px-1 py-1 text-[15px] leading-6 text-charcoal placeholder:text-secondary/70 focus:outline-none dark:text-slate-100 dark:placeholder:text-slate-400 disabled:cursor-not-allowed disabled:opacity-60 md:min-h-24" />

        <div className="flex min-w-0 flex-col gap-1.5 border-t border-border/70 pt-2.5 dark:border-dark-border/70 md:border-l md:border-t-0 md:pl-3 md:pt-0">
          <div className="min-w-0">
            <ImageUploader value={images} onChange={setImages} disabled={disabled} />
          </div>
          <div className="min-w-0">
          <label className="block min-w-0 text-[11px] font-medium text-secondary dark:text-slate-400">
            Modelo
            <select aria-label="Modelo" value={modelId} onChange={(event) => onModelChange(event.target.value)} disabled={catalogsLoading || !selectableModels.length} aria-describedby="rag-help" className="mt-0.5 h-8 w-full min-w-0 rounded-control border border-border bg-transparent px-2 text-xs text-charcoal outline-none transition hover:border-blue/60 focus:border-blue focus:ring-2 focus:ring-blue/20 dark:border-dark-border dark:bg-slate-900 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50">
              <option value="">{knowledgeBaseId ? selectableModels.length ? 'Selecione um modelo Gemini' : 'Nenhum modelo Gemini disponível' : selectableModels.length ? 'Selecione um modelo OpenAI' : 'Nenhum modelo OpenAI disponível'}</option>
              {selectableModels.map((item) => <option key={item.id} value={item.id}>{item.displayName || item.name} · {item.provider}</option>)}
            </select>
          </label>
          </div>
          <button type="button" onClick={() => void send()} disabled={disabled || !text.trim() || modelUnavailable} className="inline-flex h-8 w-full shrink-0 items-center justify-center gap-1.5 rounded-control bg-wine px-3 text-xs font-semibold text-white shadow-sm transition hover:bg-wine/90 focus:outline-none focus:ring-2 focus:ring-wine/40 active:scale-[.98] disabled:cursor-not-allowed disabled:opacity-40" aria-label="Enviar mensagem">
            <Send size={14} aria-hidden="true" /> Enviar
          </button>
          <p id="rag-help" className="pl-1 text-[10px] leading-4 text-secondary/75 dark:text-slate-400">{modelUnavailable ? (knowledgeBaseId ? 'Não há modelo Gemini ativo para este Store. O envio está indisponível.' : 'Selecione um modelo ativo para enviar.') : knowledgeBaseId ? 'RAG selecionado: escolha um modelo Gemini ativo para este Store.' : 'Sem RAG: selecione um modelo OpenAI para pesquisar fontes atuais na web.'}</p>
        </div>
      </div>
    </div>
  )
}
