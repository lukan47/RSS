import { useEffect, useState } from 'react'
import { RefreshCw, ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import { api } from '../api'
import LogConsole from './LogConsole'

const STATUS_BADGE = {
  pending:   'bg-gray-700 text-gray-300',
  running:   'bg-blue-900 text-blue-300',
  completed: 'bg-green-900 text-green-300',
  failed:    'bg-red-900 text-red-300',
}

export default function DeploymentHistory() {
  const [deployments, setDeployments] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)

  async function load() {
    setLoading(true)
    try {
      setDeployments(await api.listDeployments())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Deployment History</h1>
        <button onClick={load}
          className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300">
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-gray-500">
          <Loader2 className="animate-spin mr-2" size={20} /> Loading...
        </div>
      ) : deployments.length === 0 ? (
        <div className="text-center py-20 text-gray-500">No deployments yet.</div>
      ) : (
        <div className="space-y-2">
          {[...deployments].reverse().map(dep => (
            <div key={dep.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <button
                className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-gray-800 transition-colors"
                onClick={() => setExpanded(expanded === dep.id ? null : dep.id)}
              >
                {expanded === dep.id ? <ChevronDown size={14} className="text-gray-400 shrink-0" /> : <ChevronRight size={14} className="text-gray-400 shrink-0" />}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-white truncate">{dep.vm_name || dep.vm_id || dep.id}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[dep.status]}`}>
                      {dep.status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {new Date(dep.started_at).toLocaleString()}
                    {dep.completed_at && ` — ${Math.round((new Date(dep.completed_at) - new Date(dep.started_at)) / 1000)}s`}
                  </div>
                </div>
                <span className="text-xs text-gray-600 font-mono shrink-0">{dep.id}</span>
              </button>

              {expanded === dep.id && (
                <div className="px-5 pb-5">
                  <LogConsole
                    deploymentId={dep.status === 'running' ? dep.id : null}
                    logs={dep.logs}
                    onEntry={() => {}}
                    onDone={() => {}}
                  />
                  {dep.results?.raw_output && (
                    <div className="mt-3">
                      <h3 className="text-xs font-semibold text-gray-400 mb-1">Test Output</h3>
                      <pre className="bg-gray-950 border border-gray-800 rounded-lg p-3 text-xs text-gray-300 overflow-x-auto whitespace-pre-wrap">
                        {dep.results.raw_output}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
