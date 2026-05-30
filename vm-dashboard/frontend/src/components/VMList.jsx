import { useEffect, useState, useCallback } from 'react'
import { RefreshCw, Plus, Power, PowerOff, Trash2, Loader2 } from 'lucide-react'
import { api } from '../api'
import CreateVMModal from './CreateVMModal'

const STATE_BADGE = {
  on:        'bg-green-900 text-green-300',
  off:       'bg-gray-700 text-gray-300',
  suspended: 'bg-yellow-900 text-yellow-300',
  unknown:   'bg-gray-800 text-gray-400',
}

const OS_ICON = {
  rhel:    '🎩',
  centos:  '🎩',
  ubuntu:  '🟠',
  debian:  '🌀',
  windows: '🪟',
  unknown: '❓',
}

export default function VMList() {
  const [vms, setVMs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState({})
  const [showCreate, setShowCreate] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setVMs(await api.listVMs())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function act(id, fn, label) {
    setBusy(b => ({ ...b, [id]: label }))
    try {
      await fn()
      await load()
    } catch (e) {
      alert(e.message)
    } finally {
      setBusy(b => { const n = { ...b }; delete n[id]; return n })
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Virtual Machines</h1>
        <div className="flex gap-2">
          <button
            onClick={load}
            className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-500 text-white"
          >
            <Plus size={14} />
            New VM
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-950 border border-red-800 text-red-300 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20 text-gray-500">
          <Loader2 className="animate-spin mr-2" size={20} /> Loading VMs...
        </div>
      ) : vms.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          No VMs found. Configure your hypervisor in Settings, then create one.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-800 bg-gray-900">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">State</th>
                <th className="px-4 py-3 font-medium">IP Address</th>
                <th className="px-4 py-3 font-medium">OS</th>
                <th className="px-4 py-3 font-medium">CPU</th>
                <th className="px-4 py-3 font-medium">RAM</th>
                <th className="px-4 py-3 font-medium">Hypervisor</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {vms.map(vm => {
                const isBusy = !!busy[vm.id]
                return (
                  <tr key={vm.id} className="hover:bg-gray-900 transition-colors">
                    <td className="px-4 py-3 font-mono text-white">{vm.name}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATE_BADGE[vm.power_state] || STATE_BADGE.unknown}`}>
                        {vm.power_state}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 font-mono text-xs">{vm.ip_address || '—'}</td>
                    <td className="px-4 py-3 text-gray-400">
                      {OS_ICON[vm.os_type] || '❓'} {vm.os_type || vm.guest_os || '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-400">{vm.cpu_count || '—'}</td>
                    <td className="px-4 py-3 text-gray-400">
                      {vm.memory_mb ? `${(vm.memory_mb / 1024).toFixed(1)} GB` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300">{vm.hypervisor}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        {isBusy ? (
                          <Loader2 size={14} className="animate-spin text-gray-400" />
                        ) : (
                          <>
                            {vm.power_state === 'off' || vm.power_state === 'unknown' ? (
                              <button
                                title="Power On"
                                onClick={() => act(vm.id, () => api.powerOn(vm.id), 'on')}
                                className="p-1 rounded hover:bg-green-900 text-green-400"
                              >
                                <Power size={14} />
                              </button>
                            ) : (
                              <button
                                title="Power Off"
                                onClick={() => act(vm.id, () => api.powerOff(vm.id), 'off')}
                                className="p-1 rounded hover:bg-yellow-900 text-yellow-400"
                              >
                                <PowerOff size={14} />
                              </button>
                            )}
                            <button
                              title="Delete"
                              onClick={() => {
                                if (confirm(`Delete ${vm.name}?`))
                                  act(vm.id, () => api.deleteVM(vm.id), 'del')
                              }}
                              className="p-1 rounded hover:bg-red-900 text-red-400"
                            >
                              <Trash2 size={14} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && <CreateVMModal onClose={() => setShowCreate(false)} onCreated={load} />}
    </div>
  )
}
