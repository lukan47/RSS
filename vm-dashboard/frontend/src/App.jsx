import { useState } from 'react'
import Sidebar from './components/Sidebar'
import VMList from './components/VMList'
import DeployPanel from './components/DeployPanel'
import SettingsPanel from './components/SettingsPanel'
import DeploymentHistory from './components/DeploymentHistory'

const VIEWS = {
  vms: VMList,
  deploy: DeployPanel,
  history: DeploymentHistory,
  settings: SettingsPanel,
}

export default function App() {
  const [view, setView] = useState('vms')
  const View = VIEWS[view] || VMList

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      <Sidebar current={view} onNavigate={setView} />
      <main className="flex-1 overflow-auto p-6">
        <View />
      </main>
    </div>
  )
}
