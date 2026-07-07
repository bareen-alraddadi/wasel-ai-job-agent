import { FileSignature, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { AnalysisResult } from '../types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  result: AnalysisResult | null
}

export default function CoverLetterPage({ result }: Props) {
  const [copied, setCopied] = useState(false)

  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400">
        <FileSignature className="w-16 h-16 mb-4 text-slate-600" />
        <h2 className="text-xl font-semibold text-slate-300">No Analysis Data</h2>
        <p className="mt-2 text-sm text-center max-w-md">
          Please upload your CV and a Job Description in the Dashboard first.
        </p>
      </div>
    )
  }

  const coverLetter = result.cover_letter

  if (!coverLetter) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400">
        <FileSignature className="w-16 h-16 mb-4 text-slate-600" />
        <h2 className="text-xl font-semibold text-slate-300">Cover Letter Not Generated</h2>
        <p className="mt-2 text-sm text-center max-w-md text-slate-400">
          We need a Job Description to generate a tailored cover letter.
          Please go back to the Dashboard and paste a Job Description before analyzing.
        </p>
      </div>
    )
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(coverLetter)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="max-w-4xl mx-auto w-full">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileSignature className="w-6 h-6 text-indigo-400" />
            Tailored Cover Letter
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Generated specifically for your profile and the target job description.
          </p>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl transition-colors font-medium text-sm"
        >
          {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
          {copied ? 'Copied!' : 'Copy Text'}
        </button>
      </div>

      <div className="bg-[#1e293b] border border-slate-700/50 rounded-2xl p-8 shadow-xl shadow-black/20 relative">
        <div className="prose prose-invert max-w-none text-slate-300 prose-p:leading-relaxed prose-p:mb-4">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {coverLetter}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
