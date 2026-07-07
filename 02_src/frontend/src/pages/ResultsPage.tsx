import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft, User, Briefcase, Map, MessageCircle,
  CheckCircle, XCircle, Clock, TrendingUp, BookOpen,
  Send, ChevronDown, ChevronUp, Star, ExternalLink,
  Building2, MapPin, Banknote, Tag, LogOut, User as UserIcon
} from 'lucide-react'
import { AnalysisResult, ChatMessage, MatchResult, SkillGap } from '../types'
import { sendChatMessage, getChatHistory } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkBreaks from 'remark-breaks'

interface Props {
  result: AnalysisResult
  sessionId: string
}

type Tab = 'overview' | 'jobs' | 'roadmap' | 'chat'

export default function ResultsPage({ result, sessionId }: Props) {
  const navigate = useNavigate()
  const { guestUserId, isGuest, user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatRestoring, setChatRestoring] = useState(true)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const WELCOME: ChatMessage = {
    role: 'assistant',
    content: `مرحباً! ${result.resume_analysis.profile.name || 'Welcome'} 👋\n\nI've finished analysing your CV. Your resume scored **${result.resume_analysis.score.toFixed(0)}/100** and your best job match is **${result.job_matches[0]?.job.title || ''}** at **${result.job_matches[0]?.job.company || ''}** with a **${result.job_matches[0]?.match_score.toFixed(0)}%** match.\n\nWhat would you like to explore?`,
  }

  // Restore chat history from Supabase on mount
  useEffect(() => {
    async function restoreChat() {
      try {
        if (!sessionId) { setMessages([WELCOME]); return }
        const history = await getChatHistory(guestUserId, sessionId)
        if (history.length > 0) {
          // Prepend welcome only if history doesn't already start with a greeting
          setMessages(history)
        } else {
          setMessages([WELCOME])
        }
      } catch {
        setMessages([WELCOME])
      } finally {
        setChatRestoring(false)
      }
    }
    restoreChat()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, guestUserId])

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async () => {
    if (!chatInput.trim() || chatLoading) return
    const text = chatInput.trim()
    setChatInput('')
    setMessages(p => [...p, { role: 'user', content: text }])
    setChatLoading(true)
    try {
      const res = await sendChatMessage(guestUserId, sessionId, text, result.analysis_id)
      setMessages(p => [...p, { role: 'assistant', content: res.message }])
    } catch {
      setMessages(p => [...p, { role: 'assistant', content: 'Sorry, I had a connection issue. Please try again.' }])
    } finally { setChatLoading(false) }
  }

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: 'overview', label: 'Overview',               icon: User },
    { key: 'jobs',     label: `Jobs (${result.job_matches.length})`, icon: Briefcase },
    { key: 'roadmap',  label: 'Roadmap',                icon: Map },
    { key: 'chat',     label: 'AI Coach',               icon: MessageCircle },
  ]

  const topMatch = result.job_matches[0]
  const roadmap  = result.roadmap

  return (
    <div className="min-h-screen bg-slate-950">

      {/* Header */}
      <div className="border-b border-slate-800 px-6 py-4 flex items-center gap-4 sticky top-0 bg-slate-950/95 backdrop-blur z-10">
        <button onClick={() => navigate('/analyze')} className="text-slate-400 hover:text-white">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <span className="text-lg font-bold text-white">وصل</span>
        <span className="text-slate-500 text-sm hidden sm:inline">— Analysis Results</span>
        <span className="hidden md:flex ml-4 items-center gap-2 bg-emerald-900/30 border border-emerald-700/50 rounded-full px-3 py-1">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span className="text-emerald-400 text-xs font-medium">Powered by GPT-4 mini</span>
        </span>
        
        <div className="ml-auto flex items-center gap-3">
          {!isGuest && user ? (
            <div className="flex items-center gap-4">
              <span className="text-slate-300 text-sm hidden sm:flex items-center gap-1.5">
                <UserIcon className="w-4 h-4 text-brand-400" /> {user.name}
              </span>
              <button 
                onClick={() => { logout(); navigate('/'); }} 
                className="text-slate-400 hover:text-white text-sm flex items-center gap-1.5 transition-colors"
              >
                <LogOut className="w-4 h-4" /> <span className="hidden sm:inline">Sign out</span>
              </button>
            </div>
          ) : (
            <button 
              onClick={() => navigate('/login')} 
              className="text-slate-300 hover:text-white text-sm font-medium transition-colors"
            >
              Log in
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-800 px-6">
        <div className="flex gap-1 max-w-5xl mx-auto">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setActiveTab(key)}
              className={`flex items-center gap-2 px-4 py-3.5 text-sm font-medium border-b-2 transition-all ${
                activeTab === key ? 'border-brand-500 text-brand-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}>
              <Icon className="w-4 h-4" />{label}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8">

        {/* ── OVERVIEW ── */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid sm:grid-cols-3 gap-4">
              <ScoreCard label="Resume score" value={`${result.resume_analysis.score.toFixed(0)}/100`}
                sub="Completeness & structure" color="brand" />
              {topMatch && (
                <ScoreCard label="Best job match" value={`${topMatch.match_score.toFixed(0)}%`}
                  sub={`${topMatch.job.title} @ ${topMatch.job.company}`}
                  color={topMatch.match_score >= 70 ? 'green' : topMatch.match_score >= 50 ? 'yellow' : 'red'} />
              )}
              <ScoreCard label="Skills detected" value={`${result.resume_analysis.profile.skills.length}`}
                sub="From your CV" color="purple" />
            </div>

            {/* Profile card */}
            <div className="card">
              <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
                <User className="w-4 h-4 text-brand-400" /> Your profile
              </h2>
              <div className="grid sm:grid-cols-2 gap-4 mb-5">
                {[['Name', result.resume_analysis.profile.name],
                  ['Email', result.resume_analysis.profile.email],
                  ['Phone', result.resume_analysis.profile.phone],
                ].map(([l, v]) => v ? (
                  <div key={l}>
                    <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">{l}</p>
                    <p className="text-white text-sm">{v}</p>
                  </div>
                ) : null)}
              </div>
              <p className="text-slate-500 text-xs uppercase tracking-wider mb-2">Skills detected</p>
              <div className="flex flex-wrap gap-2">
                {result.resume_analysis.profile.skills.slice(0,24).map(s => (
                  <span key={s} className="skill-neutral">{s}</span>
                ))}
              </div>
            </div>

            {/* Resume suggestions */}
            {result.resume_analysis.suggestions.length > 0 && (
              <div className="card border-amber-700/30 bg-amber-900/10">
                <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-amber-400" /> Resume improvements
                </h2>
                <ul className="space-y-2">
                  {result.resume_analysis.suggestions.map((s, i) => (
                    <li key={i} className="flex gap-2 text-sm text-slate-300">
                      <span className="text-amber-400 shrink-0">•</span>{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* ── JOBS ── */}
        {activeTab === 'jobs' && (
          <div className="space-y-4">
            <p className="text-slate-400 text-sm">
              {result.mode === 'cv_and_jd'
                ? 'Analysis of the job description you provided:'
                : `Top matching roles from the Saudi tech dataset (${result.job_matches.length} matches):`}
            </p>
            {result.job_matches.map((match, i) => (
              <JobMatchCard key={i} match={match} rank={i+1} />
            ))}
          </div>
        )}

        {/* ── ROADMAP ── */}
        {activeTab === 'roadmap' && roadmap && (
          <div className="space-y-6">
            <div className="card bg-brand-900/20 border-brand-700/40">
              <div className="flex items-start gap-3">
                <Map className="w-5 h-5 text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <h2 className="font-semibold text-white mb-1">
                    Roadmap → {roadmap.target_role}
                    {roadmap.target_company && <span className="text-slate-400 font-normal"> at {roadmap.target_company}</span>}
                  </h2>
                  <p className="text-slate-300 text-sm leading-relaxed">{roadmap.summary}</p>
                </div>
              </div>
            </div>

            {roadmap.skill_gaps?.length > 0 && (
              <div className="card">
                <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-brand-400" />
                  Skills to develop ({roadmap.skill_gaps.length})
                </h2>
                <div className="space-y-3">
                  {roadmap.skill_gaps.map((gap, i) => <GapCard key={i} gap={gap} />)}
                </div>
              </div>
            )}

            {roadmap.milestones?.length > 0 && (
              <div className="card">
                <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <Map className="w-4 h-4 text-emerald-400" /> Action plan
                </h2>
                <div className="space-y-4">
                  {roadmap.milestones.map((m, i) => (
                    <div key={i} className="border border-slate-700 rounded-xl p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="bg-brand-600 text-white text-xs font-bold px-2.5 py-1 rounded-full">{m.phase}</span>
                        <span className="font-medium text-white">{m.title}</span>
                      </div>
                      <ul className="space-y-1.5">
                        {m.goals.map((g, j) => (
                          <li key={j} className="text-sm text-slate-400 flex items-start gap-2">
                            <CheckCircle className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />{g}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {roadmap.interview_questions?.length > 0 && (
              <div className="card">
                <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <Star className="w-4 h-4 text-amber-400" /> Interview prep
                </h2>
                <ol className="space-y-3">
                  {roadmap.interview_questions.map((q, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-slate-300">
                      <span className="w-6 h-6 bg-slate-800 rounded-full text-xs font-bold text-brand-400 flex items-center justify-center shrink-0 mt-0.5">{i+1}</span>
                      {q}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}

        {/* ── CHAT ── */}
        {activeTab === 'chat' && (
          <div className="flex flex-col" style={{ height: 'calc(100vh - 220px)' }}>
            <div className="flex-1 overflow-y-auto space-y-4 pb-4">
              {chatRestoring ? (
                /* Loading skeleton while chat history is being fetched */
                <div className="flex justify-start">
                  <div className="bg-slate-800 border border-slate-700 rounded-2xl px-4 py-3 flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
                    <span className="text-slate-400 text-sm">Restoring conversation…</span>
                  </div>
                </div>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-relaxed prose prose-sm prose-invert ${
                      msg.role === 'user'
                        ? 'bg-brand-600 text-white prose-a:text-white prose-strong:text-white prose-headings:text-white'
                        : 'bg-slate-800 text-slate-200 border border-slate-700 prose-a:text-brand-400 prose-strong:text-white prose-headings:text-white'
                    }`}>
                      <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                ))
              )}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-800 border border-slate-700 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      {[0,1,2].map(i => (
                        <div key={i} className="w-2 h-2 bg-slate-500 rounded-full animate-bounce"
                          style={{ animationDelay: `${i*0.15}s` }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Quick prompts */}
            <div className="flex gap-2 mb-3 flex-wrap">
              {[
                'What are my top skill gaps?',
                'Which Saudi companies should I target?',
                'How can I improve my resume?',
                'Give me interview tips',
              ].map(s => (
                <button key={s} onClick={() => setChatInput(s)}
                  className="text-xs text-slate-400 bg-slate-800 border border-slate-700 rounded-full px-3 py-1.5 hover:border-brand-600 hover:text-brand-400 transition-colors">
                  {s}
                </button>
              ))}
            </div>

            <div className="flex gap-3">
              <input value={chatInput} onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
                placeholder="Ask your career coach anything..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-brand-600" />
              <button onClick={send} disabled={!chatInput.trim() || chatLoading}
                className="btn-primary flex items-center gap-2 px-4">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Sub-components ───────────────────────────────────────────

function ScoreCard({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  const clr: Record<string,string> = {
    brand: 'text-brand-400', green: 'text-emerald-400',
    yellow: 'text-amber-400', red: 'text-red-400', purple: 'text-purple-400',
  }
  return (
    <div className="card text-center">
      <p className="text-slate-400 text-xs uppercase tracking-wider mb-2">{label}</p>
      <p className={`text-4xl font-bold mb-1 ${clr[color]||'text-white'}`}>{value}</p>
      <p className="text-slate-500 text-xs leading-snug">{sub}</p>
    </div>
  )
}

function JobMatchCard({ match, rank }: { match: MatchResult; rank: number }) {
  const [open, setOpen] = useState(rank === 1)
  const sc = match.match_score
  const scoreColor = sc >= 70 ? 'text-emerald-400' : sc >= 50 ? 'text-amber-400' : 'text-red-400'
  const scoreBg    = sc >= 70 ? 'bg-emerald-900/20 border-emerald-700/40' : sc >= 50 ? 'bg-amber-900/20 border-amber-700/40' : 'bg-red-900/20 border-red-700/40'

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="flex items-start gap-3 min-w-0">
          <span className="w-7 h-7 bg-slate-800 rounded-full text-xs font-bold text-slate-400 flex items-center justify-center shrink-0">#{rank}</span>
          <div className="min-w-0">
            <h3 className="font-semibold text-white leading-tight">{match.job.title}</h3>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
              <span className="flex items-center gap-1 text-slate-400 text-xs">
                <Building2 className="w-3 h-3" />{match.job.company}
              </span>
              {match.job.location && (
                <span className="flex items-center gap-1 text-slate-400 text-xs">
                  <MapPin className="w-3 h-3" />{match.job.location}
                </span>
              )}
              {match.job.industry && (
                <span className="flex items-center gap-1 text-slate-400 text-xs">
                  <Tag className="w-3 h-3" />{match.job.industry}
                </span>
              )}
              {match.job.salary_range && (
                <span className="flex items-center gap-1 text-emerald-400 text-xs font-medium">
                  <Banknote className="w-3 h-3" />{match.job.salary_range}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className={`text-center px-3 py-2 rounded-xl border ${scoreBg}`}>
            <p className={`text-2xl font-bold leading-none ${scoreColor}`}>{sc.toFixed(0)}%</p>
            <p className="text-slate-500 text-xs mt-0.5">match</p>
          </div>
          {open ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </div>
      </div>

      {open && (
        <div className="mt-5 pt-5 border-t border-slate-800 space-y-4">
          <p className="text-slate-400 text-sm">{match.match_explanation}</p>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-emerald-400 font-medium uppercase tracking-wider mb-2 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> Matched ({match.matched_skills.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {match.matched_skills.map(s => <span key={s} className="skill-matched">{s}</span>)}
                {!match.matched_skills.length && <span className="text-slate-500 text-xs">None found</span>}
              </div>
            </div>
            <div>
              <p className="text-xs text-red-400 font-medium uppercase tracking-wider mb-2 flex items-center gap-1">
                <XCircle className="w-3.5 h-3.5" /> Missing ({match.missing_skills.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {match.missing_skills.map(s => <span key={s} className="skill-missing">{s}</span>)}
                {!match.missing_skills.length && <span className="text-emerald-400 text-xs">All required skills matched! 🎉</span>}
              </div>
            </div>
          </div>

          {match.job.apply_link && (
            <a href={match.job.apply_link} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-800 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
              Apply now <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      )}
    </div>
  )
}

function GapCard({ gap }: { gap: SkillGap }) {
  const [open, setOpen] = useState(gap.priority === 'high')
  const colors: Record<string,string> = {
    high:   'text-red-400 bg-red-900/30 border-red-700/40',
    medium: 'text-amber-400 bg-amber-900/30 border-amber-700/40',
    low:    'text-slate-400 bg-slate-800 border-slate-700',
  }
  return (
    <div className="border border-slate-700 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-800/50" onClick={() => setOpen(!open)}>
        <div className="flex items-center gap-3">
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${colors[gap.priority]}`}>{gap.priority}</span>
          <span className="font-medium text-white capitalize">{gap.skill}</span>
        </div>
        <div className="flex items-center gap-3 text-slate-500 text-xs">
          <Clock className="w-3.5 h-3.5" />{gap.estimated_time}
          {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </div>
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-slate-800">
          <p className="text-slate-400 text-sm pt-3">{gap.description}</p>
          {gap.resources?.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Learning resources</p>
              {gap.resources.map((r, i) => (
                <a key={i} href={r.url} target="_blank" rel="noopener noreferrer"
                  className="flex items-center justify-between p-3 bg-slate-800/60 rounded-lg hover:bg-slate-800 transition-colors group">
                  <div>
                    <p className="text-sm text-white font-medium">{r.title}</p>
                    <p className="text-xs text-slate-500">{r.provider}{r.duration ? ` · ${r.duration}` : ''}{r.level ? ` · ${r.level}` : ''}</p>
                  </div>
                  <ExternalLink className="w-4 h-4 text-slate-600 group-hover:text-brand-400 transition-colors shrink-0" />
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
