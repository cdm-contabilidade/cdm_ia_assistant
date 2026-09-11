import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { CodeBlock } from './CodeBlock'

export function MarkdownRenderer({ content }: { content: string }) {
  return <div className="markdown-content"><ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code: ({ className, children, ...props }) => { const language = /language-(\w+)/.exec(className || '')?.[1]; const inline = !className; return inline ? <code className="markdown-inline-code rounded border border-border bg-slate-100 px-1 py-0.5 text-[.9em] dark:border-dark-border dark:bg-slate-800 dark:text-slate-100" {...props}>{children}</code> : <CodeBlock language={language} code={String(children).replace(/\n$/, '')} /> } }}>{content}</ReactMarkdown></div>
}
