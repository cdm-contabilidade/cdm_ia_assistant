import { describe, expect, it } from 'vitest'
import { normalizeQueryMessages, updateChatSummariesAfterQuery } from './ChatContext'
import { normalizeMessage, type ChatQueryResponse } from '../types'
import { chatTitleFromQuestion } from '../utils/chatTitle'

describe('chat title normalization', () => {
  it('uses the first eight words, normalizes whitespace, and limits the title to 80 characters', () => {
    const question = '  Como\tregistrar   a conciliação bancária agora para hoje e depois confirmar os lançamentos  '

    expect(chatTitleFromQuestion(question)).toBe('Como registrar a conciliação bancária agora para hoje')
    expect(chatTitleFromQuestion('1234567890 '.repeat(8))).toBe('1234567890 '.repeat(7) + '123')
  })
})

describe('chat summary after query', () => {
  it('updates the existing sidebar item and inserts missing chats', () => {
    const updatedAt = '2026-09-11T12:00:00.000Z'
    const existing = [{ id: 'chat-1', title: 'Nova Consulta', created_at: '2026-09-11T11:00:00.000Z', updated_at: '2026-09-11T11:00:00.000Z' }]
    const result = { chatId: 'chat-1', title: 'Como registrar a conciliação' }

    expect(updateChatSummariesAfterQuery(existing, result, 'pergunta', updatedAt)).toEqual([
      { ...existing[0], title: result.title, updated_at: updatedAt },
    ])
    expect(updateChatSummariesAfterQuery(existing, { chatId: 'chat-2', title: 'Nova pergunta' }, 'pergunta', updatedAt)[0]).toEqual({
      id: 'chat-2', title: 'Nova pergunta', created_at: updatedAt, updated_at: updatedAt,
    })
  })

  it('does not replace a manually renamed title when the response has no title', () => {
    const manual = { id: 'chat-1', title: 'Título manual', created_at: '2026-09-11T11:00:00.000Z', updated_at: '2026-09-11T11:00:00.000Z' }

    expect(updateChatSummariesAfterQuery([manual], { chatId: manual.id }, 'pergunta posterior', '2026-09-11T12:00:00.000Z')).toEqual([
      { ...manual, updated_at: '2026-09-11T12:00:00.000Z' },
    ])
  })
})

describe('chat message metadata normalization', () => {
  it('flattens backend metadata without dropping attachments or sources', () => {
    const message = normalizeMessage({
      id: 'assistant-1',
      role: 'assistant',
      content: 'Resposta',
      created_at: new Date().toISOString(),
      has_image: false,
      metadata: {
        model_id: 'gemini-model',
        model_display_name: 'Gemini',
        knowledge_base_id: 'rag-1',
        knowledge_base_name: 'Fiscal',
      },
      sources: [{ title: 'Manual', uri: 'https://example.test/manual' }],
    })

    expect(message.modelId).toBe('gemini-model')
    expect(message.modelName).toBe('Gemini')
    expect(message.knowledgeBaseId).toBe('rag-1')
    expect(message.knowledgeBaseName).toBe('Fiscal')
    expect(message.sources).toHaveLength(1)
    expect(message.metadata?.knowledge_base_name).toBe('Fiscal')
  })

  it('shares query origin with the result user message and keeps images', () => {
    const result: ChatQueryResponse = {
      sessionId: 'session-1',
      chatId: 'chat-1',
      answer: 'Resposta',
      messages: [
        { id: 'user-1', role: 'user', content: 'Pergunta', created_at: new Date().toISOString(), has_image: true, image_metadata: { count: 1 } },
        { id: 'assistant-1', role: 'assistant', content: 'Resposta', created_at: new Date().toISOString(), has_image: false, metadata: { knowledge_base_id: 'rag-1', knowledge_base_name: 'Fiscal', model_id: 'gemini-model', model_display_name: 'Gemini' } },
      ],
      sources: [{ title: 'Manual', uri: 'https://example.test/manual' }],
    }

    const messages = normalizeQueryMessages(result, [{ dataUrl: 'data:image/png;base64,abc', name: 'evidencia.png', size: 3, mime: 'image/png' }])
    expect(messages[0]).toMatchObject({ knowledgeBaseId: 'rag-1', knowledgeBaseName: 'Fiscal', modelId: 'gemini-model', modelName: 'Gemini', has_image: true, imageUrls: ['data:image/png;base64,abc'] })
    expect(messages[1].sources).toEqual(result.sources)
  })

  it('maps persisted image_data onto imageUrls', () => {
    const message = normalizeMessage({
      id: 'user-2',
      role: 'user',
      content: 'Pergunta com imagem',
      created_at: new Date().toISOString(),
      has_image: true,
      image_data: ['data:image/png;base64,abc'],
    })

    expect(message.imageUrls).toEqual(['data:image/png;base64,abc'])
  })
})
