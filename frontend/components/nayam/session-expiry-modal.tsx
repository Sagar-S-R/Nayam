"use client"

import { useState, useEffect } from "react"
import { AlertTriangle, LogOut, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { clearToken } from "@/lib/api"

interface SessionExpiryModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SessionExpiryModal({ isOpen, onClose }: SessionExpiryModalProps) {
  const router = useRouter()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    clearToken()
    // Give a moment for the state to update, then redirect
    await new Promise((resolve) => setTimeout(resolve, 500))
    router.push("/login")
    onClose()
  }

  // Prevent closing by clicking outside
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="border-3 border-foreground bg-card p-6 shadow-[8px_8px_0px_0px] shadow-foreground/20 max-w-sm w-full mx-4">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center border-2 border-yellow-900 bg-yellow-100">
            <AlertTriangle className="h-5 w-5 text-yellow-900" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-black uppercase tracking-wider text-foreground">
              Session Expired
            </h3>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              Your login session has expired due to inactivity. For security, please log in again to continue.
            </p>
          </div>
        </div>

        <div className="mt-6 flex gap-2 border-t-2 border-foreground/10 pt-4">
          <button
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="flex-1 flex items-center justify-center gap-2 border-2 border-foreground bg-primary px-4 py-2 text-xs font-bold uppercase tracking-wider text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {isLoggingOut ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Logging Out...
              </>
            ) : (
              <>
                <LogOut className="h-3.5 w-3.5" />
                Login Again
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
