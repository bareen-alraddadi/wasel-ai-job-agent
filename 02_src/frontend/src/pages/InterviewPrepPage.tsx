import { useState } from 'react'
import { AnalysisResult } from '../types'
import { Lightbulb, Brain, MessageSquare, RefreshCw } from 'lucide-react'
import { generateInterviewQuestions } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

interface Props {
  result: AnalysisResult
}

function categorizeDifficulty(idx: number): 'Easy' | 'Medium' | 'Hard' {
  if (idx % 3 === 0) return 'Easy'
  if (idx % 3 === 1) return 'Medium'
  return 'Hard'
}

function categorizeType(idx: number): 'Technical' | 'Behavioral' {
  return idx % 2 === 0 ? 'Behavioral' : 'Technical'
}

const difficultyColors = {
  Easy:   'bg-emerald-900/30 text-emerald-300 border-emerald-700/50',
  Medium: 'bg-amber-900/30 text-amber-300 border-amber-700/50',
  Hard:   'bg-red-900/30 text-red-300 border-red-700/50',
}

const typeColors = {
  Behavioral: 'bg-sky-900/30 text-sky-300 border-sky-700/50',
  Technical:  'bg-purple-900/30 text-purple-300 border-purple-700/50',
}

export default function InterviewPrepPage({ result }: Props) {
  const { guestUserId } = useAuth()
  const [questions, setQuestions] = useState<string[]>(
    result.roadmap?.interview_questions || []
  )
  const [generating, setGenerating] = useState(false)

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const res = await generateInterviewQuestions(
        guestUserId,
        result.analysis_id,
        result.resume_analysis.profile.skills,
        result.job_matches[0]?.job.title || ''
      )
      setQuestions(res.questions)
      toast.success('New questions generated!')
    } catch {
      toast.error('Failed to generate questions. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const technical  = questions.filter((_, i) => categorizeType(i) === 'Technical')
  const behavioral = questions.filter((_, i) => categorizeType(i) === 'Behavioral')

  return (
    <div className="max-w-5xl mx-auto w-full">

      {/* Header */}
      <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-8 mb-8 backdrop-blur-sm relative overflow-hidden flex items-center justify-between gap-4 flex-wrap">
        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-[80px] pointer-events-none" />
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Interview Preparation</h1>
          <p className="text-slate-400">Practice interview questions tailored to your profile.</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-semibold text-sm flex items-center gap-2 transition-all disabled:opacity-60 shadow-lg shadow-indigo-500/20 shrink-0"
        >
          <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
          {generating ? 'Generating...' : 'Generate More Questions'}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-sm font-medium">Total Questions</span>
            <Lightbulb className="w-5 h-5 text-amber-400" />
          </div>
          <div className="text-4xl font-bold text-white">{questions.length}</div>
        </div>
        <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-sm font-medium">Technical</span>
            <Brain className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-4xl font-bold text-white">{technical.length}</div>
        </div>
        <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-sm font-medium">Behavioral</span>
            <MessageSquare className="w-5 h-5 text-sky-400" />
          </div>
          <div className="text-4xl font-bold text-white">{behavioral.length}</div>
        </div>
      </div>

      {/* Question Cards */}
      {questions.length === 0 ? (
        <div className="text-center py-20">
          <Lightbulb className="w-16 h-16 text-amber-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">No questions yet</h3>
          <p className="text-slate-400">Click "Generate More Questions" to get personalized interview questions.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((q, idx) => {
            const type = categorizeType(idx)
            const diff = categorizeDifficulty(idx)
            return (
              <div
                key={idx}
                className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 hover:bg-[#1e293b]/80 transition-colors backdrop-blur-sm"
              >
                <div className="flex items-start gap-5">
                  <div className="shrink-0 w-10 h-10 rounded-xl bg-[#0f172a] border border-slate-700 flex items-center justify-center text-sm font-bold text-indigo-400">
                    Q{idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap gap-2 mb-3">
                      <span className={`px-3 py-0.5 rounded-full text-xs font-semibold border ${typeColors[type]}`}>
                        {type}
                      </span>
                      <span className={`px-3 py-0.5 rounded-full text-xs font-semibold border ${difficultyColors[diff]}`}>
                        {diff}
                      </span>
                    </div>
                    <p className="text-white text-base leading-relaxed">{q}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
