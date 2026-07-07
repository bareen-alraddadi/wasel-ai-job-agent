import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Sparkles, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { analyzeCV, generateSessionId } from '../utils/api'
import { AnalysisResult } from '../types'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

interface Props {
  onComplete: (result: AnalysisResult, sessionId: string) => void
}

const STEPS = [
  'Parsing your CV...',
  'Extracting skills and profile...',
  'Searching job matches...',
  'Calculating match scores...',
  'Building your roadmap...',
  'Generating interview questions...',
]

export default function DashboardPage({ onComplete }: Props) {
  const { user, isGuest, guestUserId } = useAuth()
  const navigate = useNavigate()
  
  const [file, setFile] = useState<File | null>(null)
  const [jobDesc, setJobDesc] = useState('')
  const [loading, setLoading] = useState(false)
  const [stepIdx, setStepIdx] = useState(0)

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    maxFiles: 1,
  })

  const handleAnalyze = async () => {
    if (!file) {
      toast.error('Please upload your CV first')
      return
    }

    setLoading(true)
    setStepIdx(0)
    localStorage.removeItem('wasel_session_cache')

    const interval = setInterval(() => {
      setStepIdx(prev => Math.min(prev + 1, STEPS.length - 1))
    }, 3500)

    try {
      const sessionId = generateSessionId()
      const res = await analyzeCV(guestUserId, sessionId, file, jobDesc.trim() ? jobDesc : undefined)

      clearInterval(interval)

      if (res.success) {
        toast.success('Analysis complete!')
        onComplete(res.result, res.session_id)
      } else {
        toast.error('Analysis failed. Please try again.')
      }
    } catch (err: any) {
      clearInterval(interval)
      const errorMsg = err?.response?.data?.detail || 'Analysis failed. Check your connection.'
      toast.error(errorMsg)
      
      if (err?.response?.status === 403 && errorMsg.includes('Guest limit')) {
         navigate('/login', { state: { from: { pathname: '/app/dashboard' } } })
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full">
        <div className="relative w-16 h-16 mx-auto mb-8">
          <div className="w-16 h-16 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-3">Analyzing your profile</h2>
        <p className="text-indigo-400 text-sm font-medium mb-6">{STEPS[stepIdx]}</p>
        <div className="flex gap-1.5 justify-center">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1 rounded-full transition-all duration-500 ${
                i <= stepIdx ? 'bg-indigo-500 w-6' : 'bg-slate-700 w-3'
              }`}
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto w-full">
      <div className="mb-8">
        <h2 className="text-sm text-slate-400 font-medium mb-1">
          {isGuest ? 'Welcome,' : 'Welcome back,'}
        </h2>
        <h1 className="text-3xl font-bold text-white">{isGuest ? 'Guest' : (user?.name || 'User')}</h1>
      </div>

      <div className="bg-[#1e293b]/80 border border-slate-700/50 rounded-2xl p-6 mb-6 flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div>
          <h3 className="text-white font-semibold text-lg">Welcome Back</h3>
          <p className="text-slate-400 text-sm">Let's continue building your career journey.</p>
        </div>
      </div>

      <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 mb-6">
        <h3 className="text-white font-semibold mb-4">Upload Your CV</h3>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
            isDragActive
              ? 'border-indigo-500 bg-indigo-500/10'
              : file
              ? 'border-indigo-500/50 bg-indigo-500/5'
              : 'border-slate-700 hover:border-slate-600 bg-[#0f172a]/50'
          }`}
        >
          <input {...getInputProps()} />
          {file ? (
            <div className="flex flex-col items-center">
              <FileText className="w-10 h-10 text-indigo-400 mb-3" />
              <p className="font-semibold text-white">{file.name}</p>
              <p className="text-slate-400 text-sm mt-1">{(file.size / 1024).toFixed(0)} KB · Click to change</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-full bg-[#1e293b] flex items-center justify-center mb-4 border border-slate-700">
                <Upload className="w-5 h-5 text-indigo-400" />
              </div>
              <p className="font-semibold text-white mb-1">Drag and drop your CV here</p>
              <p className="text-slate-500 text-sm">or click to browse (PDF or DOCX)</p>
            </div>
          )}
        </div>
      </div>

      <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 mb-6">
        <h3 className="text-white font-semibold mb-1">Job Description (Optional)</h3>
        <p className="text-slate-400 text-sm mb-4">Paste a job description to compare against your CV</p>
        <textarea
          value={jobDesc}
          onChange={e => setJobDesc(e.target.value)}
          placeholder="Paste job description here..."
          rows={5}
          className="w-full bg-[#0f172a] border border-slate-700 rounded-xl px-4 py-3 text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 resize-none text-sm"
        />
      </div>

      <div className="flex justify-end mb-10">
        <button
          onClick={handleAnalyze}
          disabled={!file}
          className={`px-8 py-3 rounded-xl font-semibold text-sm transition-all ${
            file
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }`}
        >
          {file ? 'Analyze Profile' : 'Upload CV to Start'}
        </button>
      </div>
      
      {isGuest && (
        <p className="text-center text-slate-500 text-xs">
          Guest Mode: You have a limit of 2 analyses. Sign up to save your progress.
        </p>
      )}
    </div>
  )
}
