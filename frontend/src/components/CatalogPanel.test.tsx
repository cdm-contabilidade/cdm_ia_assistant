import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { CatalogPanel } from './CatalogPanel'

const mocks = vi.hoisted(() => ({
  aiModels: vi.fn(),
  knowledgeBases: vi.fn(),
  createAiModel: vi.fn(),
  createKnowledgeBase: vi.fn(),
  updateAiModel: vi.fn(),
  updateKnowledgeBase: vi.fn(),
}))

vi.mock('../services/api', () => ({
  adminApi: {
    createAiModel: mocks.createAiModel,
    createKnowledgeBase: mocks.createKnowledgeBase,
    updateAiModel: mocks.updateAiModel,
    updateKnowledgeBase: mocks.updateKnowledgeBase,
  },
  catalogsApi: { aiModels: mocks.aiModels, knowledgeBases: mocks.knowledgeBases },
  getApiError: vi.fn(() => 'Não foi possível concluir a operação.'),
}))

const model = { id: 'model-1', provider: 'openai', name: 'GPT-4o', model_id: 'gpt-4o', is_active: true }
const base = { id: 'base-1', name: 'Reforma Tributária', store_id: 'fileSearchStores/reforma', is_active: true }

describe('CatalogPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.aiModels.mockResolvedValue([model])
    mocks.knowledgeBases.mockResolvedValue([base])
  })

  afterEach(() => cleanup())

  it('renders each catalog as an independent card with a readable record list', async () => {
    render(<CatalogPanel />)

    expect(await screen.findByText('GPT-4o')).toBeInTheDocument()
    expect(screen.getByText('Reforma Tributária')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Modelos cadastrados' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Bases cadastradas' })).toBeInTheDocument()
    expect(screen.getByText(/openai/)).toBeInTheDocument()
    expect(screen.getByText('fileSearchStores/reforma')).toBeInTheDocument()
  })

  it('refreshes a record status without losing the list presentation', async () => {
    const user = userEvent.setup()
    mocks.updateAiModel.mockResolvedValue({ ...model, is_active: false })
    render(<CatalogPanel />)

    await screen.findByText('GPT-4o')
    await user.click(within(screen.getAllByRole('article')[0]).getByRole('button', { name: 'Desativar' }))

    await waitFor(() => expect(mocks.updateAiModel).toHaveBeenCalledWith('model-1', { is_active: false }))
    expect(await screen.findByRole('button', { name: 'Ativar' })).toBeInTheDocument()
    expect(screen.getByText('GPT-4o')).toBeInTheDocument()
  })
})
