import { ShieldCheck } from 'lucide-react'

export default function Navbar() {
  return (
    <header className="border-b border-border bg-panel/60 backdrop-blur sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
        <ShieldCheck className="text-accent" size={26} />
        <div>
          <h1 className="text-lg font-semibold leading-none">Doc-Drift Guardian</h1>
          <p className="text-xs text-gray-400 mt-1">
            Multi-agent documentation drift detection, powered by Google ADK
          </p>
        </div>
      </div>
    </header>
  )
}
