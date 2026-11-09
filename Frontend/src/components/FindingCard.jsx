import { useState } from 'react'
import { FileWarning, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const SEVERITY_STYLES = {
  high: 'bg-red-500/15 text-red-300 border-red-500/30',
  medium: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  low: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
}

export default function FindingCard({ finding, selected, onToggleSelect }) {
  const [expanded, setExpanded] = useState(false)
  const sevClass = SEVERITY_STYLES[finding.severity] || SEVERITY_STYLES.medium

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <div className="flex items-start gap-3 p-3">
        {!finding.pr_url && (
          <input
            type="checkbox"
            checked={selected}
            onChange={() => onToggleSelect(finding.id)}
            className="mt-1 accent-accent"
          />
        )}
        <FileWarning size={16} className="text-gray-500 mt-0.5 shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium">{finding.doc_path}</p>
            <span className={`text-[10px] uppercase tracking-wide border rounded-full px-2 py-0.5 ${sevClass}`}>
              {finding.severity}
            </span>
            {finding.pr_url && (
              <a
                href={finding.pr_url}
                target="_blank"
                rel="noreferrer"
                className="text-[10px] flex items-center gap-1 text-emerald-400 hover:underline"
              >
                PR opened <ExternalLink size={10} />
              </a>
            )}
          </div>
          <p className="text-xs text-gray-400 mt-1">{finding.summary}</p>

          {finding.suggested_patch && (
            <button
              onClick={() => setExpanded(v => !v)}
              className="text-xs text-accent hover:text-indigo-400 flex items-center gap-1 mt-2"
            >
              {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              {expanded ? 'Hide suggested patch' : 'View suggested patch'}
            </button>
          )}
        </div>
      </div>
      {expanded && finding.suggested_patch && (
        <div className="border-t border-border bg-surface px-4 py-3 text-sm prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{finding.suggested_patch}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}
