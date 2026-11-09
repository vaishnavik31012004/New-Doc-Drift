import { GitCommitHorizontal, Play, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function CommitPicker({ commits, loadingCommits, onScan, scanning }) {
  if (loadingCommits) {
    return (
      <div className="bg-panel border border-border rounded-xl p-6 flex items-center justify-center text-gray-500 text-sm">
        <Loader2 size={16} className="animate-spin mr-2" /> Loading commits…
      </div>
    )
  }

  if (!commits || commits.length === 0) {
    return (
      <div className="bg-panel border border-border rounded-xl p-6 text-sm text-gray-500">
        No commits found for this repository.
      </div>
    )
  }

  return (
    <div className="bg-panel border border-border rounded-xl p-4">
      <h2 className="font-medium text-sm text-gray-300 mb-3">Recent commits</h2>
      <div className="space-y-1 max-h-80 overflow-y-auto pr-1">
        {commits.map(c => (
          <div
            key={c.sha}
            className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-surface border border-transparent hover:border-border"
          >
            <div className="min-w-0 flex items-start gap-2">
              <GitCommitHorizontal size={14} className="text-gray-500 mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-sm truncate">{c.message}</p>
                <p className="text-xs text-gray-500">
                  {c.short_sha} · {c.author || 'unknown'}
                  {c.date && <> · {formatDistanceToNow(new Date(c.date), { addSuffix: true })}</>}
                  {' '}· {c.files_changed} file(s)
                </p>
              </div>
            </div>
            <button
              disabled={scanning}
              onClick={() => onScan(c.sha)}
              className="shrink-0 ml-2 text-xs flex items-center gap-1 bg-accent/20 hover:bg-accent/30 text-indigo-300 rounded-md px-2 py-1 disabled:opacity-40"
            >
              <Play size={12} /> Scan
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
