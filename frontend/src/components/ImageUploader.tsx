import { ImagePlus, X } from 'lucide-react'
import { useRef, useState, type ChangeEvent } from 'react'
import type { ImageAttachment } from '../types'

const MAX_ITEMS = 4
const MAX_FILE_SIZE = 5 * 1024 * 1024
const MAX_TOTAL_SIZE = 8 * 1024 * 1024
const ACCEPTED = ['image/png', 'image/jpeg']

async function readImage(file: File): Promise<ImageAttachment> {
  if (!ACCEPTED.includes(file.type)) throw new Error(`${file.name}: escolha um arquivo PNG ou JPEG.`)
  if (file.size > MAX_FILE_SIZE) throw new Error(`${file.name}: o arquivo deve ter até 5 MB.`)
  const source = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result))
    reader.onerror = () => reject(new Error(`${file.name}: não foi possível ler o arquivo.`))
    reader.readAsDataURL(file)
  })
  const image = await new Promise<HTMLImageElement>((resolve, reject) => {
    const element = new Image()
    element.onload = () => resolve(element)
    element.onerror = () => reject(new Error(`${file.name}: o arquivo é inválido.`))
    element.src = source
  })
  const scale = Math.min(1, 1920 / Math.max(image.width, image.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(image.width * scale))
  canvas.height = Math.max(1, Math.round(image.height * scale))
  canvas.getContext('2d')?.drawImage(image, 0, 0, canvas.width, canvas.height)
  const dataUrl = file.size > 1_500_000 || scale < 1 ? canvas.toDataURL('image/jpeg', .82) : source
  return { dataUrl, name: file.name, size: Math.round((dataUrl.length * 3) / 4), mime: dataUrl.startsWith('data:image/jpeg') ? 'image/jpeg' : 'image/png', width: canvas.width, height: canvas.height }
}

type Props = { value: ImageAttachment[]; onChange: (value: ImageAttachment[]) => void; disabled?: boolean }

export function ImageUploader({ value, onChange, disabled = false }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  const canAdd = value.length < MAX_ITEMS

  async function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || [])
    if (!files.length) return
    event.target.value = ''
    const room = MAX_ITEMS - value.length
    const selected = files.slice(0, room)
    const messages = files.length > room ? [`Você pode anexar no máximo ${MAX_ITEMS} arquivos.`] : []
    const processed: ImageAttachment[] = []
    for (const file of selected) {
      try { processed.push(await readImage(file)) } catch (cause) { messages.push(cause instanceof Error ? cause.message : `${file.name}: arquivo inválido.`) }
    }
    const total = value.reduce((sum, item) => sum + item.size, 0) + processed.reduce((sum, item) => sum + item.size, 0)
    if (total > MAX_TOTAL_SIZE) messages.push('O tamanho total dos arquivos, após o processamento, deve ser de até 8 MB.')
    setError(messages.length ? messages.join(' ') : null)
    if (processed.length && total <= MAX_TOTAL_SIZE) onChange([...value, ...processed])
  }

  return <div className="flex min-w-0 flex-wrap items-center gap-1.5">
    <input ref={inputRef} id="chat-image-input" type="file" accept="image/png,image/jpeg" multiple onChange={onFileChange} disabled={disabled || !canAdd} className="sr-only" aria-label="Selecionar arquivos PNG ou JPEG" />
    {value.length > 0 && <div className="flex min-w-0 max-w-full flex-wrap gap-1.5" aria-label={`${value.length} ${value.length === 1 ? 'anexo' : 'anexos'}`}>
      {value.map((item, index) => <div key={`${item.name}-${index}`} className="group relative rounded-control border border-wine/20 bg-wine/[.04] p-1 dark:border-wine-soft/30 dark:bg-wine/10">
        <img src={item.dataUrl} alt={`Prévia ${index + 1}: ${item.name}`} className="h-9 w-9 rounded object-cover sm:h-10 sm:w-10" />
        <button type="button" onClick={() => onChange(value.filter((_, itemIndex) => itemIndex !== index))} disabled={disabled} className="absolute -right-1.5 -top-1.5 rounded-full bg-wine p-0.5 text-white shadow focus:outline-none focus:ring-2 focus:ring-blue/50 disabled:opacity-50" aria-label={`Remover ${item.name}`}><X size={12} /></button>
      </div>)}
    </div>}
    {canAdd && <label htmlFor="chat-image-input" className={`inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-control px-2 text-xs font-medium text-secondary transition hover:bg-slate-100 focus-within:ring-2 focus-within:ring-blue/40 dark:text-slate-300 dark:hover:bg-white/10 ${disabled ? 'pointer-events-none opacity-50' : ''}`}><ImagePlus size={16} aria-hidden="true" />{value.length ? 'Adicionar' : 'Anexar arquivos'}</label>}
    {error && <span role="alert" className="basis-full text-[11px] text-red-700 dark:text-red-300">{error}</span>}
  </div>
}
