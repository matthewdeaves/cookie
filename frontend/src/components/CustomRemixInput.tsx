interface CustomRemixInputProps {
  value: string
  onChange: (value: string) => void
  disabled: boolean
}

export default function CustomRemixInput({
  value,
  onChange,
  disabled,
}: CustomRemixInputProps) {
  return (
    <div className="mb-5">
      <label
        htmlFor="custom-remix"
        className="mb-2 block text-sm font-medium text-foreground"
      >
        Or describe your own remix
      </label>
      <input
        id="custom-remix"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="e.g., Make it gluten-free"
        className="w-full rounded-lg border border-border bg-background px-4 py-2.5 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
      />
    </div>
  )
}
