import { useEffect, useRef, useState, useCallback } from 'react'
import RepoPanel from '../components/RepoPanel.jsx'
import CommitPicker from '../components/CommitPicker.jsx'
import ScanProgress from '../components/ScanProgress.jsx'
import FindingsPanel from '../components/FindingsPanel.jsx'
import ScanHistory from '../components/ScanHistory.jsx'
import {
  listRepos, connectRepo, deleteRepo, listCommits,
  createScan, listScans, getScan, scanSocketUrl,
} from '../api/client.js'

export default function Dashboard() {
  const [repos, setRepos] = useState([])
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [commits, setCommits] = useState([])
  const [loadingCommits, setLoadingCommits] = useState(false)

  const [scans, setScans] = useState([])
  const [activeScan, setActiveScan] = useState(null)
  const [agentStates, setAgentStates] = useState({})
  const [scanning, setScanning] = useState(false)

  const wsRef = useRef(null)

  const refreshRepos = useCallback(async () => {
    setRepos(await listRepos())
  }, [])

  useEffect(() => { refreshRepos() }, [refreshRepos])

  const handleSelectRepo = async (repo) => {
    setSelectedRepo(repo)
    setActiveScan(null)
    setAgentStates({})
    setLoadingCommits(true)
    try {
      const [commitList, scanList] = await Promise.all([
        listCommits(repo.id),
        listScans(repo.id),
      ])
      setCommits(commitList)
      setScans(scanList)
    } finally {
      setLoadingCommits(false)
    }
  }

  const handleConnect = async (owner, name, token) => {
    const repo = await connectRepo(owner, name, token)
    await refreshRepos()
    await handleSelectRepo(repo)
  }

  const handleDeleteRepo = async (id) => {
    await deleteRepo(id)
    if (selectedRepo?.id === id) {
      setSelectedRepo(null); setCommits([]); setScans([]); setActiveScan(null)
    }
    await refreshRepos()
  }

  const connectSocket = (scanId) => {
    if (wsRef.current) wsRef.current.close()
    const ws = new WebSocket(scanSocketUrl(scanId))
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data)
      if (msg.type === 'agent_progress') {
        setAgentStates(prev => ({ ...prev, [msg.agent]: msg.status }))
      }
      if (msg.type === 'status') {
  if (msg.status === 'completed' || msg.status === 'failed') {
    getScan(scanId).then((updatedScan) => {
      setActiveScan(updatedScan)

      setScans(prev =>
        prev.map(scan =>
          scan.id === scanId ? updatedScan : scan
        )
      )
    })

    setScanning(false)
  }
}
    }
    wsRef.current = ws
  }

  const handleScan = async (commitSha) => {
    setScanning(true)
    setAgentStates({})
    const scan = await createScan(selectedRepo.id, commitSha)
    setActiveScan(scan)
    connectSocket(scan.id)
    setScans(prev => [scan, ...prev])
  }

  const handleSelectHistoryScan = async (scanId) => {
    const scan = await getScan(scanId)
    setActiveScan(scan)
    setAgentStates({})
    setScanning(false)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-1 space-y-4">
        <RepoPanel
          repos={repos}
          selectedRepo={selectedRepo}
          onSelect={handleSelectRepo}
          onConnect={handleConnect}
          onDelete={handleDeleteRepo}
        />
        {selectedRepo && (
          <CommitPicker
            commits={commits}
            loadingCommits={loadingCommits}
            onScan={handleScan}
            scanning={scanning}
          />
        )}
        {selectedRepo && scans.length > 0 && (
          <ScanHistory scans={scans} activeScanId={activeScan?.id} onSelect={handleSelectHistoryScan} />
        )}
      </div>

      <div className="lg:col-span-2 space-y-4">
        {!selectedRepo && (
          <div className="bg-panel border border-border rounded-xl p-10 text-center text-gray-500 text-sm">
            Connect a GitHub repository to get started, then pick a commit to scan for documentation drift.
          </div>
        )}
        {activeScan && (
          <>
            <ScanProgress
              scanStatus={activeScan.status}
              agentStates={agentStates}
              error={activeScan.status === 'failed' ? activeScan.error_message : null}
            />
            <FindingsPanel scan={activeScan} />
          </>
        )}
      </div>
    </div>
  )
}
