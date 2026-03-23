# NAYAM API — Quick Reference

## Current Setup ✅

```
Frontend: Next.js (React)
Backend: FastAPI
Auth: JWT Token (Bearer header)
Env Var: NEXT_PUBLIC_API_URL
Current URL: https://accordance-means-morgan-scsi.trycloudflare.com/api/v1
```

---

## Making API Requests

### Basic Pattern
```typescript
import { api, ApiError } from "@/lib/api"

try {
  const data = await api.METHOD("endpoint", body?)
  console.log(data)
} catch (error) {
  if (error instanceof ApiError) {
    if (error.isUnauthorized()) {
      // 401: Redirect to login
    }
  }
}
```

### Methods

| Method | Usage | Example |
|--------|-------|---------|
| `api.get<T>(path, params?)` | GET request | `api.get("/issues", {limit: 10})` |
| `api.post<T>(path, body?)` | POST request | `api.post("/issues", {...})` |
| `api.patch<T>(path, body?)` | PATCH request | `api.patch("/issues/123", {...})` |
| `api.put<T>(path, body?)` | PUT request | `api.put("/users/123", {...})` |
| `api.delete<T>(path)` | DELETE request | `api.delete("/issues/123")` |
| `api.upload<T>(path, formData)` | File upload | `api.upload("/docs/upload", fd)` |

---

## Switching Backend URLs

### To Local Backend
Edit `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### To Cloudflare Tunnel
Edit `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=https://your-tunnel.trycloudflare.com/api/v1
```

### To Production
In Vercel Dashboard → Settings → Environment Variables:
```
Key: NEXT_PUBLIC_API_URL
Value: https://api.production.com/api/v1
```

**Then:** Restart dev server or redeploy

---

## Token Management

```typescript
import { getToken, setToken, clearToken } from "@/lib/api"

// Get token
const token = getToken()

// Store token after login
setToken(result.access_token)

// Clear token on logout
clearToken()

// Authorization header is automatically added!
// No need to do it manually
```

---

## Error Handling

```typescript
import { ApiError } from "@/lib/api"

try {
  await api.get("/dashboard")
} catch (error) {
  if (error instanceof ApiError) {
    if (error.isUnauthorized()) {
      // 401: Token expired
      window.location.href = "/login"
    } else if (error.isServerError()) {
      // 5xx: Server error
      alert("Server error. Please try again later.")
    } else {
      // Other errors
      alert(`Error: ${error.detail}`)
    }
  }
}
```

---

## Common Patterns

### Login
```typescript
const result = await api.post("/auth/login", { email, password })
setToken(result.access_token)
```

### Fetch List
```typescript
const data = await api.get("/issues", {
  limit: 10,
  skip: 0,
  status: "Open"
})
```

### Create Resource
```typescript
const issue = await api.post("/issues", {
  citizen_id: "123",
  description: "Issue description",
  department: "Health"
})
```

### Update Resource
```typescript
const updated = await api.patch("/issues/123", {
  status: "Closed"
})
```

### Delete Resource
```typescript
await api.delete("/issues/123")
```

### Upload File
```typescript
const formData = new FormData()
formData.append("title", "My Document")
formData.append("file", file)
const doc = await api.upload("/documents/upload", formData)
```

---

## Debugging

### Check Base URL
Open browser console, should see:
```
[NAYAM API] Base URL: http://localhost:8000/api/v1 (from NEXT_PUBLIC_API_URL="...")
```

### View Request
Check Network tab in DevTools:
- URL: `http://localhost:8000/api/v1/issues`
- Headers: `Authorization: Bearer {token}`
- Content-Type: `application/json`

### View Errors
Check console for:
```
[NAYAM API Error] 401 Unauthorized { detail: "...", url: "..." }
```

---

## ⚠️ Common Mistakes

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| `api.get("/api/v1/issues")` | `api.get("/issues")` |
| `fetch("http://localhost:8000...")` | `api.get("/issues")` |
| Hardcode URL in component | Use `api` from `lib/api.ts` |
| Forget Bearer token | Automatic (don't remove!) |
| Ignore 401 errors | Check `error.isUnauthorized()` |
| Use cookies for auth | Use Bearer token (done automatically) |

---

## File Locations

| File | Purpose |
|------|---------|
| `lib/api.ts` | Centralized API client & token management |
| `lib/services.ts` | API service functions (already using api.ts) |
| `lib/auth-context.tsx` | Auth state & login/logout |
| `.env.local` | Local backend URL (not in git) |
| `.env.example` | Template for .env.local |
| `API_CONFIG_GUIDE.md` | Detailed documentation |
| `lib/api-examples.ts` | Usage examples |

---

## Before Hackathon Demo

1. ✅ Update `NEXT_PUBLIC_API_URL` in `.env.local`
2. ✅ Restart Next.js dev server
3. ✅ Check console: `[NAYAM API] Base URL: https://your-tunnel.trycloudflare.com/api/v1`
4. ✅ Try login to confirm backend connection
5. ✅ Ready to demo! 🚀

---

## Before Vercel Deployment

1. ✅ In Vercel Dashboard, set `NEXT_PUBLIC_API_URL`
2. ✅ Redeploy
3. ✅ Check browser console for correct base URL
4. ✅ Test login on deployed app
5. ✅ Done! ✨

---

For detailed info, see `API_CONFIG_GUIDE.md` or `lib/api-examples.ts`
