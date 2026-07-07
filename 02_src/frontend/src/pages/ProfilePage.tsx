import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { User, Mail, FileText, TrendingUp, Activity, Clock, CheckCircle, LogOut, Settings } from 'lucide-react'
import { AnalysisResult } from '../types'

// ProfilePage doesn't need analysis data but we accept it optionally for stats
interface Props {
  result?: AnalysisResult
}

export default function ProfilePage({ result }: Props) {
  const { user, isGuest, logout } = useAuth()
  const navigate = useNavigate()

  const displayName  = isGuest ? 'Guest' : (user?.name || 'User')
  const displayEmail = user?.email || '—'

  return (
    <div className="max-w-4xl mx-auto w-full">

      {/* Welcome */}
      <div className="mb-8">
        <h2 className="text-sm text-slate-400 font-medium mb-1">
          {isGuest ? 'Welcome,' : 'Welcome back,'}
        </h2>
        <h1 className="text-3xl font-bold text-white">{displayName}</h1>
      </div>

      {/* Profile Card */}
      <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-8 mb-6 flex flex-col sm:flex-row items-start sm:items-center gap-6">
        {/* Avatar */}
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
          <User className="w-10 h-10 text-white" />
        </div>

        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold text-white mb-1">{displayName}</h2>
          <p className="flex items-center gap-2 text-slate-400 text-sm mb-4">
            <Mail className="w-4 h-4" /> {displayEmail}
          </p>

          {isGuest ? (
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => navigate('/login')}
                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-5 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-500/20"
              >
                Create Account
              </button>
              <button
                onClick={() => navigate('/login')}
                className="bg-[#0f172a] border border-slate-700 hover:border-slate-600 text-slate-300 hover:text-white px-5 py-2 rounded-xl text-sm font-semibold transition-all"
              >
                Log In
              </button>
            </div>
          ) : (
            <div className="flex flex-wrap gap-3">
              <button
                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-5 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-500/20"
              >
                Edit Profile
              </button>
              <button
                className="bg-[#0f172a] border border-slate-700 hover:border-slate-600 text-slate-300 hover:text-white px-5 py-2 rounded-xl text-sm font-semibold transition-all flex items-center gap-2"
              >
                <Settings className="w-4 h-4" /> Settings
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'CV Analyses',    value: result ? '1'  : '0' },
          { label: 'Jobs Matched',   value: result ? String(result.job_matches.length) : '0' },
          { label: 'Skills Tracked', value: result ? String(result.resume_analysis?.profile?.skills?.length || result.skills?.length || 0) : '0' },
          { label: 'Days Active',    value: '1' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 text-center">
            <div className="text-3xl font-bold text-white mb-1">{value}</div>
            <div className="text-slate-400 text-sm">{label}</div>
          </div>
        ))}
      </div>

      {/* Career Activity */}
      <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-8 mb-6">
        <h3 className="text-lg font-bold text-white mb-6">Career Activity</h3>
        <div className="space-y-4">

          <div className="flex items-center gap-4 bg-[#0f172a]/60 border border-slate-800 rounded-xl p-4">
            <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0">
              <FileText className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <p className="text-white text-sm font-medium">Uploaded CV</p>
              <p className="text-slate-500 text-xs mt-0.5">
                {result ? (result.resume_analysis?.profile?.name || 'Your') + "'s CV" : 'No CV uploaded'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-[#0f172a]/60 border border-slate-800 rounded-xl p-4">
            <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0">
              <Activity className="w-4 h-4 text-purple-400" />
            </div>
            <div>
              <p className="text-white text-sm font-medium">Last Analysis</p>
              <p className="text-slate-500 text-xs mt-0.5">
                {result ? 'Completed just now' : 'No analysis yet'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-[#0f172a]/60 border border-slate-800 rounded-xl p-4">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <p className="text-white text-sm font-medium">Total Analyses Performed</p>
              <p className="text-slate-500 text-xs mt-0.5">
                {result ? '1 analysis' : '0 analyses'}
              </p>
            </div>
          </div>

        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-8 mb-6">
        <h3 className="text-lg font-bold text-white mb-6">Recent Activity</h3>
        {result ? (
          <div className="space-y-4">
            <div className="flex items-center gap-4 bg-[#0f172a]/60 border border-slate-800 rounded-xl p-4">
              <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0">
                <CheckCircle className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="flex-1">
                <p className="text-white text-sm font-medium">CV Analysis Completed</p>
                <p className="text-slate-500 text-xs mt-0.5">Score: {result.resume_analysis?.score?.toFixed(0) ?? 0}/100</p>
              </div>
              <Clock className="w-4 h-4 text-slate-600" />
            </div>
            <div className="flex items-center gap-4 bg-[#0f172a]/60 border border-slate-800 rounded-xl p-4">
              <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0">
                <CheckCircle className="w-4 h-4 text-purple-400" />
              </div>
              <div className="flex-1">
                <p className="text-white text-sm font-medium">Job Matches Found</p>
                <p className="text-slate-500 text-xs mt-0.5">{result.job_matches.length} opportunities matched to your profile</p>
              </div>
              <Clock className="w-4 h-4 text-slate-600" />
            </div>
          </div>
        ) : (
          <p className="text-slate-500 text-sm text-center py-6">No recent activity yet. Upload your CV to get started!</p>
        )}
      </div>

      {/* Sign out */}
      {!isGuest && (
        <button
          onClick={() => { logout(); navigate('/') }}
          className="flex items-center gap-2 text-red-400 hover:text-red-300 text-sm font-medium transition-colors mt-2"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      )}
    </div>
  )
}
