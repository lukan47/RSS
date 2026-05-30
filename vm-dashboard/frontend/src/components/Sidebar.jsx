import { Server, Rocket, History, Settings } from 'lucide-react'

const NAV = [
  { key: 'vms', label: 'VMs', icon: Server },
  { key: 'deploy', label: 'Deploy', icon: Rocket },
  { key: 'history', label: 'History', icon: History },
  { key: 'settings', label: 'Settings', icon: Settings },
]

export default function Sidebar({ current, onNavigate }) {
  return (
    <aside className="w-56 flex flex-col bg-gray-900 border-r border-gray-800">
      <div className="px-5 py-4 border-b border-gray-800">
        <span className="text-lg font-semibold text-white">VM Dashboard</span>
      </div>
      <nav className="flex-1 py-3 space-y-1 px-2">
        {NAV.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => onNavigate(key)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
              ${current === key
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
