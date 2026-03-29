interface InstructionDisplayProps {
  currentStep: number
  currentInstruction: string
}

export default function InstructionDisplay({
  currentStep,
  currentInstruction,
}: InstructionDisplayProps) {
  return (
    <div
      className="flex flex-1 items-center justify-center p-6"
      style={{ maxHeight: '60vh' }}
    >
      <div className="max-w-2xl text-center">
        {/* Step number */}
        <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-xl font-bold text-primary-foreground">
          {currentStep + 1}
        </div>

        {/* Instruction text */}
        <p className="text-xl leading-relaxed text-foreground sm:text-2xl">
          {currentInstruction}
        </p>
      </div>
    </div>
  )
}
