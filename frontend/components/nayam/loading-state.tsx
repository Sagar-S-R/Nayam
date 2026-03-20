import { Brain } from "lucide-react"

interface LoadingStateProps {
  message?: string
  fullScreen?: boolean
}

export function LoadingState({ message = "NAYAM is analyzing...", fullScreen = false }: LoadingStateProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="relative h-16 w-16">
        {/* Outer pulsing ring */}
        <div className="absolute inset-0 rounded-full border-2 border-primary/30 animate-pulse" />
        {/* Middle rotating ring */}
        <div className="absolute inset-2 rounded-full border-2 border-transparent border-t-primary border-r-primary animate-spin" />
        {/* Inner icon */}
        <div className="absolute inset-4 flex items-center justify-center rounded-full border-2 border-primary bg-primary/10">
          <Brain className="h-6 w-6 text-primary" />
        </div>
      </div>

      {/* Pulsing text message */}
      <div className="text-center">
        <p className="text-sm font-bold uppercase tracking-wider text-foreground animate-pulse">
          {message}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          This may take a moment...
        </p>
      </div>
    </div>
  )

  if (fullScreen) {
    return (
      <main className="flex h-[calc(100vh-3.5rem)] items-center justify-center bg-background">
        {content}
      </main>
    )
  }

  return (
    <div className="flex items-center justify-center py-16">
      {content}
    </div>
  )
}
