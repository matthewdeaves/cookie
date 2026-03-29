import type { LucideIcon } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface TabConfig<T extends string> {
  id: T
  label: string
  icon: LucideIcon
  visible: boolean
  variant?: 'default' | 'destructive'
}

interface SettingsTabNavProps<T extends string> {
  tabs: TabConfig<T>[]
  activeTab: T
  onTabChange: (tab: T) => void
}

export default function SettingsTabNav<T extends string>({
  tabs,
  activeTab,
  onTabChange,
}: SettingsTabNavProps<T>) {
  return (
    <div className="border-b border-border px-4">
      <div className="mx-auto max-w-4xl">
        <div className="flex gap-4 overflow-x-auto">
          {tabs.filter((tab) => tab.visible).map((tab) => (
            <TabButton
              key={tab.id}
              tab={tab}
              isActive={activeTab === tab.id}
              onClick={() => onTabChange(tab.id)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

interface TabButtonProps<T extends string> {
  tab: TabConfig<T>
  isActive: boolean
  onClick: () => void
}

function TabButton<T extends string>({ tab, isActive, onClick }: TabButtonProps<T>) {
  const Icon = tab.icon
  const isDestructive = tab.variant === 'destructive'

  return (
    <button
      onClick={onClick}
      className={cn(
        'border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap',
        isActive
          ? isDestructive
            ? 'border-destructive text-destructive'
            : 'border-primary text-primary'
          : isDestructive
            ? 'border-transparent text-muted-foreground hover:text-destructive'
            : 'border-transparent text-muted-foreground hover:text-foreground'
      )}
    >
      <span className="flex items-center gap-2">
        <Icon className="h-4 w-4" />
        {tab.label}
      </span>
    </button>
  )
}
