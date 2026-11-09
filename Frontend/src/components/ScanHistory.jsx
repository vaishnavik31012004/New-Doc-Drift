import { formatDistanceToNow } from 'date-fns'
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'

const STATUS_ICON = {
  completed: <CheckCircle2 size={14} className="text-emerald-400" />,
  failed: <XCircle size={14} className="text-red-400" />,
}

export default function ScanHistory({ scans, activeScanId, onSelect }) {
  if (!scans || scans.length === 0) return null

  return (
    <div className="bg-panel border border-border rounded-xl p-4">
      <h2 className="font-medium text-sm text-gray-300 mb-3">Scan history</h2>
      <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
        {scans.map(s => (
          <div
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`flex items-center justify-between rounded-lg px-3 py-2 cursor-pointer border text-sm ${
              activeScanId === s.id ? 'border-accent bg-accent/10' : 'border-transparent hover:border-border hover:bg-surface'
            }`}
          >
            <div className="flex items-center gap-2 min-w-0">
              {STATUS_ICON[s.status] || <Loader2 size={14} className="text-accent animate-spin" />}
              <span className="truncate">{s.commit_message || s.commit_sha.slice(0, 7)}</span>
            </div>
            <span className="text-xs text-gray-500 shrink-0 ml-2">
              {formatDistanceToNow(new Date(s.created_at), { addSuffix: true })}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
