import { useEffect, useRef } from 'react'
import { openLogSocket } from '../api'

const LEVEL_COLOR = {
  info:    'text-gray-300',
  warning: 'text-yellow-400',
  error:   'text-red-400',
  success: 'text-green-400',
}

export default function LogConsole({ deploymentId, logs, onEntry, onDone }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    if (!deploymentId) return
    const ws = openLogSocket(deploymentId, onEntry, onDone, (err) => {
      onEntry?.({ level: 'error', message: err, timestamp: new Date().toISOString() })
    })
    return () => ws.close()
  }, [deploymentId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div className="bg-gray-950 border border-gray-800 rounded-xl p-4 font-mono text-xs h-80 overflow-y-auto">
      {logs.length === 0 ? (
        <span className="text-gray-600">Waiting for output...</span>
      ) : (
        logs.map((entry, i) => (
          <div key={i} className="flex gap-2 leading-5">
            <span className="text-gray-600 shrink-0">
              {new Date(entry.timestamp).toLocaleTimeString()}
            </span>
            <span className={LEVEL_COLOR[entry.level] || 'text-gray-300'}>
              {entry.message}
            </span>
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  )
}
