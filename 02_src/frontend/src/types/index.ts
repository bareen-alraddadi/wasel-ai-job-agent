export interface ResumeProfile {
  name: string
  email: string
  phone: string
  location: string
  summary: string
  skills: string[]
  experience: Array<{ text: string }>
  education: Array<{ text: string }>
  certifications: string[]
}

export interface ResumeAnalysis {
  profile: ResumeProfile
  score: number
  score_breakdown: Record<string, number>
  suggestions: string[]
}

export interface JobPosting {
  job_id?: string
  title: string
  company: string
  location?: string
  description: string
  required_skills: string[]
  preferred_skills: string[]
  experience_years?: string | number
  education_level?: string
  job_type?: string
  salary_range?: string    // in SAR
  industry?: string
  apply_link?: string
}

export interface MatchResult {
  job: JobPosting
  match_score: number
  matched_skills: string[]
  missing_skills: string[]
  match_explanation: string
}

export interface LearningResource {
  title: string
  provider: string
  url: string
  duration: string
  level?: string
  skill?: string
}

export interface SkillGap {
  skill: string
  priority: 'high' | 'medium' | 'low'
  description: string
  resources: LearningResource[]
  estimated_time: string
}

export interface RoadmapMilestone {
  phase: string
  title: string
  goals: string[]
  skills: string[]
}

export interface CareerRoadmap {
  target_role: string
  target_company?: string
  total_gap_score: number
  skill_gaps: SkillGap[]
  milestones: RoadmapMilestone[]
  interview_questions: string[]
  summary: string
}

export interface AnalysisResult {
  user_id: string
  session_id: string
  analysis_id: string
  mode: 'cv_and_jd' | 'cv_only'
  resume_analysis: ResumeAnalysis
  job_matches: MatchResult[]
  roadmap: CareerRoadmap
  cover_letter?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface UserProfile {
  user_id: string
  email: string
  name: string
  created_at?: string
  latest_analysis_id?: string
}

