interface InstructionDisplayProps {
  currentStep: number
  currentInstruction: string
}

export default function InstructionDisplay({
  currentStep,
  currentInstruction,
}: InstructionDisplayProps) {
  return (
    <div className="flex flex-1 items-center justify-center overflow-y-auto p-6 sm:p-8">
      <div className="max-w-2xl text-center">
        {/* Step number badge */}
        <div className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground sm:mb-6 sm:h-12 sm:w-12 sm:text-xl">
          {currentStep + 1}
        </div>

        {/* Instruction text */}
        <p className="text-lg leading-relaxed text-foreground sm:text-xl md:text-2xl">
          {currentInstruction}
        </p>
      </div>
    </div>
  )
}
