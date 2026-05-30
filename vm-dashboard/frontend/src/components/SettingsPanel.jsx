import { useEffect, useState } from 'react'
import { Save, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { api } from '../api'

export default function SettingsPanel() {
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.getSettings().then(setForm).catch(() => {})
  }, [])

  function set(key, val) {
    setForm(f => ({ ...f, [key]: val }))
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setSaved(false)
    try {
      await api.updateSettings(form)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      alert(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleTest() {
    setTesting(true)
    setTestResult(null)
    try {
      await api.updateSettings(form)
      const result = await api.testConnection()
      setTestResult(result)
    } catch (err) {
      setTestResult({ ok: false, message: err.message })
    } finally {
      setTesting(false)
    }
  }

  if (!form) {
    return (
      <div className="flex items-center justify-center py-20 text-gray-500">
        <Loader2 className="animate-spin mr-2" size={20} /> Loading settings...
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-xl font-bold text-white">Settings</h1>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Active hypervisor */}
        <section className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Active Hypervisor</h2>
          <div className="flex gap-4">
            {['esxi', 'proxmox'].map(h => (
              <label key={h} className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="hypervisor" checked={form.active_hypervisor === h}
                  onChange={() => set('active_hypervisor', h)} />
                <span className="text-sm text-gray-300">{h === 'esxi' ? 'ESXi / vCenter' : 'Proxmox VE'}</span>
              </label>
            ))}
          </div>
        </section>

        {/* ESXi */}
        <section className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">ESXi / vCenter</h2>
          <F label="Host / IP"><input value={form.esxi_host} onChange={e => set('esxi_host', e.target.value)}
            placeholder="vcenter.example.com" className="input" /></F>
          <div className="grid grid-cols-2 gap-3">
            <F label="Username"><input value={form.esxi_user} onChange={e => set('esxi_user', e.target.value)}
              placeholder="administrator@vsphere.local" className="input" /></F>
            <F label="Password"><input type="password" value={form.esxi_password}
              onChange={e => set('esxi_password', e.target.value)} className="input" /></F>
          </div>
          <Toggle label="Verify SSL certificate" checked={form.esxi_verify_ssl}
            onChange={v => set('esxi_verify_ssl', v)} />
        </section>

        {/* Proxmox */}
        <section className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Proxmox VE</h2>
          <F label="Host / IP"><input value={form.proxmox_host} onChange={e => set('proxmox_host', e.target.value)}
            placeholder="proxmox.example.com" className="input" /></F>
          <div className="grid grid-cols-2 gap-3">
            <F label="Username"><input value={form.proxmox_user} onChange={e => set('proxmox_user', e.target.value)}
              placeholder="root@pam" className="input" /></F>
            <F label="Password"><input type="password" value={form.proxmox_password}
              onChange={e => set('proxmox_password', e.target.value)} className="input" /></F>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <F label="API Token ID (optional)"><input value={form.proxmox_token_id}
              onChange={e => set('proxmox_token_id', e.target.value)} placeholder="mytoken" className="input" /></F>
            <F label="API Token Secret"><input type="password" value={form.proxmox_token_secret}
              onChange={e => set('proxmox_token_secret', e.target.value)} className="input" /></F>
          </div>
          <Toggle label="Verify SSL certificate" checked={form.proxmox_verify_ssl}
            onChange={v => set('proxmox_verify_ssl', v)} />
        </section>

        {/* Default SSH */}
        <section className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Default SSH Credentials</h2>
          <div className="grid grid-cols-2 gap-3">
            <F label="Username"><input value={form.default_ssh_user}
              onChange={e => set('default_ssh_user', e.target.value)} placeholder="root" className="input" /></F>
            <F label="Password"><input type="password" value={form.default_ssh_password}
              onChange={e => set('default_ssh_password', e.target.value)} className="input" /></F>
          </div>
          <F label="Path to private key (on server)">
            <input value={form.default_ssh_key_path}
              onChange={e => set('default_ssh_key_path', e.target.value)}
              placeholder="/root/.ssh/id_rsa" className="input" />
          </F>
        </section>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button type="submit" disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50">
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            Save
          </button>
          <button type="button" onClick={handleTest} disabled={testing}
            className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 disabled:opacity-50">
            {testing ? <Loader2 size={14} className="animate-spin" /> : null}
            Test Connection
          </button>
          {saved && <span className="text-sm text-green-400">✓ Saved</span>}
          {testResult && (
            <span className={`flex items-center gap-1 text-sm ${testResult.ok ? 'text-green-400' : 'text-red-400'}`}>
              {testResult.ok ? <CheckCircle size={14} /> : <XCircle size={14} />}
              {testResult.message}
            </span>
          )}
        </div>
      </form>

      <style>{`
        .input { @apply w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500; }
      `}</style>
    </div>
  )
}

function F({ label, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-400 mb-1">{label}</label>
      {children}
    </div>
  )
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)}
        className="w-4 h-4 rounded accent-blue-500" />
      <span className="text-sm text-gray-300">{label}</span>
    </label>
  )
}
