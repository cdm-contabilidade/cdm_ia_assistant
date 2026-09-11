export function chatTitleFromQuestion(question: string): string {
  const normalizedQuestion = question.trim().split(/\s+/u).slice(0, 8).join(' ')
  return Array.from(normalizedQuestion).slice(0, 80).join('')
}
