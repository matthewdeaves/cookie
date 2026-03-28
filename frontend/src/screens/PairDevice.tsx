import { useNavigate } from 'react-router-dom'
import DeviceCodeEntry from '../components/DeviceCodeEntry'

export default function PairDevice() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">Pair a Device</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Enter the code shown on the device you want to pair
          </p>
        </div>

        <DeviceCodeEntry />

        <div className="text-center">
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Go back
          </button>
        </div>
      </div>
    </div>
  )
}
