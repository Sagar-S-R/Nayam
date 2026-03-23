# NAYAM API Configuration Guide

## Overview

The frontend uses a **centralized, dynamic API configuration** that allows seamless switching between:
- ✅ Local backend (`http://localhost:8000/api/v1`)
- ✅ Cloudflare tunnel (for hackathon demos)
- ✅ Production deployment (Vercel with custom backend)

All changes **do not require code modifications** — only environment variable updates.

---

## Quick Start

### 1. **Local Development**

Create or update `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 2. **Cloudflare Tunnel** (Hackathon Demos)

Update `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=https://your-tunnel-url.trycloudflare.com/api/v1
```

### 3. **Production** (Vercel Deployment)

Set in Vercel Dashboard:
1. Go to **Settings** → **Environment Variables**
2. Add:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://api.production.com/api/v1`
3. Redeploy

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────┐
│  Next.js Frontend (React Components)    │
│  ├─ pages/*, components/*               │
│  └─ lib/services.ts (business logic)    │
└────────────────┬────────────────────────┘
                 │ uses
                 ↓
╔═════════════════════════════════════════╗
║  lib/api.ts (Centralized API Client)    ║
║  ├─ API_BASE from env variable          ║
║  ├─ Token management                    ║
║  ├─ Error handling                      ║
║  ├─ CORS-compatible (Bearer tokens)     ║
║  └─ Automatic Authorization headers     ║
╚═════════════════╦═════════════════════════╝
                  │ sends requests to
                  ↓
      ┌───────────────────────┐
      │  FastAPI Backend      │
      │  (any domain/tunnel)  │
      └───────────────────────┘
```

### Environment Variable Configuration

**File:** `frontend/.env.local`

```env
# Backend API base URL (with /api/v1 path)
# Change this to switch backends without code changes
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

**Key Details:**
- `NEXT_PUBLIC_` prefix: Makes variable available to browser bundle
- Must include full path: `http://domain/api/v1`
- Works with CORS: Uses token-based auth (Bearer header), not cookies

---

## Core Files

### 1. **lib/api.ts** — Centralized API Client

**What it does:**
- Resolves `API_BASE` from environment
- Wraps all HTTP requests
- Auto-injects Bearer token
- Handles errors consistently
- CORS-compatible

**Key exports:**

```typescript
// Use this object for all API calls
api.get<T>(endpoint, params?)      // GET request
api.post<T>(endpoint, body?)       // POST request
api.patch<T>(endpoint, body?)      // PATCH request
api.delete<T>(endpoint)            // DELETE request
api.upload<T>(endpoint, formData)  // File upload

// Token management
getToken()              // Retrieve stored JWT token
setToken(token)         // Store JWT token
clearToken()            // Clear token (logout)

// Error handling
ApiError                // Thrown by failed requests
  .isUnauthorized()     // Check if 401
  .isServerError()      // Check if 5xx
```

### 2. **lib/services.ts** — API Service Functions

**Already using the centralized config!** Example:

```typescript
// All these use api.ts automatically
export async function login(email: string, password: string) {
  return api.post<TokenResponse>("/auth/login", { email, password })
  // This sends to: ${API_BASE}/auth/login
  // Headers include: Authorization: Bearer ${token}
}

export async function fetchCitizens(params?) {
  return api.get<CitizenListResponse>("/citizens", params)
  // This sends to: ${API_BASE}/citizens?...params
}

export async function uploadDocument(title: string, file: File) {
  const formData = new FormData()
  formData.append("title", title)
  formData.append("file", file)
  return api.upload<DocumentBackend>("/documents/upload", formData)
  // This sends to: ${API_BASE}/documents/upload
}
```

---

## Usage Examples

### Example 1: Simple GET Request

```typescript
import { api } from "@/lib/api"

async function fetchUserDashboard() {
  try {
    const data = await api.get("/dashboard")
    console.log("Dashboard:", data)
  } catch (error) {
    if (error instanceof ApiError && error.isUnauthorized()) {
      // Handle 401: redirect to login
      window.location.href = "/login"
    } else {
      console.error("Failed to load dashboard:", error.message)
    }
  }
}
```

### Example 2: POST with Error Handling

```typescript
import { api, ApiError } from "@/lib/api"
import { login } from "@/lib/services"

async function handleLogin(email: string, password: string) {
  try {
    const result = await login(email, password)
    localStorage.setItem("token", result.access_token)
    return result
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.isUnauthorized()) {
        alert("Invalid email or password")
      } else if (error.isServerError()) {
        alert("Server error. Please try again later.")
      } else {
        alert(`Error: ${error.detail}`)
      }
    }
    throw error
  }
}
```

### Example 3: File Upload

```typescript
import { api } from "@/lib/api"

async function uploadFile(file: File) {
  try {
    const formData = new FormData()
    formData.append("title", file.name)
    formData.append("file", file)

    const response = await api.upload("/documents/upload", formData)
    console.log("Uploaded:", response)
  } catch (error) {
    console.error("Upload failed:", error)
  }
}
```

### Example 4: Query Parameters

```typescript
import { api } from "@/lib/api"

async function fetchFilteredIssues() {
  const data = await api.get("/issues", {
    limit: 10,
    skip: 0,
    status: "Open",
    priority: "High",
  })
  // Sends to: ${API_BASE}/issues?limit=10&skip=0&status=Open&priority=High
}
```

---

## Authentication Flow

### Token Management

1. **Login** — Get token from backend
   ```typescript
   const result = await api.post("/auth/login", {...})
   setToken(result.access_token)
   ```

2. **Auto-inject** — All requests include token
   ```typescript
   // Automatically added by api.ts:
   // Authorization: Bearer ${token}
   ```

3. **Handle Expiry** — Catch 401 and redirect
   ```typescript
   try {
     await api.get("/dashboard")
   } catch (error) {
     if (error instanceof ApiError && error.isUnauthorized()) {
       window.location.href = "/login"
     }
   }
   ```

4. **Logout** — Clear token
   ```typescript
   clearToken()
   window.location.href = "/login"
   ```

---

## CORS & Security

### Why Token-Based Auth (Not Cookies)?

✅ **Token-based (current):**
- Works with Cloudflare tunnels
- No CORS issues (not cookie-based)
- Stateless backend
- Secure for cross-origin requests

❌ **Cookie-based:**
- Requires SameSite=None (potential CSRF)
- CORS issues with different domains
- Doesn't work well with tunnels

### Headers Automatically Set

| Header | Value | When |
|--------|-------|------|
| `Authorization` | `Bearer {token}` | If token exists in localStorage |
| `Content-Type` | `application/json` | For JSON requests (not FormData) |

---

## Debugging

### Check API Base URL at Startup

Open browser console and look for:

```
[NAYAM API] Base URL: http://localhost:8000/api/v1 (from NEXT_PUBLIC_API_URL="...")
```

Or (if using Next.js rewrites):

```
[NAYAM API] Base URL: /api/v1 (using Next.js rewrites)
```

### Enable Development Logging

In `lib/api.ts`, `apiFetch()` logs all requests:

```typescript
if (process.env.NODE_ENV === "development") {
  console.log(`[NAYAM API] GET /issues`)
}
```

### View Error Details

```typescript
try {
  await api.get("/dashboard")
} catch (error) {
  console.error(`[NAYAM API Error] ${error.status}`, error.detail)
}
```

---

## Switching Between Backends

### Scenario 1: Local → Cloudflare Tunnel

**Before (local development):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

**After (hackathon demo):**
```env
NEXT_PUBLIC_API_URL=https://my-tunnel.trycloudflare.com/api/v1
```

**Steps:**
1. Edit `frontend/.env.local`
2. Save and let Next.js auto-reload
3. No code changes needed!

### Scenario 2: Local → Vercel Production

**In Vercel Dashboard:**
1. Go to **Settings** → **Environment Variables**
2. Set `NEXT_PUBLIC_API_URL=https://api.production.com/api/v1`
3. Redeploy
4. Done!

---

## Troubleshooting

### Issue: "401 Unauthorized"

**Problem:** Token is missing or expired

**Solution:**
```typescript
// Check if token exists
console.log("Token:", getToken())

// Clear old token and re-login
clearToken()
window.location.href = "/login"
```

### Issue: "CORS error" or "Network error"

**Problem:** Wrong backend URL or backend is down

**Solution:**
```typescript
// Check correct URL is being used
console.log("[DEBUG] API_BASE:", process.env.NEXT_PUBLIC_API_URL)

// Check backend is running
curl http://localhost:8000/api/v1/health
```

### Issue: "Double /api/v1" in URL

**Problem:** Using `api.get("/api/v1/issues")` instead of `api.get("/issues")`

**Solution:**
```typescript
// ❌ Wrong
api.get("/api/v1/issues")  // Becomes: ${API_BASE}/api/v1/issues

// ✅ Correct
api.get("/issues")         // Becomes: ${API_BASE}/issues
```

### Issue: Environment variable not updating

**Problem:** Next.js caches environment on startup

**Solution:**
1. Stop dev server (`Ctrl+C`)
2. Update `.env.local`
3. Restart dev server (`npm run dev`)
4. Check console log: `[NAYAM API] Base URL: ...`

---

## Best Practices

✅ **DO:**
- Keep API_BASE in `lib/api.ts` (single source of truth)
- Use `/endpoint` paths in services (without `/api/v1`)
- Include token in Authorization header (automatic)
- Handle ApiError with `.isUnauthorized()` for 401s
- Use TypeScript for request/response types

❌ **DON'T:**
- Hardcode URLs in components (`fetch("http://localhost...")`)
- Use multiple API clients
- Rely on cookies for auth (use tokens)
- Skip the Authorization header (automatic, don't remove)
- Commit `.env.local` to version control

---

## Environment Variable Reference

| Environment | Variable | Example Value |
|-------------|----------|------------------|
| Local Dev | `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` |
| Cloudflare Tunnel | `NEXT_PUBLIC_API_URL` | `https://tunnel.trycloudflare.com/api/v1` |
| Vercel Staging | `NEXT_PUBLIC_API_URL` | `https://staging-api.com/api/v1` |
| Vercel Production | `NEXT_PUBLIC_API_URL` | `https://api.production.com/api/v1` |

---

## Testing the Setup

```bash
# 1. Check environment variable is set
cat frontend/.env.local

# 2. Start dev server
cd frontend
npm run dev

# 3. Open browser console
# Should see: [NAYAM API] Base URL: http://localhost:8000/api/v1

# 4. Try a login request
# Check Network tab in DevTools
# URL should be: http://localhost:8000/api/v1/auth/login
# Headers should include: Authorization: Bearer {token}
```

---

## Summary

| Aspect | Configuration |
|--------|---|
| **Where to set API URL?** | `frontend/.env.local` → `NEXT_PUBLIC_API_URL` |
| **How to switch backends?** | Edit `.env.local`, restart dev server |
| **How is auth handled?** | Automatic Bearer token in Authorization header |
| **CORS issues?** | Won't happen (token-based, not cookies) |
| **Production deployment?** | Set `NEXT_PUBLIC_API_URL` in Vercel Dashboard |
| **Code changes needed?** | ❌ No! Only env variable updates |

---

For questions or issues, check the console logs or create an issue in the repository.
