import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Link, useNavigate } from 'react-router-dom'
import { Upload, FileText, Briefcase, Loader2, ArrowLeft, CheckCircle, Lock } from 'lucide-react'
import toast from 'react-hot-toast'
import { analyzeCV, generateSessionId } from '../utils/api'
import { AnalysisResult } from '../types'
import { useAuth } from '../context/AuthContext'

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

export default function AnalysisPage({ onComplete }: Props) {
  const navigate = useNavigate()
  const { isGuest, guestUserId } = useAuth()
  const [file, setFile] = useState<File | null>(null)
  const [jobDesc, setJobDesc] = useState('')
//const [targetRole, setTargetRole] = useState('')
//const [careerGoal, setCareerGoal] = useState('')
  const [mode, setMode] = useState<'cv_only' | 'cv_and_jd'>('cv_only')
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
    if (mode === 'cv_and_jd' && !jobDesc.trim()) {
      toast.error('Please paste a job description')
      return
    }

    setLoading(true)
    setStepIdx(0)

    // Clear stale cache immediately — if the user refreshes during the upload
    // they should see the upload page, not the old (outdated) results
    localStorage.removeItem('wasel_session_cache')

    // Simulate step progression
    const interval = setInterval(() => {
      setStepIdx(prev => Math.min(prev + 1, STEPS.length - 1))
    }, 3500)

    try {
      // Use the stable user ID from AuthContext
      const userId = guestUserId
      const sessionId = generateSessionId()
      const res = await analyzeCV(userId, sessionId, file, mode === 'cv_and_jd' ? jobDesc : undefined)

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
      
      // If guest limit reached, redirect to login
      if (err?.response?.status === 403 && errorMsg.includes('Guest limit')) {
         navigate('/login', { state: { from: { pathname: '/analyze' } } })
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center max-w-sm px-6">
          <div className="relative w-16 h-16 mx-auto mb-8">
            <div className="w-16 h-16 rounded-full border-2 border-brand-600 border-t-transparent animate-spin" />
          </div>
          <h2 className="text-xl font-semibold text-white mb-3">Analyzing your profile</h2>
          <p className="text-brand-400 text-sm font-medium mb-6">{STEPS[stepIdx]}</p>
          <div className="flex gap-1.5 justify-center">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`h-1 rounded-full transition-all duration-500 ${
                  i <= stepIdx ? 'bg-brand-500 w-6' : 'bg-slate-700 w-3'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="border-b border-slate-800 px-6 py-4 flex items-center gap-4">
        <button onClick={() => navigate('/')} className="text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <span className="text-lg font-bold text-white">وصل</span>
          <span className="text-slate-500 text-sm ml-2">— Start your analysis</span>
        </div>
      </div>

      {isGuest && (
        <div className="bg-brand-900/30 border-b border-brand-800 text-brand-300 px-6 py-3 text-sm flex items-center justify-center gap-3">
          <Lock className="w-4 h-4" />
          <span>You are using Wasel as a guest (limit 2 analyses).</span>
          <Link to="/login" className="font-semibold hover:text-white transition-colors underline underline-offset-2 ml-2">
            Sign up to save progress
          </Link>
        </div>
      )}

      <div className="max-w-2xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-white mb-2">Upload your CV</h1>
        <p className="text-slate-400 mb-10">Get your career analysis in under 30 seconds.</p>

        {/* Mode selector */}
        <div className="flex gap-3 mb-8">
          {[
            { key: 'cv_only', label: 'Find matching jobs', icon: Briefcase },
            { key: 'cv_and_jd', label: 'Match to a specific job', icon: CheckCircle },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setMode(key as typeof mode)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl border text-sm font-medium transition-all ${
                mode === key
                  ? 'bg-brand-900/40 border-brand-600 text-brand-300'
                  : 'border-slate-700 text-slate-400 hover:border-slate-600'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* File drop zone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all mb-6 ${
            isDragActive
              ? 'border-brand-500 bg-brand-900/20'
              : file
              ? 'border-accent-600 bg-emerald-900/10'
              : 'border-slate-700 hover:border-slate-600 bg-slate-900/50'
          }`}
        >
          <input {...getInputProps()} />
          {file ? (
            <>
              <FileText className="w-10 h-10 text-accent-400 mx-auto mb-3" />
              <p className="font-semibold text-white">{file.name}</p>
              <p className="text-slate-400 text-sm mt-1">{(file.size / 1024).toFixed(0)} KB · Click to change</p>
            </>
          ) : (
            <>
              <Upload className="w-10 h-10 text-slate-500 mx-auto mb-3" />
              <p className="font-semibold text-white mb-1">Drop your CV here</p>
              <p className="text-slate-400 text-sm">PDF or DOCX · Max 10MB</p>
            </>
          )}
        </div>

        {/* Job description input */}
        {mode === 'cv_and_jd' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Job description
            </label>
            <textarea
              value={jobDesc}
              onChange={e => setJobDesc(e.target.value)}
              placeholder="Paste the full job posting here..."
              rows={8}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-brand-600 resize-none text-sm"
            />
          </div>
        )}

        <button
          onClick={handleAnalyze}
          disabled={!file}
          className={`w-full py-4 rounded-xl font-semibold text-base transition-all ${
            file
              ? 'bg-brand-600 hover:bg-brand-800 text-white'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }`}
        >
          {mode === 'cv_only' ? 'Find my top job matches →' : 'Analyze match & build roadmap →'}
        </button>

        <p className="text-center text-slate-500 text-xs mt-4">
          Your CV is processed securely and stored privately.
        </p>
      </div>
    </div>
  )
}
