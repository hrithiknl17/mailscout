"use client"

import { useCallback, useState } from "react"
import { Upload } from "lucide-react"
import { cn } from "@/lib/utils"

interface CsvUploaderProps {
  onFile: (file: File) => void
  disabled?: boolean
}

export function CsvUploader({ onFile, disabled }: CsvUploaderProps) {
  const [dragging, setDragging] = useState(false)

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.endsWith(".csv") && !file.name.endsWith(".txt")) return
      onFile(file)
    },
    [onFile]
  )

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ""
  }

  return (
    <label
      className={cn(
        "flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-10 cursor-pointer transition-colors",
        dragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/30",
        disabled && "opacity-50 pointer-events-none"
      )}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <Upload className="h-8 w-8 text-muted-foreground mb-3" />
      <p className="text-sm font-medium">Drop CSV or TXT file here</p>
      <p className="text-xs text-muted-foreground mt-1">or click to browse</p>
      <p className="text-xs text-muted-foreground mt-2">CSV must have an &quot;email&quot; column · max 10,000 emails</p>
      <input
        type="file"
        accept=".csv,.txt"
        className="sr-only"
        onChange={onInputChange}
        disabled={disabled}
      />
    </label>
  )
}
