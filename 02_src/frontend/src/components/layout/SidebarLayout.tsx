import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom'
import { LayoutDashboard, FileText, Briefcase, Map, GraduationCap, MessageCircle, User, FileSignature } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import waselLogo from '../../assets/wasel_logo.png'

export default function SidebarLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const navItems = [
    { name: 'Dashboard',       path: '/app/dashboard',   icon: LayoutDashboard },
    { name: 'CV Analysis',     path: '/app/cv-analysis', icon: FileText },
    { name: 'Cover Letter',    path: '/app/cover-letter', icon: FileSignature },
    { name: 'Job Matching',    path: '/app/job-matching', icon: Briefcase },
    { name: 'Learning Roadmap', path: '/app/roadmap',    icon: Map },
    { name: 'Interview Prep',  path: '/app/interview',   icon: GraduationCap },
    { name: 'AI Coach',        path: '/app/ai-coach',    icon: MessageCircle },
    { name: 'Profile',         path: '/app/profile',     icon: User },
  ]

  return (
    <div className="flex h-screen bg-[#0B1120] text-slate-200 overflow-hidden">
      
      {/* Sidebar */}
      <aside className="w-64 bg-[#111827] border-r border-slate-800 flex flex-col">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8 cursor-pointer" onClick={() => navigate('/')}>
            <img src={waselLogo} alt="Wasel Logo" className="w-8 h-8 object-contain rounded" />
            <span className="text-xl font-bold text-white tracking-wide">WASEL</span>
          </div>

          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path)
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-xl font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg'
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Page Content */}
        <div className="flex-1 overflow-y-auto px-8 py-10 pb-20">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
