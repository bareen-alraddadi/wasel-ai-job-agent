import { AnalysisResult, SkillGap } from '../types'
import { BookOpen, Code, Award, CheckCircle2 } from 'lucide-react'

interface Props {
  result: AnalysisResult
}

export default function LearningRoadmapPage({ result }: Props) {
  const gaps = result.roadmap?.skill_gaps || []

  // Group by priority to simulate 30/60/90 day plans
  const plan30 = gaps.filter(g => g.priority === 'high')
  const plan60 = gaps.filter(g => g.priority === 'medium')
  const plan90 = gaps.filter(g => g.priority === 'low')

  const renderSection = (title: string, subtitle: string, items: SkillGap[], badgeColor: string) => {
    if (items.length === 0) return null

    return (
      <div className="relative pl-8 pb-12">
        {/* Timeline Line */}
        <div className="absolute top-0 bottom-0 left-[11px] w-px bg-slate-800" />
        
        {/* Timeline Dot — centered with the badge row */}
        <div className={`absolute top-4 left-0 w-6 h-6 rounded-full border-4 border-[#0B1120] ${badgeColor} z-10 flex items-center justify-center`} />

        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <div className={`${badgeColor} px-4 py-1.5 rounded-full text-white text-sm font-bold shadow-lg`}>
            {title}
          </div>
          <span className="text-slate-500 text-sm font-medium">{subtitle}</span>
        </div>

        {/* Cards */}
        <div className="space-y-6">
          {items.map((gap, idx) => (
            <div key={idx} className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 hover:border-indigo-500/30 transition-colors backdrop-blur-sm relative">
              <h3 className="text-xl font-bold text-white mb-4">{gap.skill}</h3>
              <p className="text-slate-400 text-sm mb-6">{gap.description}</p>
              
              <div className="space-y-6">
                
                {/* Resources */}
                {gap.resources.length > 0 && (
                  <div>
                    <h4 className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
                      <BookOpen className="w-4 h-4 text-indigo-400" /> Recommended Learning
                    </h4>
                    <ul className="space-y-2">
                      {gap.resources.map((res, i) => (
                        <li key={i} className="text-sm text-slate-400 flex items-start gap-2">
                          <span className="text-indigo-500 mt-1">•</span>
                          {res.url ? (
                            <a
                              href={res.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-indigo-400 hover:text-indigo-300 hover:underline transition-colors font-medium"
                            >
                              {res.title}
                            </a>
                          ) : (
                            <span className="text-slate-300">{res.title}</span>
                          )}
                          {res.provider && (
                            <span className="text-slate-500 ml-1 text-xs">({res.provider})</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Practical Projects (Mocked since API doesn't provide specific projects yet) */}
                <div>
                  <h4 className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-3">
                    <Code className="w-4 h-4 text-purple-400" /> Practical Application
                  </h4>
                  <ul className="space-y-2">
                    <li className="text-sm text-slate-400 flex items-start gap-2">
                      <span className="text-purple-500 mt-1">•</span>
                      Build a small proof-of-concept project integrating {gap.skill}.
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto w-full pb-20">
      {/* Header */}
      <div className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-8 mb-12 backdrop-blur-sm relative overflow-hidden">
        <div className="absolute top-0 left-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-[80px] pointer-events-none" />
        <h1 className="text-3xl font-bold text-white mb-2">Learning Roadmap</h1>
        <p className="text-slate-400">Your personalized career growth plan</p>
      </div>

      <div className="relative mt-8">
        {renderSection('30-Day Plan', 'Month 1 — High Priority', plan30, 'bg-indigo-500')}
        {renderSection('60-Day Plan', 'Month 2 — Medium Priority', plan60, 'bg-purple-500')}
        {renderSection('90-Day Plan', 'Month 3 — Low Priority', plan90, 'bg-emerald-500')}
        
        {gaps.length === 0 && (
          <div className="text-center py-20">
            <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">You are perfectly aligned!</h3>
            <p className="text-slate-400">We didn't detect any major skill gaps for your target roles.</p>
          </div>
        )}
      </div>
    </div>
  )
}
