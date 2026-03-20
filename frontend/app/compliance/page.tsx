"use client"

import { useState, useMemo, useEffect } from "react"
import { Download, Filter, Shield, Lock, CheckCircle, Search, Loader2, Bot, User } from "lucide-react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { toast } from "sonner"

type AuditEntry = {
  id: string
  timestamp: string
  actor_name: string
  actor_role: string
  action: string
  resource_type: string
  resource_id: string
  description: string
  is_ai: boolean
}

async function fetchAuditTrail(): Promise<{ total: number; entries: AuditEntry[] }> {
  const token = typeof window !== "undefined" ? localStorage.getItem("nayam_token") : null
  const res = await fetch("/api/v1/compliance/audit-trail?limit=100", {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error("Failed to fetch audit trail")
  return res.json()
}

export default function CompliancePage() {
  const [userFilter, setUserFilter] = useState("")
  const [typeFilter, setTypeFilter] = useState("")
  const [isExporting, setIsExporting] = useState(false)
  const [includeHindi, setIncludeHindi] = useState(true)
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    setIsLoading(true)
    fetchAuditTrail()
      .then((data) => setAuditEntries(data.entries))
      .catch(() => toast.error("Could not load audit trail"))
      .finally(() => setIsLoading(false))
  }, [])

  const handleExportPDF = async () => {
    setIsExporting(true)
    try {
      const token = localStorage.getItem("nayam_token")
      if (!token) {
        toast.error("Not authenticated", { description: "Please log in to export." })
        return
      }
      const response = await fetch(`/api/v1/compliance/audit-trail/pdf?include_hindi=${includeHindi}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.status === 403) {
        toast.error("Access denied", { description: "You need Leader or Analyst role." })
        return
      }
      if (!response.ok) {
        toast.error("Export failed", { description: `Server error ${response.status}` })
        return
      }
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `NAYAM_AuditTrail_${Date.now()}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      toast.success("PDF exported successfully")
    } catch (err) {
      toast.error("Export failed", { description: err instanceof Error ? err.message : "Unknown error" })
    } finally {
      setIsExporting(false)
    }
  }

  const actors = useMemo(() => [...new Set(auditEntries.map((e) => e.actor_name))], [auditEntries])
  const resourceTypes = useMemo(() => [...new Set(auditEntries.map((e) => e.resource_type))], [auditEntries])

  const filtered = auditEntries.filter((e) => {
    const matchActor = !userFilter || e.actor_name === userFilter
    const matchType = !typeFilter || e.resource_type === typeFilter
    return matchActor && matchType
  })

  if (isLoading) {
    return (
      <main className="flex h-[calc(100vh-3.5rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </main>
    )
  }

  return (
    <main className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black uppercase tracking-wider text-foreground">
            Compliance &amp; Audit
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Immutable audit trail — every action logged, timestamped, and traceable
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2 border-2 border-foreground bg-card px-3 py-2">
            <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Language:</span>
            <select
              value={includeHindi ? "bilingual" : "english"}
              onChange={(e) => setIncludeHindi(e.target.value === "bilingual")}
              className="bg-card text-xs font-bold uppercase text-foreground focus:outline-none"
            >
              <option value="bilingual">English + Hindi</option>
              <option value="english">English Only</option>
            </select>
          </div>
          <button
            onClick={handleExportPDF}
            disabled={isExporting}
            className="flex items-center gap-2 border-3 border-foreground bg-primary px-4 py-2 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-[4px_4px_0px_0px] shadow-foreground/20 transition-all hover:shadow-[6px_6px_0px_0px] hover:-translate-x-0.5 hover:-translate-y-0.5 disabled:opacity-50"
          >
            {isExporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {isExporting ? "Exporting..." : "Export PDF"}
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center border-2 border-emerald-900 bg-emerald-100">
              <Shield className="h-5 w-5 text-emerald-900" />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Total Logs</p>
              <p className="text-xl font-black text-foreground">{auditEntries.length}</p>
            </div>
          </div>
        </div>
        <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center border-2 border-foreground bg-primary">
              <Lock className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Encryption</p>
              <p className="text-sm font-black text-foreground">AES-256 Active</p>
            </div>
          </div>
        </div>
        <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center border-2 border-purple-900 bg-purple-100">
              <Bot className="h-5 w-5 text-purple-900" />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">AI Actions</p>
              <p className="text-xl font-black text-purple-700">{auditEntries.filter((e) => e.is_ai).length}</p>
            </div>
          </div>
        </div>
        <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center border-2 border-foreground bg-muted">
              <CheckCircle className="h-5 w-5 text-foreground" />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Unique Actors</p>
              <p className="text-xl font-black text-foreground">{actors.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <select
          value={userFilter}
          onChange={(e) => setUserFilter(e.target.value)}
          className="border-2 border-foreground bg-card px-3 py-2 text-xs font-bold uppercase text-foreground"
        >
          <option value="">All Actors</option>
          {actors.map((u) => <option key={u} value={u}>{u}</option>)}
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="border-2 border-foreground bg-card px-3 py-2 text-xs font-bold uppercase text-foreground"
        >
          <option value="">All Resources</option>
          {resourceTypes.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="border-3 border-foreground bg-card shadow-[4px_4px_0px_0px] shadow-foreground/20">
        <Table>
          <TableHeader>
            <TableRow className="border-b-2 border-foreground bg-muted/50">
              <TableHead className="text-xs font-black uppercase tracking-widest">Timestamp</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Actor</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Role</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Action</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Resource</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Initiated By</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Description</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="py-10 text-center text-sm text-muted-foreground">
                  No audit entries yet. Perform any action (create an issue, upload a document, approve a request) to see it logged here.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((entry) => (
                <TableRow key={entry.id} className="border-b border-foreground/10">
                  <TableCell className="text-xs font-mono text-muted-foreground whitespace-nowrap">
                    {entry.timestamp.replace("T", " ").slice(0, 19)}
                  </TableCell>
                  <TableCell className="text-sm font-bold text-foreground">{entry.actor_name}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border border-foreground/30 bg-muted text-foreground">
                      {entry.actor_role}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border ${entry.action === "create"
                        ? "border-emerald-900 bg-emerald-100 text-emerald-900"
                        : entry.action === "approve"
                          ? "border-blue-900 bg-blue-100 text-blue-900"
                          : entry.action === "reject"
                            ? "border-red-900 bg-red-100 text-red-900"
                            : "border-amber-900 bg-amber-100 text-amber-900"
                      }`}>
                      {entry.action}
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground font-mono">{entry.resource_type}</TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border ${entry.is_ai
                        ? "border-purple-900 bg-purple-100 text-purple-900"
                        : "border-foreground/30 bg-muted text-foreground"
                      }`}>
                      {entry.is_ai ? <Bot className="h-3 w-3" /> : <User className="h-3 w-3" />}
                      {entry.is_ai ? "AI" : "Human"}
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground max-w-xs truncate">{entry.description}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </main>
  )
}
