import { AnalysisResult, SkillGap } from '../types'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import { Briefcase, Building2, MapPin, Award, TrendingUp, Target } from 'lucide-react'

interface Props {
  result: AnalysisResult
  sessionId: string
}

export default function CVAnalysisPage({ result }: Props) {
  const { user, isGuest } = useAuth()
  const navigate = useNavigate()
  
  const topJob = result.job_matches[0]
  const matchScore = topJob ? topJob.match_score : result.resume_analysis.score
  
  // Example dummy data mapping for Career Readiness radar chart 
  // (In a real app, you'd calculate these from the analysis results)
  const radarData = [
    { subject: 'Technical Skills', A: result.resume_analysis.score, fullMark: 100 },
    { subject: 'Experience', A: Math.min(100, (result.resume_analysis.profile.experience.length * 20) + 40), fullMark: 100 },
    { subject: 'Education', A: result.resume_analysis.profile.education.length > 0 ? 90 : 50, fullMark: 100 },
    { subject: 'Projects', A: 75, fullMark: 100 }, // Mock
    { subject: 'Certifications', A: result.resume_analysis.profile.certifications.length > 0 ? 80 : 40, fullMark: 100 },
  ]

  const totalSkills = result.resume_analysis.profile.skills
  const detectedSkills = totalSkills.slice(0, 3)
  const remainingSkillsCount = Math.max(0, totalSkills.length - 3)

  const missingSkills = topJob ? topJob.missing_skills : []
  const topMissing = missingSkills.slice(0, 3)

  // Circular progress math
  const radius = 36
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (matchScore / 100) * circumference

  return (
    <div className="max-w-6xl mx-auto w-full">
      <div className="mb-8">
        <h2 className="text-sm text-slate-400 font-medium mb-1">
          {isGuest ? 'Welcome,' : 'Welcome back,'}
        </h2>
        <h1 className="text-3xl font-bold text-white">{isGuest ? 'Guest' : (user?.name || 'User')}</h1>
      </div>

      {/* Top Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        
        {/* Match Score Card */}
        <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 relative overflow-hidden flex flex-col justify-center items-center">
          <div className="absolute top-4 left-4 text-slate-400 text-sm font-medium">Match Score</div>
          <Target className="absolute top-4 right-4 w-4 h-4 text-indigo-400" />
          
          <div className="relative w-28 h-28 mt-4 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                className="text-slate-700"
                strokeWidth="8"
                stroke="currentColor"
                fill="transparent"
                r={radius}
                cx="50"
                cy="50"
              />
              <circle
                className="text-indigo-500 drop-shadow-[0_0_8px_rgba(99,102,241,0.5)] transition-all duration-1000"
                strokeWidth="8"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                r={radius}
                cx="50"
                cy="50"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl font-bold text-white">{matchScore.toFixed(0)}%</span>
            </div>
          </div>
        </div>

        {/* Skills Detected */}
        <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 relative">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-sm font-medium">Skills Detected</span>
            <Award className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-bold text-white mb-4">{totalSkills.length}</div>
          <div className="flex flex-wrap gap-2">
            {detectedSkills.map(s => (
              <span key={s} className="bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded text-xs font-medium">
                {s}
              </span>
            ))}
            {remainingSkillsCount > 0 && (
              <span className="bg-slate-700/50 text-slate-300 border border-slate-600 px-2 py-0.5 rounded text-xs font-medium">
                +{remainingSkillsCount} more
              </span>
            )}
          </div>
        </div>

        {/* Missing Skills */}
        <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 relative">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-sm font-medium">Missing Skills</span>
            <TrendingUp className="w-4 h-4 text-orange-400" />
          </div>
          <div className="text-3xl font-bold text-white mb-4">{missingSkills.length}</div>
          <div className="flex flex-wrap gap-2">
            {topMissing.length > 0 ? (
              topMissing.map(s => (
                <span key={s} className="bg-orange-500/20 text-orange-300 border border-orange-500/30 px-2 py-0.5 rounded text-xs font-medium">
                  {s}
                </span>
              ))
            ) : (
              <span className="text-slate-500 text-sm">None detected for top job!</span>
            )}
          </div>
        </div>

        {/* Experience */}
        <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 relative">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-400 text-sm font-medium">Experience</span>
            <Briefcase className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold text-white mb-4">{result.resume_analysis.profile.experience.length} roles</div>
          <p className="text-xs text-slate-400 leading-relaxed">
            {result.resume_analysis.suggestions[0] || 'Strong background with proven track record.'}
          </p>
        </div>

      </div>

      {/* Recommended Jobs */}
      <h3 className="text-xl font-bold text-white mb-4">Recommended Jobs</h3>
      <div className="space-y-4 mb-10">
        {result.job_matches.map((match, i) => (
          <div
            key={i}
            onClick={() => navigate('/app/job-matching')}
            className="bg-[#1e293b]/50 border border-slate-700/50 rounded-xl p-5 flex items-center justify-between hover:bg-[#1e293b] hover:border-indigo-500/40 transition-all cursor-pointer group"
          >
            <div>
              <h4 className="text-white font-bold text-lg mb-2">{match.job.title}</h4>
              <div className="flex items-center gap-4 text-sm text-slate-400">
                <span className="flex items-center gap-1"><Building2 className="w-4 h-4" /> {match.job.company}</span>
                <span className="flex items-center gap-1"><MapPin className="w-4 h-4" /> {match.job.location || 'Saudi Arabia'}</span>
              </div>
            </div>
            <div className="flex flex-col items-end gap-3">
              <div className="bg-indigo-900/40 text-indigo-300 border border-indigo-700/50 px-3 py-1 rounded-full text-sm font-semibold">
                {match.match_score.toFixed(0)}% Match
              </div>
              <span className="text-indigo-400 text-xs font-semibold flex items-center gap-1 group-hover:text-indigo-300 group-hover:underline transition-colors">
                View Details →
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Grid for Skill Gap & Readiness */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Skill Gap Analysis */}
        <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-8 flex flex-col">
          <h3 className="text-xl font-bold text-white mb-6">Skill Gap Analysis</h3>
          
          <div className="mb-6">
            <h4 className="text-sm text-slate-400 font-medium mb-3">Current Strengths</h4>
            <div className="flex flex-wrap gap-2">
              {totalSkills.slice(0, 8).map(s => (
                <span key={s} className="bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-3 py-1 rounded-full text-xs font-medium">
                  {s}
                </span>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <h4 className="text-sm text-slate-400 font-medium mb-3">Skills to Develop</h4>
            <div className="flex flex-wrap gap-2">
              {missingSkills.slice(0, 5).map(s => (
                <span key={s} className="bg-orange-500/20 text-orange-300 border border-orange-500/30 px-3 py-1 rounded-full text-xs font-medium">
                  {s}
                </span>
              ))}
              {missingSkills.length === 0 && <span className="text-slate-500 text-sm">No critical gaps identified!</span>}
            </div>
          </div>

          <div>
            <h4 className="text-sm text-slate-400 font-medium mb-3">Improvement Suggestions</h4>
            <ul className="space-y-2 text-sm text-slate-300 list-disc list-inside">
              {result.roadmap?.skill_gaps?.slice(0, 3).map((gap, i) => (
                <li key={i} className="text-slate-300">
                  <span className="text-white font-medium">{gap.skill}:</span> {gap.description}
                </li>
              ))}
              {!result.roadmap?.skill_gaps?.length && (
                <li className="text-slate-500 list-none">Continue building on your current strengths.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Career Readiness */}
        <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-8 flex flex-col">
          <h3 className="text-xl font-bold text-white mb-6">Career Readiness</h3>
          
          <div className="flex-1 min-h-[250px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Radar
                  name="Score"
                  dataKey="A"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fill="#6366f1"
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-[#0f172a]/60 border border-slate-700/50 p-4 rounded-xl mt-6">
            <p className="text-slate-400 text-sm leading-relaxed">
              {result.roadmap?.summary || 'Your profile shows strong educational background and solid technical skills. Focus on gaining more practical experience and industry certifications to reach senior-level positions.'}
            </p>
          </div>
        </div>

      </div>

    </div>
  )
}
