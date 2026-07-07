import axios from 'axios'
import { AnalysisResult, ChatMessage } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 180000, // Increased timeout to 180s to prevent premature network timeout during analysis
})

export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

export async function loginUser(email: string, password: string): Promise<any> {
  const res = await api.post('/auth/login', { email, password })
  return res.data
}

export async function signupUser(email: string, password: string, name: string, guestUserId: string): Promise<any> {
  const res = await api.post('/auth/signup', { email, password, name, guest_user_id: guestUserId })
  return res.data
}

export async function analyzeCV(
  userId: string,
  sessionId: string,
  file: File,
  jobDescription?: string,
  targetRole?: string,
  careerGoal?: string
): Promise<{ success: boolean; analysis_id: string; session_id: string; result: AnalysisResult }> {
  const form = new FormData()
  form.append('user_id', userId)
  form.append('session_id', sessionId)
  form.append('cv_file', file)
  if (jobDescription) {
    form.append('job_description', jobDescription)
  }
  if (targetRole) {
    form.append('target_role', targetRole)
  }
  if (careerGoal) {
    form.append('career_goal', careerGoal)
  }
  const res = await api.post('/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function sendChatMessage(
  userId: string,
  sessionId: string,
  message: string,
  analysisId?: string
): Promise<{ message: string; sources: string[]; suggested_actions: string[] }> {
  const res = await api.post('/chat', {
    user_id: userId,
    session_id: sessionId,
    message,
    analysis_id: analysisId,
  })
  return res.data
}

export async function getLatestAnalysis(userId: string): Promise<AnalysisResult | null> {
  try {
    const res = await api.get(`/users/${userId}/analysis/latest`)
    return res.data
  } catch {
    return null
  }
}

export async function getChatHistory(userId: string, sessionId: string): Promise<ChatMessage[]> {
  try {
    const res = await api.get(`/users/${userId}/chat/${sessionId}`)
    return res.data.messages || []
  } catch {
    return []
  }
}

export async function generateInterviewQuestions(
  userId: string,
  analysisId: string,
  skills: string[],
  targetRole: string
): Promise<{ questions: string[] }> {
  const prompt = `Generate 10 interview questions for someone applying for a ${targetRole || 'tech'} role with these skills: ${skills.slice(0, 8).join(', ')}. Mix technical and behavioral questions. Return ONLY a numbered list, one question per line, no intro text.`
  const res = await api.post('/chat', {
    user_id: userId,
    session_id: crypto.randomUUID(),
    message: prompt,
    analysis_id: analysisId,
  })
  // Parse numbered list from the response
  const raw: string = res.data.message || ''
  const questions = raw
    .split('\n')
    .map((l: string) => l.replace(/^\d+[\.\)]\s*/, '').trim())
    .filter((l: string) => l.length > 10)
  return { questions }
}

export async function getCVTips(
  userId: string,
  jobTitle: string,
  jobCompany: string,
  requiredSkills: string[],
  missingSkills: string[],
  matchScore: number
): Promise<{ section: string; action: string; tip: string }[]> {
  const res = await api.post('/cv-tips', {
    user_id: userId,
    job_title: jobTitle,
    job_company: jobCompany,
    required_skills: requiredSkills,
    missing_skills: missingSkills,
    match_score: matchScore,
  })
  return res.data.tips || []
}

export function generateUserId(): string {
  const stored = localStorage.getItem('wasel_user_id')
  if (stored) return stored
  const id = crypto.randomUUID()
  localStorage.setItem('wasel_user_id', id)
  return id
}

export function generateSessionId(): string {
  return crypto.randomUUID()
}
