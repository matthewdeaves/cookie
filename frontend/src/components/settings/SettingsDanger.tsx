import { useState } from 'react'
import { toast } from 'sonner'
import { api, type ResetPreview } from '../../api/client'
import DangerZoneInfo from './DangerZoneInfo'
import ResetPreviewStep from './ResetPreviewStep'
import ConfirmResetStep from './ConfirmResetStep'

export default function SettingsDanger() {
  const [showResetModal, setShowResetModal] = useState(false)
  const [resetPreview, setResetPreview] = useState<ResetPreview | null>(null)
  const [resetStep, setResetStep] = useState<1 | 2>(1)

  const handleResetClick = async () => {
    try {
      const preview = await api.system.resetPreview()
      setResetPreview(preview)
      setResetStep(1)
      setShowResetModal(true)
    } catch (error) {
      console.error('Failed to load reset preview:', error)
      toast.error('Failed to load reset preview')
    }
  }

  const handleCancelReset = () => {
    setShowResetModal(false)
    setResetPreview(null)
    setResetStep(1)
  }

  return (
    <>
      <DangerZoneInfo onResetClick={handleResetClick} />

      {showResetModal && resetPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleCancelReset}
          />
          <div className="relative w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            {resetStep === 1 ? (
              <ResetPreviewStep
                resetPreview={resetPreview}
                onCancel={handleCancelReset}
                onContinue={() => setResetStep(2)}
              />
            ) : (
              <ConfirmResetStep onBack={() => setResetStep(1)} />
            )}
          </div>
        </div>
      )}
    </>
  )
}
