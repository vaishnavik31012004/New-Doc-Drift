import { CheckCircle2, Loader2, Circle, XCircle } from 'lucide-react'

const STAGES = [
  { key: 'diff_analyzer', label: 'Diff Analyzer', hint: 'Understanding what the commit actually changed' },
  { key: 'doc_matcher', label: 'Doc Matcher', hint: 'Cross-referencing the change against your docs (RAG)' },
  { key: 'patch_writer', label: 'Patch Writer', hint: 'Drafting the corrected documentation' },
]

export default function ScanProgress({ scanStatus, agentStates, error }) {
  if (!scanStatus) return null

  return (
    <div className="bg-panel border border-border rounded-xl p-4">
      <h2 className="font-medium text-sm text-gray-300 mb-3">Agent pipeline</h2>
      <div className="space-y-3">
        {STAGES.map((stage, i) => {
          const state = agentStates[stage.key] || (scanStatus === 'failed' ? 'idle' : 'idle')
          const isDone = state === 'done'
          const isRunning = state === 'running'
          return (
            <div key={stage.key} className="flex items-start gap-3">
              <div className="mt-0.5">
                {error && !isDone ? (
                  <XCircle size={18} className="text-red-400" />
                ) : isDone ? (
                  <CheckCircle2 size={18} className="text-emerald-400" />
                ) : isRunning ? (
                  <Loader2 size={18} className="text-accent animate-spin" />
                ) : (
                  <Circle size={18} className="text-gray-600" />
                )}
              </div>
              <div>
                <p className={`text-sm ${isDone ? 'text-gray-200' : isRunning ? 'text-white font-medium' : 'text-gray-500'}`}>
                  {stage.label}
                </p>
                <p className="text-xs text-gray-500">{stage.hint}</p>
              </div>
            </div>
          )
        })}
      </div>
      {error && (
        <p className="text-xs text-red-400 mt-3 border-t border-border pt-3">{error}</p>
      )}
    </div>
  )
}
