import { describe, expect, it } from 'vitest'
import { getApiError } from './api'

describe('getApiError', () => {
  it('returns a FastAPI detail message', () => {
    expect(getApiError({ response: { data: { detail: { message: 'Acesso negado.' } } } })).toBe('Acesso negado.')
  })

  it('returns a network error message when there is no API response', () => {
    expect(getApiError({ message: 'Network Error' })).toBe('Network Error')
  })
})
