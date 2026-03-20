import { ReactNode } from "react"
import { LucideIcon } from "lucide-react"

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({ icon: Icon, title, description, action, className = "" }: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-lg border-3 border-dashed border-foreground/30 bg-muted/50 p-12 text-center ${className}`}
    >
      <Icon className="h-12 w-12 text-muted-foreground/60 mb-4" />
      <h3 className="text-lg font-black uppercase tracking-wider text-foreground mb-2">
        {title}
      </h3>
      <p className="text-sm text-muted-foreground max-w-sm mb-6">
        {description}
      </p>
      {action && (
        <button
          onClick={action.onClick}
          className="border-2 border-foreground bg-primary px-6 py-2 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-[3px_3px_0px_0px] shadow-foreground/20 transition-all hover:shadow-[5px_5px_0px_0px] hover:-translate-x-0.5 hover:-translate-y-0.5"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
