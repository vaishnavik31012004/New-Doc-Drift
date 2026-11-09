import { useState, useEffect } from 'react'
import { GitPullRequest, Loader2, CheckCircle2 } from 'lucide-react'
import FindingCard from './FindingCard.jsx'
import { createPR } from '../api/client.js'

export default function FindingsPanel({ scan }) {
  const [selected, setSelected] = useState([])
  const [creating, setCreating] = useState(false)
  const [prUrl, setPrUrl] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setSelected([])
    setPrUrl(null)
    setError('')
  }, [scan?.id])

  if (!scan) return null

  const toggleSelect = (id) =>
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const handleCreatePR = async () => {
    setCreating(true)
    setError('')
    try {
      const res = await createPR(scan.id, selected)
      setPrUrl(res.pr_url)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to create pull request.')
    } finally {
      setCreating(false)
    }
  }

  if (scan.status !== 'completed') return null

  return (
    <div className="bg-panel border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-medium text-sm text-gray-300">
          {scan.findings.length === 0 ? 'No documentation drift found' : `Drift findings (${scan.findings.length})`}
        </h2>
        {scan.findings.length > 0 && (
          <button
            disabled={selected.length === 0 || creating}
            onClick={handleCreatePR}
            className="text-xs flex items-center gap-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 rounded-md px-3 py-1.5 disabled:opacity-40"
          >
            {creating ? <Loader2 size={12} className="animate-spin" /> : <GitPullRequest size={12} />}
            Create PR ({selected.length})
          </button>
        )}
      </div>

      {scan.findings.length === 0 && (
        <p className="text-sm text-gray-500">
          This commit doesn't look like it requires a documentation update.
        </p>
      )}

      <div className="space-y-2">
        {scan.findings.map(f => (
          <FindingCard key={f.id} finding={f} selected={selected.includes(f.id)} onToggleSelect={toggleSelect} />
        ))}
      </div>

      {prUrl && (
        <div className="mt-3 flex items-center gap-2 text-sm text-emerald-400">
          <CheckCircle2 size={14} />
          Pull request created:{' '}
          <a href={prUrl} target="_blank" rel="noreferrer" className="underline">{prUrl}</a>
        </div>
      )}
      {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
    </div>
  )
}
