import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import AnalysisPage from './pages/AnalysisPage'
import ResultsPage from './pages/ResultsPage'
import LoginPage from './pages/LoginPage'
import SidebarLayout from './components/layout/SidebarLayout'
import DashboardPage from './pages/DashboardPage'
import CVAnalysisPage from './pages/CVAnalysisPage'
import JobMatchingPage from './pages/JobMatchingPage'
import LearningRoadmapPage from './pages/LearningRoadmapPage'
import InterviewPrepPage from './pages/InterviewPrepPage'
import AICoachPage from './pages/AICoachPage'
import ProfilePage from './pages/ProfilePage'
import CoverLetterPage from './pages/CoverLetterPage'
import { AnalysisResult } from './types'
import { getLatestAnalysis } from './utils/api'
import { useAuth } from './context/AuthContext'

// ── Cache config ──────────────────────────────────────────────
const CACHE_KEY = 'wasel_session_cache'
const CACHE_TTL = 30 * 60 * 1000  // 30 minutes in ms

interface SessionCache {
  result:     AnalysisResult
  sessionId:  string
  analysisId: string
  cachedAt:   number  // Date.now() timestamp
}

function readCache(): SessionCache | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function writeCache(result: AnalysisResult, sessionId: string, analysisId: string) {
  const cache: SessionCache = {
    result,
    sessionId,
    analysisId,
    cachedAt: Date.now(),
  }
  localStorage.setItem(CACHE_KEY, JSON.stringify(cache))
}

function isCacheExpired(cache: SessionCache): boolean {
  return Date.now() - cache.cachedAt > CACHE_TTL
}

// ── App ───────────────────────────────────────────────────────
export default function App() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [sessionId, setSessionId]           = useState<string>('')
  const [restoring, setRestoring]           = useState(true)
  const { guestUserId, loading: authLoading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (authLoading) return

    async function restore() {
      try {
        const cache = readCache()

        if (cache && !isCacheExpired(cache)) {
          setAnalysisResult(cache.result)
          setSessionId(cache.sessionId)
          return
        }

        if (guestUserId) {
          const latest = await getLatestAnalysis(guestUserId).catch(() => null)
          if (latest) {
            const sid = cache?.sessionId ?? crypto.randomUUID()
            writeCache(latest, sid, latest.analysis_id ?? '')
            setAnalysisResult(latest)
            setSessionId(sid)
          } else {
            setAnalysisResult(null)
          }
        }
      } finally {
        setRestoring(false)
      }
    }

    restore()
  }, [authLoading, guestUserId])

  const handleComplete = (result: AnalysisResult, sid: string) => {
    const analysisId = result.analysis_id ?? crypto.randomUUID()
    writeCache(result, sid, analysisId)
    setAnalysisResult(result)
    setSessionId(sid)
    navigate('/app/cv-analysis')
  }

  if (authLoading || restoring) {
    return (
      <div className="min-h-screen bg-[#0B1120] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Restoring your session…</p>
        </div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      
      {/* Old Legacy routes mapping to new routes just in case */}
      <Route path="/analyze" element={<Navigate to="/app/dashboard" replace />} />
      <Route path="/results" element={<Navigate to="/app/cv-analysis" replace />} />
      
      {/* New Sidebar Layout */}
      <Route path="/app" element={<SidebarLayout />}>
        <Route index element={<Navigate to="/app/dashboard" replace />} />
        
        <Route 
          path="dashboard" 
          element={<DashboardPage onComplete={handleComplete} />} 
        />
        

        {/* Existing CV Analysis Route */}
        <Route 
          path="cv-analysis" 
          element={
            analysisResult ? (
              <CVAnalysisPage result={analysisResult} sessionId={sessionId} />
            ) : (
              <Navigate to="/app/dashboard" replace />
            )
          } 
        />
        
        <Route 
          path="cover-letter" 
          element={
            <CoverLetterPage result={analysisResult} />
          } 
        />
        {/* New Routes */}
        <Route 
          path="job-matching" 
          element={
            analysisResult ? <JobMatchingPage result={analysisResult} /> : <Navigate to="/app/dashboard" replace />
          } 
        />
        <Route 
          path="roadmap" 
          element={
            analysisResult ? <LearningRoadmapPage result={analysisResult} /> : <Navigate to="/app/dashboard" replace />
          } 
        />
        <Route 
          path="interview" 
          element={
            analysisResult ? <InterviewPrepPage result={analysisResult} /> : <Navigate to="/app/dashboard" replace />
          } 
        />
        <Route 
          path="ai-coach" 
          element={
            analysisResult ? <AICoachPage result={analysisResult} sessionId={sessionId} /> : <Navigate to="/app/dashboard" replace />
          } 
        />
        
        <Route path="profile" element={<ProfilePage result={analysisResult ?? undefined} />} />
      </Route>
    </Routes>
  )
}
