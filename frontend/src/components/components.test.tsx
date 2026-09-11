import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { AdminPanel } from './AdminPanel'
import { InputBox } from './InputBox'
import { MessageBubble } from './MessageBubble'
import { MarkdownRenderer } from './MarkdownRenderer'
import { adminApi } from '../services/api'

describe('chat surface behavior', () => {
  it('renders GFM tables and code blocks', () => {
    render(<MarkdownRenderer content={'| Campo | Valor |\n| --- | --- |\n| status | ok |\n\n```ts\nconst answer = true\n```'} />)
    expect(screen.getByText('status')).toBeInTheDocument()
    expect(screen.getByText('Copiar')).toBeInTheDocument()
  })

  it('sends on Enter but preserves Shift+Enter', async () => {
    const user = userEvent.setup(); const onSend = vi.fn().mockResolvedValue(undefined)
    render(<InputBox disabled={false} onSend={onSend} />)
    const input = screen.getByLabelText('Mensagem')
    await user.type(input, 'linha 1')
    await user.keyboard('{Shift>}{Enter}{/Shift}linha 2')
    expect(onSend).not.toHaveBeenCalled()
    await user.keyboard('{Enter}')
    expect(onSend).toHaveBeenCalledWith('linha 1\nlinha 2', null)
  })
  it('removes the chat RAG selector and locks the model when a sidebar RAG is active', () => {
    render(<InputBox disabled={false} onSend={vi.fn().mockResolvedValue(undefined)} aiModels={[{ id: 'gemini-1', provider: 'gemini', name: 'Gemini' }]} modelId="" knowledgeBaseId="rag-1" />)

    expect(screen.queryByRole('combobox', { name: 'RAG Google (opcional)' })).not.toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Modelo' })).toBeDisabled()
    expect(screen.getByText('RAG selecionado: a resposta usa somente o Store escolhido.')).toBeInTheDocument()
  })

  it('offers only OpenAI models without a selected RAG', () => {
    render(<InputBox disabled={false} onSend={vi.fn().mockResolvedValue(undefined)} aiModels={[
      { id: 'gemini-1', provider: 'gemini', name: 'Gemini' },
      { id: 'openai-1', provider: 'openai', name: 'OpenAI' },
    ]} />)

    expect(screen.queryByRole('option', { name: /Gemini/ })).not.toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'OpenAI · openai' })).toBeInTheDocument()
  })

  it('renders grounded sources as accessible safe links', () => {
    render(<MessageBubble message={{ id: '1', role: 'assistant', content: 'Resposta', created_at: new Date().toISOString(), has_image: false, sources: [{ title: 'Manual CDM', uri: 'https://example.test/manual' }, { title: 'Fonte insegura', uri: 'javascript:alert(1)' }] }} />)
    expect(screen.getByRole('heading', { name: 'Fontes consultadas' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Abrir fonte' })).toHaveAttribute('href', 'https://example.test/manual')
    expect(screen.getByText('Fonte insegura')).toBeInTheDocument()
  })

  it('copies assistant responses and does not show the action for user messages', async () => {
    const user = userEvent.setup()
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
    render(<><MessageBubble message={{ id: 'assistant-1', role: 'assistant', content: 'Resposta para copiar', created_at: new Date().toISOString(), has_image: false }} /><MessageBubble message={{ id: 'user-1', role: 'user', content: 'Pergunta', created_at: new Date().toISOString(), has_image: false }} /></>)

    await user.click(screen.getByRole('button', { name: 'Copiar resposta' }))
    expect(writeText).toHaveBeenCalledWith('Resposta para copiar')
    expect(screen.getByRole('button', { name: 'Resposta copiada' })).toHaveTextContent('Copiado')
    expect(screen.queryByRole('button', { name: 'Copiar resposta' })).not.toBeInTheDocument()
  })

  it('renders the empty collaborator state', async () => {
    vi.spyOn(adminApi, 'users').mockResolvedValue([])
    render(<AdminPanel onClose={vi.fn()} />)
    expect(await screen.findByText('Nenhum colaborador cadastrado.')).toBeInTheDocument()
    vi.restoreAllMocks()
  })
})
