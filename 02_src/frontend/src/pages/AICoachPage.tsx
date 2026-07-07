import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Bot } from 'lucide-react'
import { AnalysisResult, ChatMessage } from '../types'
import { sendChatMessage, getChatHistory } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  result: AnalysisResult
  sessionId: string
}

const SUGGESTED = [
  'How can I improve my technical skills?',
  'What certifications should I pursue?',
  'How do I negotiate salary?',
  'Tips for remote job interviews',
]

export default function AICoachPage({ result, sessionId }: Props) {
  const { guestUserId } = useAuth()

  const WELCOME: ChatMessage = {
    role: 'assistant',
    content: `Hi! I'm your **AI Career Coach**. 👋\n\nI've analysed your CV — you scored **${result.resume_analysis.score.toFixed(0)}/100** and your best match is **${result.job_matches[0]?.job.title || 'a great role'}** at **${result.job_matches[0]?.job.company || ''}** with **${result.job_matches[0]?.match_score.toFixed(0)}%** fit.\n\nAsk me anything about jobs, career growth, skills, learning plans, or interview preparation. How can I help you today?`,
  }

  const [messages, setMessages]     = useState<ChatMessage[]>([])
  const [input, setInput]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [restoring, setRestoring]   = useState(true)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Restore chat history on mount
  useEffect(() => {
    async function restore() {
      try {
        const history = await getChatHistory(guestUserId, sessionId)
        setMessages(history.length > 0 ? history : [WELCOME])
      } catch {
        setMessages([WELCOME])
      } finally {
        setRestoring(false)
      }
    }
    restore()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, guestUserId])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text?: string) => {
    const msg = (text ?? input).trim()
    if (!msg || loading) return
    setInput('')
    setMessages(p => [...p, { role: 'user', content: msg }])
    setLoading(true)
    try {
      const res = await sendChatMessage(guestUserId, sessionId, msg, result.analysis_id)
      setMessages(p => [...p, { role: 'assistant', content: res.message }])
    } catch {
      setMessages(p => [...p, { role: 'assistant', content: 'Sorry, I had a connection issue. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] max-w-5xl mx-auto w-full">

      {/* Chat messages area */}
      <div className="flex-1 overflow-y-auto space-y-6 pb-6">
        {restoring ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              {/* Avatar */}
              <div className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center shadow-lg ${
                msg.role === 'assistant'
                  ? 'bg-gradient-to-br from-indigo-500 to-purple-600'
                  : 'bg-[#1e293b] border border-slate-700'
              }`}>
                {msg.role === 'assistant'
                  ? <Sparkles className="w-4 h-4 text-white" />
                  : <span className="text-white text-xs font-bold">You</span>
                }
              </div>

              {/* Bubble */}
              <div className={`max-w-[75%] px-5 py-4 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'assistant'
                  ? 'bg-[#1e293b]/80 border border-slate-700/50 text-slate-200 rounded-tl-none'
                  : 'bg-indigo-600 text-white rounded-tr-none'
              }`}>
                {msg.role === 'assistant' ? (
                  <>
                    {idx === 0 && (
                      <div className="flex items-center gap-2 mb-3 text-xs text-indigo-400 font-semibold uppercase tracking-wider">
                        <Bot className="w-3.5 h-3.5" /> AI Career Coach
                      </div>
                    )}
                    <ReactMarkdown remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                        ul: ({ children }) => <ul className="list-disc list-inside space-y-1.5 my-2">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal list-inside space-y-3 my-2">{children}</ol>,
                        li: ({ children }) => <li className="text-slate-200 mb-1">{children}</li>,
                        h3: ({ children }) => <h3 className="text-white font-bold text-sm mt-4 mb-2">{children}</h3>,
                        h2: ({ children }) => <h2 className="text-white font-bold mt-4 mb-2">{children}</h2>,
                        a: ({ href, children }) => (
                          <a
                            href={href}
                            target="_blank"
                            rel="noreferrer"
                            className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 transition-colors"
                          >
                            {children}
                          </a>
                        ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading bubble */}
        {loading && (
          <div className="flex gap-4">
            <div className="shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="bg-[#1e293b]/80 border border-slate-700/50 px-5 py-4 rounded-2xl rounded-tl-none flex items-center gap-2">
              <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Suggested questions */}
      {messages.length <= 1 && !loading && (
        <div className="mb-4">
          <p className="text-xs text-slate-500 font-medium mb-3">Suggested questions:</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {SUGGESTED.map(q => (
              <button
                key={q}
                onClick={() => send(q)}
                className="text-left bg-[#1e293b]/50 border border-slate-700/50 hover:border-indigo-500/50 hover:bg-[#1e293b] px-4 py-3 rounded-xl text-sm text-slate-300 transition-all"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input bar */}
      <div className="flex items-end gap-3 bg-[#1e293b]/80 border border-slate-700/50 rounded-2xl px-4 py-3 backdrop-blur-md">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
          placeholder="Ask me anything about your career..."
          rows={1}
          className="flex-1 bg-transparent text-slate-200 placeholder:text-slate-600 text-sm resize-none focus:outline-none max-h-28 overflow-y-auto"
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || loading}
          className="shrink-0 w-10 h-10 rounded-xl bg-indigo-600 hover:bg-indigo-500 flex items-center justify-center transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4 text-white" />
        </button>
      </div>
    </div>
  )
}
