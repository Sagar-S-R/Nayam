/**
 * NAYAM — API Client
 *
 * Centralized fetch wrapper with:
 *  • Dynamic base URL via NEXT_PUBLIC_API_URL environment variable
 *  • Automatic JWT token injection (Bearer token in Authorization header)
 *  • Typed JSON response parsing
 *  • Error handling with status codes
 *  • CORS-compatible token-based authentication
 *  • Vercel & Cloudflare tunnel support
 *
 * Environment Variables:
 *  • NEXT_PUBLIC_API_URL: Backend base URL (e.g., http://localhost:8000/api/v1 or Cloudflare tunnel)
 *  • If not set, uses relative path "/api/v1" (requires Next.js rewrites)
 */

// Dynamically resolve API base URL from environment
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1"

// Log API configuration once at startup for debugging
if (typeof window !== "undefined") {
  console.log(
    `[NAYAM API] Base URL: ${API_BASE}`,
    API_BASE === "/api/v1"
      ? "(using Next.js rewrites)"
      : `(from NEXT_PUBLIC_API_URL="${process.env.NEXT_PUBLIC_API_URL}")`
  )
}
/** Retrieve the stored JWT token */
export function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("nayam_token")
}

/** Store the JWT token */
export function setToken(token: string): void {
  localStorage.setItem("nayam_token", token)
}

/** Clear the stored JWT token */
export function clearToken(): void {
  localStorage.removeItem("nayam_token")
  localStorage.removeItem("nayam_user")
}

/** API error with status code and context */
export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
    this.name = "ApiError"
  }

  /**
   * Check if error is due to authentication failure.
   * Useful for redirecting to login on 401 responses.
   */
  isUnauthorized(): boolean {
    return this.status === 401
  }

  /**
   * Check if error is a server error (5xx).
   * Useful for showing different error messages to users.
   */
  isServerError(): boolean {
    return this.status >= 500
  }
}

interface FetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown
  params?: Record<string, string | number | boolean | undefined | null>
}

/**
 * Core fetch wrapper with automatic features:
 *  • Base URL handling (API_BASE + endpoint)
 *  • Query string building
 *  • Authorization header (Bearer token if available)
 *  • Content-Type detection (JSON or FormData)
 *  • Error handling with ApiError
 *
 * @param endpoint - Path relative to API_BASE (e.g., "/issues", "/dashboard")
 * @param options - Fetch options with body, params, and headers
 * @returns Typed response data or throws ApiError
 */
async function apiFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { body, params, headers: extraHeaders, ...rest } = options

  // Build full URL with query parameters
  let url = `${API_BASE}${endpoint}`
  if (params) {
    const search = new URLSearchParams()
    for (const [key, val] of Object.entries(params)) {
      if (val !== undefined && val !== null && val !== "") {
        search.set(key, String(val))
      }
    }
    const qs = search.toString()
    if (qs) url += `?${qs}`
  }

  // Build headers with authorization and content-type
  const headers: Record<string, string> = {
    ...(extraHeaders as Record<string, string>),
  }

  // Add Bearer token for CORS-compatible authentication
  const token = getToken()
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  // Only set Content-Type for JSON (FormData sets its own boundary)
  if (body !== undefined && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json"
  }

  // Debug logging in development
  if (process.env.NODE_ENV === "development") {
    console.log(`[NAYAM API] ${rest.method || "GET"} ${endpoint}`)
  }

  // Make the request
  const res = await fetch(url, {
    ...rest,
    headers,
    body:
      body instanceof FormData
        ? body
        : body !== undefined
          ? JSON.stringify(body)
          : undefined,
  })

  return handleResponse<T>(res)
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`

    // Try to extract error detail from backend response
    try {
      const err = await res.json()
      if (Array.isArray(err.detail)) {
        // FastAPI validation errors return an array of objects
        detail = err.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join("; ")
      } else {
        detail = err.detail || err.message || detail
      }
    } catch {
      // If response is not JSON, use status text
      detail = res.statusText || detail
    }

    // Log errors for debugging
    console.error(
      `[NAYAM API Error] ${res.status} ${res.statusText}`,
      { detail, url: res.url }
    )

    throw new ApiError(res.status, detail)
  }

  // Handle empty responses (204 No Content)
  if (res.status === 204) return {} as T

  return res.json() as Promise<T>
}

// ── Convenience Methods ─────────────────────────────────────────────
//
// All methods automatically:
//  • Use API_BASE from environment
//  • Include Authorization header with token
//  • Parse response as typed JSON
//  • Handle errors and throw ApiError
//

export const api = {
  /**
   * GET request
   * @example
   * const data = await api.get<User>('/users/123');
   * const list = await api.get<User[]>('/users', { limit: 10, skip: 0 });
   */
  get: <T>(endpoint: string, params?: FetchOptions["params"]) =>
    apiFetch<T>(endpoint, { method: "GET", params }),

  /**
   * POST request
   * @example
   * const result = await api.post<TokenResponse>('/auth/login', { email, password });
   */
  post: <T>(endpoint: string, body?: unknown) =>
    apiFetch<T>(endpoint, { method: "POST", body }),

  /**
   * PUT request (replace entire resource)
   * @example
   * const updated = await api.put<User>('/users/123', { name: 'New Name' });
   */
  put: <T>(endpoint: string, body?: unknown) =>
    apiFetch<T>(endpoint, { method: "PUT", body }),

  /**
   * PATCH request (partial update)
   * @example
   * const updated = await api.patch<Issue>('/issues/123', { status: 'Closed' });
   */
  patch: <T>(endpoint: string, body?: unknown) =>
    apiFetch<T>(endpoint, { method: "PATCH", body }),

  /**
   * DELETE request
   * @example
   * await api.delete('/users/123');
   */
  delete: <T>(endpoint: string) =>
    apiFetch<T>(endpoint, { method: "DELETE" }),

  /**
   * POST request with FormData (for file uploads)
   * @example
   * const formData = new FormData();
   * formData.append('file', file);
   * formData.append('title', 'My Document');
   * const doc = await api.upload<Document>('/documents/upload', formData);
   */
  upload: <T>(endpoint: string, formData: FormData) =>
    apiFetch<T>(endpoint, { method: "POST", body: formData }),
}
