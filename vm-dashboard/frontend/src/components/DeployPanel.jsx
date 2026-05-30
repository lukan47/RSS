import { useEffect, useState } from 'react'
import { Rocket, Loader2 } from 'lucide-react'
import { api } from '../api'
import LogConsole from './LogConsole'

const OS_TYPES = ['', 'rhel', 'centos', 'ubuntu', 'debian', 'windows', 'unknown']

export default function DeployPanel() {
  const [vms, setVMs] = useState([])
  const [templates, setTemplates] = useState([])
  const [networks, setNetworks] = useState([])
  const [settings, setSettings] = useState(null)

  const [mode, setMode] = useState('existing') // 'existing' | 'create'
  const [vmId, setVmId] = useState('')

  // VM creation fields
  const [vmName, setVmName] = useState('')
  const [templateId, setTemplateId] = useState('')
  const [cpuCount, setCpuCount] = useState(2)
  const [memoryMb, setMemoryMb] = useState(4096)
  const [storageGb, setStorageGb] = useState(40)
  const [networkId, setNetworkId] = useState('')
  const [hypervisor, setHypervisor] = useState('esxi')
  const [node, setNode] = useState('')

  // SSH
  const [sshUser, setSshUser] = useState('root')
  const [sshPassword, setSshPassword] = useState('')
  const [sshKey, setSshKey] = useState('')
  const [sshPort, setSshPort] = useState(22)

  // Deploy options
  const [osOverride, setOsOverride] = useState('')
  const [runPrep, setRunPrep] = useState(true)
  const [runTest, setRunTest] = useState(true)

  // Pipeline state
  const [deploying, setDeploying] = useState(false)
  const [deploymentId, setDeploymentId] = useState(null)
  const [logs, setLogs] = useState([])
  const [done, setDone] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.listVMs().then(setVMs).catch(() => {})
    api.listTemplates().then(setTemplates).catch(() => {})
    api.listNetworks().then(setNetworks).catch(() => {})
    api.getSettings().then(s => {
      setSettings(s)
      setSshUser(s.default_ssh_user || 'root')
      setSshPassword(s.default_ssh_password || '')
      setHypervisor(s.active_hypervisor || 'esxi')
    }).catch(() => {})
  }, [])

  async function handleDeploy(e) {
    e.preventDefault()
    setError(null)
    setLogs([])
    setDone(false)
    setDeploymentId(null)
    setDeploying(true)

    try {
      const spec = {
        ssh_credentials: {
          username: sshUser,
          password: sshPassword || null,
          private_key: sshKey || null,
          port: sshPort,
        },
        os_type: osOverride || null,
        run_prep: runPrep,
        run_perf_test: runTest,
      }

      if (mode === 'existing') {
        spec.vm_id = vmId
      } else {
        spec.vm_create_spec = {
          name: vmName,
          template_id: templateId,
          cpu_count: cpuCount,
          memory_mb: memoryMb,
          storage_gb: storageGb,
          network_id: networkId || null,
          hypervisor,
          node: node || null,
        }
      }

      const dep = await api.startDeployment(spec)
      setDeploymentId(dep.id)
    } catch (err) {
      setError(err.message)
      setDeploying(false)
    }
  }

  function handleEntry(entry) {
    setLogs(l => [...l, entry])
  }

  function handleDone() {
    setDeploying(false)
    setDone(true)
  }

  return (
    <div className="max-w-3xl space-y-6">
      <h1 className="text-xl font-bold text-white">Deploy & Prep VM</h1>

      <form onSubmit={handleDeploy} className="space-y-5">
        {/* Target VM */}
        <section className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Target VM</h2>

          <div className="flex gap-4">
            {['existing', 'create'].map(m => (
              <label key={m} className="flex items-center gap-2 cursor-pointer">
                <input type="radio" checked={mode === m} onChange={() => setMode(m)} />
                <span className="text-sm text-gray-300">{m === 'existing' ? 'Use existing VM' : 'Create new VM'}</span>
              </label>
            ))}
          </div>

          {mode === 'existing' ? (
            <div>
              <label className="field-label">Virtual Machine</label>
              <select required value={vmId} onChange={e => setVmId(e.target.value)} className="input">
                <option value="">— select VM —</option>
                {vms.map(v => (
                  <option key={v.id} value={v.id}>{v.name} ({v.power_state})</option>
                ))}
              </select>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="field-label">VM Name</label>
                  <input required value={vmName} onChange={e => setVmName(e.target.value)}
                    placeholder="perf-test-01" className="input" />
                </div>
                <div>
                  <label className="field-label">Hypervisor</label>
                  <select value={hypervisor} onChange={e => setHypervisor(e.target.value)} className="input">
                    <option value="esxi">ESXi / vCenter</option>
                    <option value="proxmox">Proxmox</option>
                  </select>
                </div>
              </div>
              {hypervisor === 'proxmox' && (
                <div>
                  <label className="field-label">Proxmox Node</label>
                  <input value={node} onChange={e => setNode(e.target.value)} placeholder="pve" className="input" />
                </div>
              )}
              <div>
                <label className="field-label">Template</label>
                <select required value={templateId} onChange={e => setTemplateId(e.target.value)} className="input">
                  <option value="">— select template —</option>
                  {templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="field-label">CPUs</label>
                  <input type="number" min={1} max={64} value={cpuCount}
                    onChange={e => setCpuCount(+e.target.value)} className="input" />
                </div>
                <div>
                  <label className="field-label">RAM (MB)</label>
                  <input type="number" min={512} step={512} value={memoryMb}
                    onChange={e => setMemoryMb(+e.target.value)} className="input" />
                </div>
                <div>
                  <label className="field-label">Disk (GB)</label>
                  <input type="number" min={10} value={storageGb}
                    onChange={e => setStorageGb(+e.target.value)} className="input" />
                </div>
              </div>
              <div>
                <label className="field-label">Network</label>
                <select value={networkId} onChange={e => setNetworkId(e.target.value)} className="input">
                  <option value="">— default —</option>
                  {networks.map(n => <option key={n.id} value={n.id}>{n.name}</option>)}
                </select>
              </div>
            </div>
          )}
        </section>

        {/* SSH Credentials */}
        <section className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">SSH Credentials</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="field-label">Username</label>
              <input required value={sshUser} onChange={e => setSshUser(e.target.value)}
                placeholder="root" className="input" />
            </div>
            <div>
              <label className="field-label">Port</label>
              <input type="number" value={sshPort} onChange={e => setSshPort(+e.target.value)}
                className="input" />
            </div>
          </div>
          <div>
            <label className="field-label">Password (leave blank if using key)</label>
            <input type="password" value={sshPassword} onChange={e => setSshPassword(e.target.value)}
              placeholder="••••••••" className="input" />
          </div>
          <div>
            <label className="field-label">Private Key (PEM, optional)</label>
            <textarea value={sshKey} onChange={e => setSshKey(e.target.value)}
              rows={3} placeholder="-----BEGIN OPENSSH PRIVATE KEY-----"
              className="input font-mono text-xs resize-none" />
          </div>
        </section>

        {/* Pipeline Options */}
        <section className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Pipeline Options</h2>
          <div>
            <label className="field-label">OS Override (auto-detect if blank)</label>
            <select value={osOverride} onChange={e => setOsOverride(e.target.value)} className="input">
              {OS_TYPES.map(t => <option key={t} value={t}>{t || '— auto-detect —'}</option>)}
            </select>
          </div>
          <div className="flex gap-6">
            <Toggle checked={runPrep} onChange={setRunPrep} label="Run prep script" />
            <Toggle checked={runTest} onChange={setRunTest} label="Run perf test" />
          </div>
        </section>

        {error && (
          <div className="p-3 rounded-lg bg-red-950 border border-red-800 text-red-300 text-sm">{error}</div>
        )}

        <button
          type="submit"
          disabled={deploying}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium disabled:opacity-50 transition-colors"
        >
          {deploying ? <Loader2 size={16} className="animate-spin" /> : <Rocket size={16} />}
          {deploying ? 'Deploying...' : 'Deploy & Prep'}
        </button>
      </form>

      {/* Log console */}
      {(deploymentId || logs.length > 0) && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-semibold text-gray-300">Deployment Log</h2>
            {done && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-green-900 text-green-300">Complete</span>
            )}
          </div>
          <LogConsole
            deploymentId={deploymentId}
            logs={logs}
            onEntry={handleEntry}
            onDone={handleDone}
          />
        </div>
      )}

      <style>{`
        .input { @apply w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500; }
        .field-label { @apply block text-xs font-medium text-gray-400 mb-1; }
      `}</style>
    </div>
  )
}

function Toggle({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)}
        className="w-4 h-4 rounded accent-blue-500" />
      <span className="text-sm text-gray-300">{label}</span>
    </label>
  )
}
