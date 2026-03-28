import { useEffect, useState, useCallback } from "react"
import { setUnauthorizedHandler } from "@/lib/api"

/**
 * Hook to handle session expiration (401 errors)
 * Shows a modal when token expires and coordinates logout
 */
export function useSessionExpiry() {
  const [isSessionExpired, setIsSessionExpired] = useState(false)

  useEffect(() => {
    // Register the 401 handler on mount
    const handleUnauthorized = () => {
      setIsSessionExpired(true)
    }

    setUnauthorizedHandler(handleUnauthorized)

    // Cleanup on unmount
    return () => {
      setUnauthorizedHandler(null)
    }
  }, [])

  const closeModal = useCallback(() => {
    setIsSessionExpired(false)
  }, [])

  return {
    isSessionExpired,
    closeModal,
  }
}
