import React, { createContext, useContext, useState, useEffect } from 'react'
import { UserProfile } from '../types'
import { loginUser, signupUser, setAuthToken, generateUserId } from '../utils/api'

interface AuthContextType {
  user: UserProfile | null
  token: string | null
  isGuest: boolean
  guestUserId: string
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [guestUserId, setGuestUserId] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)

  // On mount, check if there's a stored session
  useEffect(() => {
    // 1. Initialize or load Guest User ID
    const guestId = generateUserId()
    setGuestUserId(guestId)

    // 2. Load stored authenticated session
    const storedToken = localStorage.getItem('wasel_auth_token')
    const storedUser = localStorage.getItem('wasel_auth_user')

    if (storedToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser) as UserProfile
        setToken(storedToken)
        setUser(parsedUser)
        setAuthToken(storedToken) // Set default header for axios calls
      } catch (e) {
        console.error("Failed to restore session:", e)
        localStorage.removeItem('wasel_auth_token')
        localStorage.removeItem('wasel_auth_user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    setLoading(true)
    try {
      const data = await loginUser(email, password)
      const { access_token, user: profile } = data

      // Persist session
      localStorage.setItem('wasel_auth_token', access_token)
      localStorage.setItem('wasel_auth_user', JSON.stringify(profile))
      
      setToken(access_token)
      setUser(profile)
      setAuthToken(access_token) // Update api client default headers
      
      // Override local user id with claimed user id
      localStorage.setItem('wasel_user_id', profile.user_id)
      setGuestUserId(profile.user_id)
    } finally {
      setLoading(false)
    }
  }

  const signup = async (email: string, password: string, name: string) => {
    setLoading(true)
    try {
      // Pass guestUserId so the backend claims the profile
      const data = await signupUser(email, password, name, guestUserId)
      const { access_token, user: profile } = data

      // Persist session
      localStorage.setItem('wasel_auth_token', access_token)
      localStorage.setItem('wasel_auth_user', JSON.stringify(profile))
      
      setToken(access_token)
      setUser(profile)
      setAuthToken(access_token)

      // The new user ID should match the claimed user ID
      localStorage.setItem('wasel_user_id', profile.user_id)
      setGuestUserId(profile.user_id)
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    // Clear credentials
    localStorage.removeItem('wasel_auth_token')
    localStorage.removeItem('wasel_auth_user')
    // Clear cached analyses
    localStorage.removeItem('wasel_session_cache')
    
    // Reset state
    setToken(null)
    setUser(null)
    setAuthToken(null)

    // Generate a fresh guest user ID so they can start fresh
    const freshGuestId = crypto.randomUUID()
    localStorage.setItem('wasel_user_id', freshGuestId)
    setGuestUserId(freshGuestId)
  }

  const isGuest = !user

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isGuest,
        guestUserId,
        login,
        signup,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
