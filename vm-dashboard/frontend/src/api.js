const BASE = '/api'

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // VMs
  listVMs: () => request('GET', '/vms'),
  getVM: (id) => request('GET', `/vms/${encodeURIComponent(id)}`),
  createVM: (spec) => request('POST', '/vms', spec),
  deleteVM: (id) => request('DELETE', `/vms/${encodeURIComponent(id)}`),
  powerOn: (id) => request('POST', `/vms/${encodeURIComponent(id)}/power/on`),
  powerOff: (id) => request('POST', `/vms/${encodeURIComponent(id)}/power/off`),

  // Templates & Networks
  listTemplates: () => request('GET', '/vms/templates'),
  listNetworks: () => request('GET', '/vms/networks'),

  // Deployments
  startDeployment: (spec) => request('POST', '/deployments', spec),
  listDeployments: () => request('GET', '/deployments'),
  getDeployment: (id) => request('GET', `/deployments/${id}`),

  // Settings
  getSettings: () => request('GET', '/settings'),
  updateSettings: (s) => request('PUT', '/settings', s),
  testConnection: () => request('POST', '/settings/test'),
}

export function openLogSocket(deploymentId, onEntry, onDone, onError) {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host = window.location.host
  const ws = new WebSocket(`${protocol}://${host}/api/deployments/${deploymentId}/logs`)

  ws.onmessage = (ev) => {
    const data = JSON.parse(ev.data)
    if (data.done) {
      onDone?.()
    } else if (data.error) {
      onError?.(data.error)
    } else {
      onEntry(data)
    }
  }
  ws.onerror = () => onError?.('WebSocket error')
  ws.onclose = () => onDone?.()
  return ws
}
