import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Sidebar } from './Sidebar'

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useChat: vi.fn(),
  getApiError: vi.fn(() => 'Não foi possível excluir a conversa.'),
}))

vi.mock('../contexts/AuthContext', () => ({ useAuth: mocks.useAuth }))
vi.mock('../contexts/ChatContext', () => ({ useChat: mocks.useChat }))
vi.mock('../services/api', () => ({ getApiError: mocks.getApiError }))

const chat = { id: 'chat-1', title: 'Consulta fiscal', created_at: '2025-01-01', updated_at: '2025-01-01' }
const rag = { id: 'rag-1', name: 'Reforma Tributária', featured: true }

function renderSidebar(deleteChat = vi.fn(), role: 'admin' | 'collaborator' = 'collaborator', selectedRag = '') {
  const onNotify = vi.fn()
  const setKnowledgeBaseId = vi.fn()
  mocks.useAuth.mockReturnValue({ user: { name: 'Ana', email: 'ana@example.com', role }, logout: vi.fn() })
  mocks.useChat.mockReturnValue({ chats: [chat], activeChatId: chat.id, selectChat: vi.fn(), createChat: vi.fn(), renameChat: vi.fn(), deleteChat, catalogsLoading: false, knowledgeBases: [rag], knowledgeBaseId: selectedRag, setKnowledgeBaseId })
  render(<Sidebar open collapsed={false} onClose={vi.fn()} onToggle={vi.fn()} onAdmin={vi.fn()} onNotify={onNotify} />)
  return { onNotify, setKnowledgeBaseId }
}

describe('Sidebar navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('keeps authentication and theme controls out of the sidebar', () => {
    renderSidebar()

    expect(screen.queryByRole('button', { name: 'Entrar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sair' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Ativar tema escuro' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Administração' })).not.toBeInTheDocument()
  })

  it('shows only the administration action for administrators', () => {
    renderSidebar(vi.fn(), 'admin')

    expect(screen.getByRole('button', { name: 'Administração' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Ativar tema escuro' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Sair' })).not.toBeInTheDocument()
  })
  it('selects a RAG from the sidebar', async () => {
    const user = userEvent.setup()
    const { setKnowledgeBaseId } = renderSidebar()
    const ragButton = screen.getByRole('button', { name: /Reforma Tributária/ })

    expect(ragButton).toHaveAttribute('aria-pressed', 'false')
    await user.click(ragButton)

    expect(setKnowledgeBaseId).toHaveBeenCalledWith('rag-1')
  })


describe('Sidebar delete flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('opens the custom confirmation, supports cancel and never calls native confirm', async () => {
    const user = userEvent.setup()
    const deleteChat = vi.fn()
    const nativeConfirm = vi.spyOn(window, 'confirm').mockImplementation(() => true)
    renderSidebar(deleteChat)

    await user.click(screen.getByRole('button', { name: 'Excluir Consulta fiscal' }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancelar' })).toHaveFocus()
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Excluir Consulta fiscal' }))
    await user.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(deleteChat).not.toHaveBeenCalled()
    expect(nativeConfirm).not.toHaveBeenCalled()
    nativeConfirm.mockRestore()
  })

  it('deletes after confirmation and reports success', async () => {
    const user = userEvent.setup()
    const deleteChat = vi.fn().mockResolvedValue(undefined)
    const { onNotify } = renderSidebar(deleteChat)

    await user.click(screen.getByRole('button', { name: 'Excluir Consulta fiscal' }))
    await user.click(screen.getByRole('button', { name: 'Excluir conversa' }))

    await waitFor(() => expect(deleteChat).toHaveBeenCalledWith('chat-1'))
    expect(onNotify).toHaveBeenCalledWith({ tone: 'success', message: 'Conversa excluída.' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('reports a failed deletion and keeps the dialog available', async () => {
    const user = userEvent.setup()
    const deleteChat = vi.fn().mockRejectedValue(new Error('delete failed'))
    const { onNotify } = renderSidebar(deleteChat)

    await user.click(screen.getByRole('button', { name: 'Excluir Consulta fiscal' }))
    await user.click(screen.getByRole('button', { name: 'Excluir conversa' }))

    await waitFor(() => expect(onNotify).toHaveBeenCalledWith({ tone: 'error', message: 'Não foi possível excluir a conversa.' }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Excluir conversa' })).toBeEnabled()
  })
})
})
