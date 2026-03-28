"use client"

import { useSessionExpiry } from "@/hooks/use-session-expiry"
import { SessionExpiryModal } from "@/components/nayam/session-expiry-modal"

/**
 * SessionExpiryProvider
 * Wraps the app and handles session expiration UI.
 * Must be placed inside AuthProvider to access auth context.
 */
export function SessionExpiryProvider({ children }: { children: React.ReactNode }) {
  const { isSessionExpired, closeModal } = useSessionExpiry()

  return (
    <>
      {children}
      <SessionExpiryModal isOpen={isSessionExpired} onClose={closeModal} />
    </>
  )
}
