import { Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { AiModel, ImageAttachment, KnowledgeBase } from '../types'
import { ImageUploader } from './ImageUploader'

type Props = { disabled: boolean; catalogsLoading?: boolean; onSend: (text: string, image: ImageAttachment | null) => Promise<void>; aiModels?: AiModel[]; modelId?: string; knowledgeBaseId?: string; onModelChange?: (id: string) => void }

export function InputBox({ disabled, catalogsLoading = false, onSend, aiModels = [], modelId = '', knowledgeBaseId = '', onModelChange = () => {} }: Props) {
  const [text, setText] = useState('')
  const [image, setImage] = useState<ImageAttachment | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const node = textareaRef.current
    if (!node) return
    node.style.height = 'auto'
    node.style.height = `${Math.min(node.scrollHeight, 144)}px`
  }, [text])

  async function send() {
    if (!text.trim() || disabled) return
    const currentText = text
    const currentImage = image
    setText('')
    setImage(null)
    try { await onSend(currentText, currentImage) } catch { setText(currentText); setImage(currentImage) }
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void send() }
  }

  return (
    <div className="rounded-container border border-border/90 bg-white/95 p-3 shadow-panel transition focus-within:border-blue/60 dark:border-dark-border dark:bg-dark-surface/95 sm:p-3.5">
      <textarea ref={textareaRef} value={text} onChange={(event) => setText(event.target.value)} onKeyDown={onKeyDown} disabled={disabled} rows={1} maxLength={10000} placeholder="Digite sua dúvida contábil..." aria-label="Mensagem" className="max-h-36 min-h-10 w-full resize-none border-0 bg-transparent px-1 py-1.5 text-[15px] leading-6 text-charcoal placeholder:text-secondary/70 focus:outline-none dark:text-slate-100 dark:placeholder:text-slate-400 disabled:cursor-not-allowed disabled:opacity-60" />

      <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-border/70 pt-2 dark:border-dark-border/70">
        <ImageUploader value={image} onChange={setImage} disabled={disabled} />
        <span className="hidden h-4 w-px bg-border sm:block dark:bg-dark-border" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <label className="min-w-0 text-[11px] font-medium text-secondary dark:text-slate-400">
            Modelo
            <select aria-label="Modelo" value={modelId} onChange={(event) => onModelChange(event.target.value)} disabled={catalogsLoading || !aiModels.length || Boolean(knowledgeBaseId)} aria-describedby="rag-help" className="mt-0.5 h-8 w-full min-w-0 rounded-control border border-border bg-transparent px-2 text-xs text-charcoal outline-none transition hover:border-blue/60 focus:border-blue focus:ring-2 focus:ring-blue/20 dark:border-dark-border dark:bg-slate-900 dark:text-slate-100 disabled:cursor-not-allowed disabled:opacity-50">
              <option value="">{knowledgeBaseId ? 'Gemini obrigatório com RAG' : aiModels.length ? 'Padrão do sistema' : 'Entre para escolher um modelo'}</option>
              {aiModels.map((item) => <option key={item.id} value={item.id}>{item.displayName || item.name} · {item.provider}</option>)}
            </select>
          </label>
        </div>
        <button type="button" onClick={() => void send()} disabled={disabled || !text.trim()} className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-control bg-wine px-3 text-xs font-semibold text-white shadow-sm transition hover:bg-wine/90 focus:outline-none focus:ring-2 focus:ring-wine/40 active:scale-[.98] disabled:cursor-not-allowed disabled:opacity-40" aria-label="Enviar mensagem">
          <Send size={14} aria-hidden="true" /> <span className="hidden sm:inline">Enviar</span>
        </button>
      </div>
      <p id="rag-help" className="mt-1.5 pl-1 text-[10px] text-secondary/75 dark:text-slate-400">{knowledgeBaseId ? 'RAG selecionado na barra lateral. O modelo Gemini será usado.' : 'Selecione um RAG na barra lateral para consultar uma base.'}</p>
    </div>
  )
}
