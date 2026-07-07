import { useNavigate } from 'react-router-dom'
import { ArrowRight, Zap, Target, Map, MessageCircle, ChevronRight, Briefcase, LogOut, User as UserIcon } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import waselLogo from '../assets/wasel_logo.png'

const features = [
  { icon: Zap,           title: 'CV Analysis',      desc: 'Extract and score your skills, experience, and profile in seconds using GPT-4 mini.' },
  { icon: Target,        title: 'Saudi Job Match',   desc: 'Semantic AI matching against 500 real Saudi tech jobs — Aramco, NEOM, STC, Careem and more.' },
  { icon: Map,           title: 'Career Roadmap',    desc: 'Personalised 30/90/180-day plan with real learning resources to close your skill gaps.' },
  { icon: MessageCircle, title: 'AI Coach',          desc: 'Ask anything — your coach knows your CV, job matches, and gaps from day one.' },
]

const companies = ['Saudi Aramco','NEOM','stc','Careem','Foodics','Tamara','Noon','Al Rajhi Bank','SDAIA','PwC']

export default function LandingPage() {
  const navigate = useNavigate()
  const { isGuest, user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-[#0B1120] overflow-hidden selection:bg-indigo-500/30">
      
      {/* Decorative background gradients */}
      <div className="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-indigo-900/20 to-transparent pointer-events-none" />
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-purple-600/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-40 -left-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-[100px] pointer-events-none" />

      {/* Nav */}
      <nav className="border-b border-slate-800/50 bg-[#0B1120]/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src={waselLogo} alt="Wasel Logo" className="w-8 h-8 object-contain rounded" />
            <span className="text-xl font-bold text-white tracking-wide">WASEL</span>
            <span className="hidden sm:inline-flex items-center gap-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-3 py-1 text-xs text-indigo-400 font-medium ml-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
              more than 1000 tech jobs in Saudi Arabia
            </span>
          </div>
          <div className="flex items-center gap-4">
            {!isGuest && user ? (
              <div className="flex items-center gap-4">
                <span className="text-slate-300 text-sm hidden sm:flex items-center gap-1.5">
                  <UserIcon className="w-4 h-4 text-indigo-400" /> {user.name}
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
                className="text-slate-300 hover:text-white text-sm font-medium transition-colors hidden sm:block"
              >
                Log in
              </button>
            )}
            <button
              onClick={() => navigate('/app/dashboard')}
              className="bg-white text-[#0B1120] hover:bg-slate-200 flex items-center gap-2 text-sm px-5 py-2.5 rounded-xl font-semibold transition-colors"
            >
              Get started <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative max-w-5xl mx-auto px-6 pt-32 pb-24 text-center z-10">
        <div className="inline-flex items-center gap-2 bg-slate-800/50 border border-slate-700/50 rounded-full px-4 py-1.5 mb-8 backdrop-blur-sm">
          <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
          <span className="text-slate-300 text-sm font-medium">Powered by GPT-4 mini · Saudi tech market</span>
        </div>

        <h1 className="text-5xl md:text-7xl font-extrabold text-white mb-8 tracking-tight">
          Your AI career agent <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
            built for Saudi tech roles
          </span>
        </h1>

        <p className="text-lg md:text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
          Upload your CV. Get a personalised match score against real Saudi job openings,
          a skill-gap roadmap, and an AI coach that knows the local market —
          all in under 30 seconds.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => navigate('/app/dashboard')}
            className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/25 flex items-center justify-center gap-2 text-base px-8 py-4 rounded-xl font-semibold transition-all hover:scale-[1.02]"
          >
            Analyze my CV <ArrowRight className="w-5 h-5" />
          </button>
          <button
            onClick={() => navigate('/app/dashboard')}
            className="bg-slate-800/50 hover:bg-slate-800 border border-slate-700 text-white text-base px-8 py-4 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all hover:scale-[1.02] backdrop-blur-sm"
          >
            <Briefcase className="w-5 h-5 text-indigo-400" /> Match to a specific job
          </button>
        </div>
      </section>

      {/* Company logos ticker
      <div className="border-y border-slate-800/50 bg-[#111827]/30 py-6 overflow-hidden mb-24 backdrop-blur-sm">
        <div className="flex gap-8 items-center px-6 max-w-7xl mx-auto">
          <p className="text-slate-500 text-sm font-medium whitespace-nowrap shrink-0">Jobs from:</p>
          <div className="flex gap-10 flex-wrap items-center opacity-70">
            {companies.map(c => (
              <span key={c} className="text-slate-300 font-semibold whitespace-nowrap">{c}</span>
            ))}
            <span className="text-indigo-400 text-sm font-bold">+ 490 more</span>
          </div>
        </div>
      </div> */}

      {/* Features */}
      <section className="max-w-7xl mx-auto px-6 pb-24 grid sm:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
        {features.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="bg-[#1e293b]/50 border border-slate-700/50 rounded-2xl p-6 hover:border-indigo-500/50 transition-all group backdrop-blur-sm hover:bg-[#1e293b]/80">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Icon className="w-6 h-6 text-indigo-400" />
            </div>
            <h3 className="font-semibold text-white mb-3 text-lg">{title}</h3>
            <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
          </div>
        ))}
      </section>

      {/* How it works */}
      <section className="max-w-4xl mx-auto px-6 pb-32">
        <h2 className="text-3xl font-bold text-white text-center mb-16">How it works</h2>
        <div className="space-y-4 relative">
          {/* Vertical line connector */}
          <div className="absolute left-8 top-8 bottom-8 w-px bg-slate-800 hidden md:block" />
          
          {[
            ['Upload your CV',     'PDF or DOCX — we extract your full profile and skills automatically'],
            ['Choose your path',   'Paste a specific job description, or let Wasel find your top 3 Saudi matches'],
            ['Get your results',   'Match score per job, missing skills, and a step-by-step career roadmap'],
            ['Chat with your coach','Ask follow-up questions — your coach already knows your analysis'],
          ].map(([title, desc], i) => (
            <div key={i} className="flex flex-col md:flex-row items-start md:items-center gap-6 bg-[#1e293b]/30 border border-slate-700/50 p-6 rounded-2xl relative z-10 hover:bg-[#1e293b]/60 transition-colors">
              <div className="w-16 h-16 rounded-2xl bg-[#0f172a] border border-slate-700 flex items-center justify-center shrink-0 shadow-inner">
                <span className="text-2xl font-bold text-indigo-400">{i+1}</span>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-lg font-semibold text-white mb-1">{title}</h4>
                <p className="text-slate-400">{desc}</p>
              </div>
              <div className="hidden md:flex w-10 h-10 rounded-full bg-[#0f172a] border border-slate-700 items-center justify-center group-hover:border-indigo-500/50 transition-colors">
                <ChevronRight className="w-5 h-5 text-slate-500" />
              </div>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-slate-800/50 bg-[#111827]/50 py-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <img src={waselLogo} alt="Wasel Logo" className="w-6 h-6 object-contain rounded" />
            <span className="text-slate-400 font-semibold text-sm tracking-wider">WASEL</span>
          </div>
          <p className="text-slate-500 text-sm">
            AI Career Agent · GPT-4 mini · FastAPI · React · Supabase
          </p>
        </div>
      </footer>
    </div>
  )
}
