import { ChevronLeft, ChevronRight, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

type ImageViewerModalProps = {
  images: string[]
  initialIndex: number
  onClose: () => void
}

export function ImageViewerModal({ images, initialIndex, onClose }: ImageViewerModalProps) {
  const [index, setIndex] = useState(initialIndex)
  const closeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    closeRef.current?.focus()
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') { onClose(); return }
      if (images.length < 2) return
      if (event.key === 'ArrowLeft') setIndex((current) => (current - 1 + images.length) % images.length)
      if (event.key === 'ArrowRight') setIndex((current) => (current + 1) % images.length)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose, images.length])

  function handleBackdropMouseDown(event: React.MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget) onClose()
  }

  return <div className="fixed inset-0 z-40 flex items-center justify-center bg-navy/70 p-4 dark:bg-black/80" role="presentation" onMouseDown={handleBackdropMouseDown}>
    <section role="dialog" aria-modal="true" aria-label="Visualizador de imagem" className="flex max-h-full max-w-full flex-col items-center gap-3">
      <div className="flex w-full items-center justify-between gap-3">
        {images.length > 1 && <p aria-live="polite" className="text-sm text-slate-200">{index + 1} de {images.length}</p>}
        <button ref={closeRef} type="button" onClick={onClose} aria-label="Fechar visualizador" className="flex h-10 w-10 items-center justify-center rounded-control border border-white/30 text-white transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-blue/50">
          <X size={20} aria-hidden="true" />
        </button>
      </div>
      <img src={images[index]} alt={`Imagem anexada ${index + 1}`} className="max-h-[80vh] w-auto max-w-full rounded-control object-contain" />
      {images.length > 1 && <div className="flex items-center gap-3">
        <button type="button" onClick={() => setIndex((current) => (current - 1 + images.length) % images.length)} aria-label="Imagem anterior" className="flex h-10 w-10 items-center justify-center rounded-control border border-white/30 text-white transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-blue/50">
          <ChevronLeft size={20} aria-hidden="true" />
        </button>
        <button type="button" onClick={() => setIndex((current) => (current + 1) % images.length)} aria-label="Próxima imagem" className="flex h-10 w-10 items-center justify-center rounded-control border border-white/30 text-white transition hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-blue/50">
          <ChevronRight size={20} aria-hidden="true" />
        </button>
      </div>}
    </section>
  </div>
}
