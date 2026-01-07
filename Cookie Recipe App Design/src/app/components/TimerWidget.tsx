import { FC, useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, X } from 'lucide-react';

interface TimerWidgetProps {
  id: string;
  label: string;
  duration: number; // in seconds
  onComplete: () => void;
  onDelete: () => void;
}

export const TimerWidget: FC<TimerWidgetProps> = ({ id, label, duration, onComplete, onDelete }) => {
  const [timeLeft, setTimeLeft] = useState(duration);
  const [isRunning, setIsRunning] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    let interval: number | undefined;
    
    if (isRunning && timeLeft > 0) {
      interval = window.setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            setIsRunning(false);
            setIsComplete(true);
            onComplete();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, timeLeft, onComplete]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleToggle = () => {
    setIsRunning(!isRunning);
    if (isComplete) {
      setIsComplete(false);
    }
  };

  const handleReset = () => {
    setTimeLeft(duration);
    setIsRunning(false);
    setIsComplete(false);
  };

  const progress = ((duration - timeLeft) / duration) * 100;

  return (
    <div className={`bg-card rounded-xl p-4 shadow-sm border-2 transition-colors ${
      isComplete ? 'border-primary' : 'border-transparent'
    }`}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1">
          <div className="text-sm text-muted-foreground mb-1">{label}</div>
          <div className={`text-2xl font-medium ${isComplete ? 'text-primary' : ''}`}>
            {formatTime(timeLeft)}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleToggle}
            className="w-12 h-12 bg-primary text-primary-foreground rounded-full flex items-center justify-center hover:opacity-90 transition-opacity active:scale-95"
            aria-label={isRunning ? 'Pause timer' : 'Start timer'}
          >
            {isRunning ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>
          <button
            onClick={handleReset}
            className="w-12 h-12 bg-secondary text-secondary-foreground rounded-full flex items-center justify-center hover:bg-muted transition-colors active:scale-95"
            aria-label="Reset timer"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
          <button
            onClick={onDelete}
            className="w-12 h-12 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors active:scale-95"
            aria-label="Delete timer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
      {isRunning && (
        <div className="mt-3 h-1.5 bg-secondary rounded-full overflow-hidden">
          <div 
            className="h-full bg-primary transition-all duration-1000 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};