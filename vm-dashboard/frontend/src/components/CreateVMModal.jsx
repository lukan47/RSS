import { useEffect, useState } from 'react'
import { X, Loader2 } from 'lucide-react'
import { api } from '../api'

const HYPERVISORS = ['esxi', 'proxmox']

export default function CreateVMModal({ onClose, onCreated }) {
  const [templates, setTemplates] = useState([])
  const [networks, setNetworks] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({
    name: '',
    template_id: '',
    cpu_count: 2,
    memory_mb: 4096,
    storage_gb: 40,
    network_id: '',
    hypervisor: 'esxi',
    node: '',
  })

  useEffect(() => {
    Promise.all([api.listTemplates(), api.listNetworks()])
      .then(([t, n]) => { setTemplates(t); setNetworks(n) })
      .catch(() => {})
  }, [])

  function set(key, val) {
    setForm(f => ({ ...f, [key]: val }))
  }

  async function submit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await api.createVM(form)
      onCreated?.()
      onClose()
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-white">Create Virtual Machine</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X size={18} /></button>
        </div>

        <form onSubmit={submit} className="px-6 py-5 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-950 border border-red-800 text-red-300 text-sm">{error}</div>
          )}

          <Field label="VM Name">
            <input
              required
              value={form.name}
              onChange={e => set('name', e.target.value)}
              placeholder="my-test-vm"
              className="input"
            />
          </Field>

          <Field label="Hypervisor">
            <select value={form.hypervisor} onChange={e => set('hypervisor', e.target.value)} className="input">
              {HYPERVISORS.map(h => <option key={h} value={h}>{h}</option>)}
            </select>
          </Field>

          {form.hypervisor === 'proxmox' && (
            <Field label="Node (Proxmox)">
              <input
                value={form.node}
                onChange={e => set('node', e.target.value)}
                placeholder="pve"
                className="input"
              />
            </Field>
          )}

          <Field label="Template">
            <select value={form.template_id} onChange={e => set('template_id', e.target.value)} className="input">
              <option value="">— select template —</option>
              {templates.map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </Field>

          <div className="grid grid-cols-3 gap-3">
            <Field label="CPUs">
              <input type="number" min={1} max={64} value={form.cpu_count}
                onChange={e => set('cpu_count', +e.target.value)} className="input" />
            </Field>
            <Field label="RAM (MB)">
              <input type="number" min={512} step={512} value={form.memory_mb}
                onChange={e => set('memory_mb', +e.target.value)} className="input" />
            </Field>
            <Field label="Disk (GB)">
              <input type="number" min={10} value={form.storage_gb}
                onChange={e => set('storage_gb', +e.target.value)} className="input" />
            </Field>
          </div>

          <Field label="Network">
            <select value={form.network_id} onChange={e => set('network_id', e.target.value)} className="input">
              <option value="">— default —</option>
              {networks.map(n => (
                <option key={n.id} value={n.id}>{n.name}</option>
              ))}
            </select>
          </Field>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="px-4 py-2 text-sm rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300">
              Cancel
            </button>
            <button type="submit" disabled={loading}
              className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50">
              {loading && <Loader2 size={14} className="animate-spin" />}
              Create VM
            </button>
          </div>
        </form>
      </div>

      <style>{`.input { @apply w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500; }`}</style>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-400 mb-1">{label}</label>
      {children}
    </div>
  )
}
