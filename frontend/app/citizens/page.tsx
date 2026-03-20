"use client"

import { useState, useMemo, useEffect } from "react"
import { Search, Plus, Filter, ChevronLeft, ChevronRight, Loader2, CheckCircle, Lock, Eye } from "lucide-react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { StatusBadge } from "@/components/nayam/status-badge"
import { useApiData } from "@/hooks/use-api-data"
import { fetchCitizens, createCitizen, fetchWards } from "@/lib/services"
import { toast } from "sonner"
import type { Citizen } from "@/lib/types"

export default function CitizensPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [wardFilter, setWardFilter] = useState("")
  const [riskFilter, setRiskFilter] = useState("")
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedCitizen, setSelectedCitizen] = useState<string | null>(null)

  // PII Toggle State
  const [showPii, setShowPii] = useState(false)
  const [userRole, setUserRole] = useState("")

  useEffect(() => {
    try {
      const userStr = localStorage.getItem("nayam_user")
      if (userStr) {
        setUserRole(JSON.parse(userStr).role || "Analyst")
      } else {
        setUserRole("Analyst")
      }
    } catch {
      setUserRole("Analyst")
    }
  }, [])

  // Form state
  const [newName, setNewName] = useState("")
  const [newContact, setNewContact] = useState("")
  const [newWard, setNewWard] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  //  Validation messages
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Ward list
  const [wardList, setWardList] = useState<string[]>([])
  const [loadingWards, setLoadingWards] = useState(true)

  const { data, isLoading, refetch } = useApiData(() => fetchCitizens({ limit: 200, show_pii: showPii }), [showPii])
  const allCitizens: Citizen[] = data?.citizens || []

  // Fetch ward list on mount
  useEffect(() => {
    const loadWards = async () => {
      try {
        const wards = await fetchWards()
        setWardList(wards)
      } catch (err) {
        console.error("Failed to fetch wards:", err)
        setWardList([]) // Fallback to empty
      } finally {
        setLoadingWards(false)
      }
    }
    loadWards()
  }, [])

  const dynamicWards = useMemo(() => [...new Set(allCitizens.map((c) => c.ward))], [allCitizens])

  const filtered = allCitizens.filter((c) => {
    const matchSearch =
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.id.toLowerCase().includes(searchQuery.toLowerCase())
    const matchWard = !wardFilter || c.ward === wardFilter
    const matchRisk = !riskFilter || c.riskLevel === riskFilter
    return matchSearch && matchWard && matchRisk
  })

  const citizen = selectedCitizen
    ? allCitizens.find((c) => c.id === selectedCitizen)
    : null

  // Validate form inputs
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    if (!newName.trim()) {
      errors.name = "Name is required"
    } else if (newName.trim().length < 2) {
      errors.name = "Name must be at least 2 characters"
    } else if (!/[a-zA-Z]/.test(newName)) {
      errors.name = "Name must contain letters"
    }

    if (!newContact.trim()) {
      errors.contact = "Phone number is required"
    } else if (!/^\d{10}$|^\+91\d{10}$|^91\d{10}$|^0\d{10}$/.test(newContact.replace(/[\s\-]/g, ""))) {
      errors.contact = "Invalid phone format. Use Indian format: +91XXXXXXXXXX or XXXXXXXXXX"
    }

    if (!newWard.trim()) {
      errors.ward = "Ward is required"
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleAddCitizen = async () => {
    console.log("Add citizen clicked", { newName, newContact, newWard, wardList })

    if (!validateForm()) {
      console.log("Form validation failed", { errors: validationErrors })
      return
    }

    if (wardList.length === 0) {
      toast.error("Error", { description: "Ward list not loaded. Please refresh and try again." })
      return
    }

    setIsSubmitting(true)
    try {
      console.log("Creating citizen with:", { newName, newContact, newWard })
      const newCitizen = await createCitizen({
        name: newName.trim(),
        contact_number: newContact.trim(),
        ward: newWard.trim(),
      })

      console.log("Citizen created:", newCitizen)

      // Show success toast
      toast.success("Citizen added successfully!", {
        description: `${newName} has been added to Ward ${newWard}`,
      })

      // Reset form
      setShowAddModal(false)
      setNewName("")
      setNewContact("")
      setNewWard("")
      setValidationErrors({})

      // Refetch to show new citizen
      await refetch()
    } catch (error) {
      console.error("Error adding citizen:", error)

      let userMessage = "Failed to add citizen"
      const errorText = error instanceof Error ? error.message : ""

      // Provide actionable error messages
      if (errorText.includes("already exists")) {
        userMessage = "This citizen already exists in the database."
      } else if (errorText.includes("Invalid") || errorText.includes("validation")) {
        userMessage = "Please check your input. Phone number must be valid Indian format."
      } else if (errorText.includes("Unauthorized") || errorText.includes("401")) {
        userMessage = "Your session has expired. Please log in again."
      } else if (errorText.includes("Forbidden") || errorText.includes("403")) {
        userMessage = "You don't have permission to add citizens."
      } else if (errorText.includes("network")) {
        userMessage = "Network error. Please check your connection and try again."
      } else if (errorText) {
        userMessage = errorText
      }

      toast.error("Could not add citizen", {
        description: userMessage,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <main className="flex h-[calc(100vh-3.5rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </main>
    )
  }

  return (
    <main className="p-4 md:p-6 space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-black uppercase tracking-wider text-foreground">
            Citizens
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Citizen records and profile management
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowPii(!showPii)}
            disabled={userRole === "Analyst"}
            className={`flex items-center gap-2 border-3 px-4 py-2 text-xs font-bold uppercase tracking-wider transition-all hover:-translate-x-0.5 hover:-translate-y-0.5 ${userRole === "Analyst"
              ? "border-foreground/30 bg-muted text-muted-foreground cursor-not-allowed"
              : showPii
                ? "border-emerald-600 bg-emerald-50 text-emerald-700 shadow-[4px_4px_0px_0px] shadow-emerald-600/20 hover:shadow-[6px_6px_0px_0px]"
                : "border-foreground bg-background text-foreground shadow-[4px_4px_0px_0px] shadow-foreground/20 hover:shadow-[6px_6px_0px_0px]"
              }`}
            title={userRole === "Analyst" ? "Analyst access restricted" : "Toggle sensitive data"}
          >
            {showPii ? <Eye className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
            {showPii ? "Hide PII" : "Show PII"}
          </button>
          <button
            onClick={() => {
              console.log("Add Citizen button clicked")
              setShowAddModal(true)
              setValidationErrors({})
              setNewName("")
              setNewContact("")
              setNewWard("")
              console.log("Modal opened, ward list:", wardList)
            }}
            className="flex items-center gap-2 border-3 border-foreground bg-primary px-4 py-2 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-[4px_4px_0px_0px] shadow-foreground/20 transition-all hover:shadow-[6px_6px_0px_0px] hover:-translate-x-0.5 hover:-translate-y-0.5"
          >
            <Plus className="h-4 w-4" />
            Add Citizen
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex items-center border-2 border-foreground bg-card px-3 py-2 flex-1 max-w-sm">
          <Search className="mr-2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm font-medium text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={wardFilter}
            onChange={(e) => setWardFilter(e.target.value)}
            className="border-2 border-foreground bg-card px-3 py-2 text-xs font-bold uppercase text-foreground"
          >
            <option value="">All Wards</option>
            {dynamicWards.map((w) => (
              <option key={w} value={w}>
                {w}
              </option>
            ))}
          </select>
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="border-2 border-foreground bg-card px-3 py-2 text-xs font-bold uppercase text-foreground"
          >
            <option value="">All Risk</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="border-3 border-foreground bg-card shadow-[4px_4px_0px_0px] shadow-foreground/20">
        <Table>
          <TableHeader>
            <TableRow className="border-b-2 border-foreground bg-muted/50">
              <TableHead className="text-xs font-black uppercase tracking-widest">Name</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Contact</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Ward</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Active Issues</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Risk Level</TableHead>
              <TableHead className="text-xs font-black uppercase tracking-widest">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((c) => (
              <TableRow key={c.id} className="border-b border-foreground/10">
                <TableCell>
                  <div>
                    <p className="text-sm font-bold text-foreground">{c.name}</p>
                    <p className="text-[10px] font-mono text-muted-foreground">{c.id}</p>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1.5 font-mono text-sm text-foreground">
                    {showPii ? <Eye className="h-3.5 w-3.5 text-muted-foreground" /> : <Lock className="h-3.5 w-3.5 text-muted-foreground" />}
                    {c.contact}
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-sm font-semibold text-foreground">{c.ward}</span>
                </TableCell>
                <TableCell>
                  <span className="text-sm font-black text-foreground">{c.activeIssues}</span>
                </TableCell>
                <TableCell>
                  <StatusBadge status={c.riskLevel} variant="risk" />
                </TableCell>
                <TableCell>
                  <button
                    onClick={() => setSelectedCitizen(c.id)}
                    className="border-2 border-foreground bg-background px-3 py-1 text-xs font-bold uppercase tracking-wider text-foreground transition-colors hover:bg-foreground hover:text-background"
                  >
                    View
                  </button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t-2 border-foreground px-4 py-3">
          <p className="text-xs font-bold text-muted-foreground">
            Showing {filtered.length} of {allCitizens.length} records
          </p>
          <div className="flex items-center gap-2">
            <button className="flex h-8 w-8 items-center justify-center border-2 border-foreground bg-background text-foreground transition-colors hover:bg-muted">
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="flex h-8 w-8 items-center justify-center border-2 border-foreground bg-foreground text-xs font-bold text-background">
              1
            </span>
            <button className="flex h-8 w-8 items-center justify-center border-2 border-foreground bg-background text-foreground transition-colors hover:bg-muted">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Citizen Profile Panel */}
      <Dialog open={!!selectedCitizen} onOpenChange={() => setSelectedCitizen(null)}>
        <DialogContent className="border-3 border-foreground rounded-none shadow-[8px_8px_0px_0px] shadow-foreground/20 sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-lg font-black uppercase tracking-wider">
              Citizen Profile
            </DialogTitle>
          </DialogHeader>
          {citizen && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="border-2 border-foreground p-3">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Name</p>
                  <p className="mt-1 text-sm font-bold text-foreground">{citizen.name}</p>
                </div>
                <div className="border-2 border-foreground p-3">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">ID</p>
                  <p className="mt-1 text-sm font-mono font-bold text-foreground">{citizen.id}</p>
                </div>
                <div className="border-2 border-foreground p-3">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Contact</p>
                  <p className="mt-1 text-sm font-mono text-foreground flex items-center gap-1.5">
                    {showPii ? <Eye className="h-3.5 w-3.5 text-muted-foreground" /> : <Lock className="h-3.5 w-3.5 text-muted-foreground" />}
                    {citizen.contact}
                  </p>
                </div>
                <div className="border-2 border-foreground p-3">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Ward</p>
                  <p className="mt-1 text-sm font-bold text-foreground">{citizen.ward}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="border-2 border-foreground p-3 flex-1">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Active Issues</p>
                  <p className="mt-1 text-2xl font-black text-foreground">{citizen.activeIssues}</p>
                </div>
                <div className="border-2 border-foreground p-3 flex-1">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Risk Level</p>
                  <div className="mt-1">
                    <StatusBadge status={citizen.riskLevel} variant="risk" />
                  </div>
                </div>
              </div>
              <div className="border-2 border-foreground p-3">
                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Audit Trail</p>
                <div className="mt-2 space-y-2">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="font-mono text-muted-foreground">2026-02-25 14:30</span>
                    <span className="font-semibold text-foreground">Record accessed by Admin</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="font-mono text-muted-foreground">2026-02-20 09:15</span>
                    <span className="font-semibold text-foreground">Contact information updated</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="font-mono text-muted-foreground">2026-02-15 11:00</span>
                    <span className="font-semibold text-foreground">New issue linked: ISS-001</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Add Citizen Modal */}
      <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
        <DialogContent className="border-3 border-foreground rounded-none shadow-[8px_8px_0px_0px] shadow-foreground/20 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-lg font-black uppercase tracking-wider">
              Add New Citizen
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                Full Name
              </label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddCitizen()}
                className={`mt-1 w-full border-2 px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary ${validationErrors.name
                  ? "border-red-500 bg-red-50 text-foreground"
                  : "border-foreground bg-background text-foreground"
                  }`}
                placeholder="Enter full name"
              />
              {validationErrors.name && (
                <p className="mt-1 text-xs text-red-600">{validationErrors.name}</p>
              )}
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                Contact Number
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={newContact}
                  onChange={(e) => setNewContact(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddCitizen()}
                  className={`mt-1 w-full border-2 px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary ${validationErrors.contact
                    ? "border-red-500 bg-red-50 text-foreground"
                    : "border-foreground bg-background text-foreground"
                    }`}
                  placeholder="+91 XXXXX XXXXX or XXXXXXXXXX"
                />
                {!validationErrors.contact && newContact && /^\d{10}$|^\+91\d{10}$|^91\d{10}$|^0\d{10}$/.test(newContact.replace(/[\s\-]/g, "")) && (
                  <CheckCircle className="absolute right-3 top-3 h-5 w-5 text-green-600" />
                )}
              </div>
              {validationErrors.contact && (
                <p className="mt-1 text-xs text-red-600">{validationErrors.contact}</p>
              )}
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                Ward
              </label>
              <div className="relative">
                <select
                  value={newWard}
                  onChange={(e) => {
                    console.log("Ward selected:", e.target.value)
                    setNewWard(e.target.value)
                  }}
                  disabled={loadingWards || wardList.length === 0}
                  className={`mt-1 w-full border-2 px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary ${validationErrors.ward
                    ? "border-red-500 bg-red-50 text-foreground"
                    : wardList.length === 0
                      ? "border-yellow-500 bg-yellow-50 text-foreground"
                      : "border-foreground bg-background text-foreground"
                    }`}
                >
                  <option value="">— Select Ward —</option>
                  {wardList && wardList.length > 0 ? (
                    wardList.map((ward) => (
                      <option key={ward} value={ward}>
                        {ward}
                      </option>
                    ))
                  ) : (
                    <option disabled>Loading wards...</option>
                  )}
                </select>
                {loadingWards && (
                  <Loader2 className="absolute right-3 top-3 h-5 w-5 animate-spin text-muted-foreground" />
                )}
              </div>
              {validationErrors.ward && (
                <p className="mt-1 text-xs text-red-600">{validationErrors.ward}</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <button
              onClick={() => setShowAddModal(false)}
              disabled={isSubmitting}
              className="border-2 border-foreground bg-background px-4 py-2 text-xs font-bold uppercase tracking-wider text-foreground transition-colors hover:bg-muted disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                console.log("Submit button clicked")
                handleAddCitizen()
              }}
              type="button"
              disabled={isSubmitting || wardList.length === 0}
              className="border-2 border-foreground bg-primary px-4 py-2 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-[3px_3px_0px_0px] shadow-foreground/20 transition-all hover:shadow-[5px_5px_0px_0px] hover:-translate-x-0.5 hover:-translate-y-0.5 disabled:opacity-50 flex items-center gap-2 w-full justify-center"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isSubmitting ? "Adding..." : wardList.length === 0 ? "Loading wards..." : "Add Citizen"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
  )
}
