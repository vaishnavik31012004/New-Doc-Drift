import { useState } from 'react'
import { Plus, Trash2, Github, Loader2 } from 'lucide-react'

export default function RepoPanel({ repos, selectedRepo, onSelect, onConnect, onDelete, loading }) {
  const [owner, setOwner] = useState('')
  const [name, setName] = useState('')
  const [token, setToken] = useState('')
  const [showForm, setShowForm] = useState(repos.length === 0)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!owner.trim() || !name.trim()) return
    setSubmitting(true)
    setError('')
    try {
      await onConnect(owner.trim(), name.trim(), token.trim())
      setOwner(''); setName(''); setToken('')
      setShowForm(false)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not connect to that repository.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-panel border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-medium text-sm text-gray-300">Repositories</h2>
        <button
          onClick={() => setShowForm(v => !v)}
          className="text-xs flex items-center gap-1 text-accent hover:text-indigo-400"
        >
          <Plus size={14} /> Connect
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mb-4 space-y-2">
          <div className="flex gap-2">
            <input
              className="w-1/2 bg-surface border border-border rounded-lg px-2 py-1.5 text-sm outline-none focus:border-accent"
              placeholder="owner"
              value={owner}
              onChange={e => setOwner(e.target.value)}
            />
            <input
              className="w-1/2 bg-surface border border-border rounded-lg px-2 py-1.5 text-sm outline-none focus:border-accent"
              placeholder="repo name"
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </div>
          <input
            className="w-full bg-surface border border-border rounded-lg px-2 py-1.5 text-sm outline-none focus:border-accent"
            placeholder="GitHub token (optional if set in backend .env)"
            type="password"
            value={token}
            onChange={e => setToken(e.target.value)}
          />
          {error && <p className="text-xs text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-accent hover:bg-indigo-500 disabled:opacity-50 rounded-lg py-1.5 text-sm font-medium flex items-center justify-center gap-2"
          >
            {submitting ? <Loader2 size={14} className="animate-spin" /> : <Github size={14} />}
            Connect repository
          </button>
        </form>
      )}

      <div className="space-y-1.5">
        {repos.length === 0 && !showForm && (
          <p className="text-xs text-gray-500">No repositories connected yet.</p>
        )}
        {repos.map(repo => (
          <div
            key={repo.id}
            onClick={() => onSelect(repo)}
            className={`group flex items-center justify-between rounded-lg px-3 py-2 cursor-pointer border transition ${
              selectedRepo?.id === repo.id
                ? 'border-accent bg-accent/10'
                : 'border-transparent hover:border-border hover:bg-surface'
            }`}
          >
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{repo.full_name}</p>
              {repo.description && (
                <p className="text-xs text-gray-500 truncate">{repo.description}</p>
              )}
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(repo.id) }}
              className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 shrink-0 ml-2"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
