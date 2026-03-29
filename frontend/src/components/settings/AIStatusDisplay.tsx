import { AlertCircle } from 'lucide-react'
import type { AIStatus, AIModel } from '../../api/client'
import { cn } from '../../lib/utils'

interface AIStatusDisplayProps {
  aiStatus: AIStatus | null
  models: AIModel[]
}

function getStatusColor(aiStatus: AIStatus | null): string {
  if (aiStatus?.available) return 'bg-green-500'
  if (aiStatus?.configured) return 'bg-yellow-500'
  return 'bg-red-500'
}

function getStatusLabel(aiStatus: AIStatus | null): string {
  if (aiStatus?.available) return 'Connected'
  if (aiStatus?.configured) return 'Invalid key'
  return 'Not configured'
}

function StatusWarning({ aiStatus }: { aiStatus: AIStatus | null }) {
  if (!aiStatus?.configured || aiStatus?.valid) return null

  return (
    <div className="mb-4 flex items-center gap-2 rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-3">
      <AlertCircle className="h-5 w-5 flex-shrink-0 text-yellow-500" />
      <p className="text-sm text-yellow-600 dark:text-yellow-400">
        {aiStatus?.error ||
          'Your API key appears to be invalid or expired. Please update it.'}
      </p>
    </div>
  )
}

export default function AIStatusDisplay({ aiStatus, models }: AIStatusDisplayProps) {
  const getModelName = (modelId: string) => {
    const model = models.find((m) => m.id === modelId)
    return model?.name || modelId
  }

  return (
    <>
      <div className="mb-4 flex items-center gap-2">
        <div
          className={cn('h-2 w-2 rounded-full', getStatusColor(aiStatus))}
        />
        <span className="text-sm text-muted-foreground">
          {getStatusLabel(aiStatus)}
        </span>
      </div>

      <StatusWarning aiStatus={aiStatus} />

      {aiStatus?.available && (
        <div className="mb-4 text-sm text-muted-foreground">
          Default model:{' '}
          <span className="font-medium text-foreground">
            {getModelName(aiStatus.default_model)}
          </span>
        </div>
      )}
    </>
  )
}
