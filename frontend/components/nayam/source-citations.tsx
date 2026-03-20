'use client'

import { SourceCitation } from '@/lib/types'
import { useState } from 'react'
import { FileText, ChevronDown, ChevronUp } from 'lucide-react'

interface SourceCitationsProps {
  sources: SourceCitation[]
  className?: string
}

export function SourceCitations({ sources, className = '' }: SourceCitationsProps) {
  const [expandedIndices, setExpandedIndices] = useState<Set<number>>(new Set())

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedIndices)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedIndices(newExpanded)
  }

  if (!sources || sources.length === 0) {
    return (
      <div className={`mt-3 px-3 py-2 bg-blue-50 text-blue-700 text-sm rounded-md flex items-center gap-2 ${className}`}>
        <FileText size={16} />
        <span>No documents matched — response based on general knowledge</span>
      </div>
    )
  }

  return (
    <div className={`mt-4 space-y-2 ${className}`}>
      <div className="text-xs font-semibold text-gray-600 uppercase">Sources</div>
      <div className="space-y-1">
        {sources.map((source, idx) => {
          const isExpanded = expandedIndices.has(idx)
          const scorePercent = Math.round((source.relevance_score || 0) * 100)

          return (
            <div key={`${source.document_id}-${source.chunk_index}`} className="space-y-1">
              <button
                onClick={() => toggleExpanded(idx)}
                className="w-full text-left group flex items-start gap-2 px-2 py-2 bg-gray-50 hover:bg-blue-50 rounded border border-gray-200 hover:border-blue-300 transition-colors"
              >
                <div className="mt-0.5">
                  {isExpanded ? (
                    <ChevronUp size={16} className="text-gray-500 group-hover:text-blue-600" />
                  ) : (
                    <ChevronDown size={16} className="text-gray-500 group-hover:text-blue-600" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-gray-900 truncate group-hover:text-blue-700">
                    <FileText size={14} className="inline mr-1 -mt-0.5" />
                    {source.document_title}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    Chunk {source.chunk_index + 1} · {scorePercent}% relevance
                  </div>
                </div>
              </button>

              {isExpanded && (
                <div className="ml-4 px-3 py-2 bg-blue-50 rounded border border-blue-200 text-xs leading-relaxed text-gray-700">
                  <p className="italic">&ldquo;{source.chunk_preview}&rdquo;</p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
