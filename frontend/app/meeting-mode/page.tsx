"use client"

import { useState, useRef } from "react"
import { Upload, Loader2, CheckCircle2, AlertCircle, FileText, CheckSquare, Users, AlertTriangle } from "lucide-react"
import { processAsMeetingMode } from "@/lib/services"
import type { MeetingModeResponse } from "@/lib/types"

export default function MeetingModePage() {
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<MeetingModeResponse | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const processFile = async (file: File) => {
    if (!file.type.startsWith("audio/")) {
      setError("Please upload an audio file (.mp3, .wav, .webm, .flac, .ogg, .aac)")
      return
    }

    if (file.size > 25 * 1024 * 1024) {
      setError("File size exceeds 25 MB limit")
      return
    }

    setIsProcessing(true)
    setError(null)
    setResult(null)

    try {
      const res = await processAsMeetingMode(file, file.name)
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process meeting audio")
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) processFile(file)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.currentTarget.files?.[0]
    if (file) processFile(file)
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const reset = () => {
    setResult(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  return (
    <main className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-black uppercase tracking-wider text-foreground">
          Meeting Mode
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload a meeting recording and auto-generate Minutes of Meeting with action items
        </p>
      </div>

      {!result ? (
        <div className="border-3 border-foreground bg-card p-8 shadow-[4px_4px_0px_0px] shadow-foreground/20">
          {/* Upload Area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleUploadClick}
            className={`cursor-pointer rounded border-2 border-dashed p-8 text-center transition-colors ${
              isDragging
                ? "border-primary bg-primary/10"
                : "border-foreground/30 hover:border-foreground hover:bg-muted/30"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              className="hidden"
              disabled={isProcessing}
            />

            <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
            <p className="mt-4 text-sm font-bold uppercase tracking-wider text-foreground">
              Drop audio file or click to upload
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              Supported: MP3, WAV, WebM, FLAC, OGG, AAC (Max 25 MB)
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mt-4 border-2 border-red-600 bg-red-50 p-4 dark:bg-red-950">
              <div className="flex gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />
                <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
              </div>
            </div>
          )}

          {/* Processing */}
          {isProcessing && (
            <div className="mt-6 border-2 border-blue-600 bg-blue-50 p-6 text-center dark:bg-blue-950">
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-600" />
              <p className="mt-3 font-bold uppercase tracking-wider text-blue-700 dark:text-blue-200">
                Processing Meeting Audio...
              </p>
              <p className="mt-1 text-xs text-blue-600 dark:text-blue-300">
                Transcribing, extracting summary, decisions, and action items
              </p>
            </div>
          )}
        </div>
      ) : (
        // Results
        <>
          <div className="border-3 border-green-600 bg-green-50 p-4 dark:bg-green-950">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <p className="font-bold uppercase tracking-wider text-green-700 dark:text-green-200">
                Meeting processed successfully!
              </p>
            </div>
          </div>

          {/* Tabs for Transcript, Extraction, etc */}
          <div className="space-y-6">
            {/* Transcript */}
            <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
              <h2 className="text-lg font-black uppercase tracking-wider text-foreground mb-3">
                Transcript
              </h2>
              <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">
                Provider: {result.provider}
              </p>
              <div className="border-2 border-foreground/20 bg-background p-4 max-h-48 overflow-y-auto">
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{result.transcript}</p>
              </div>
            </div>

            {/* Summary */}
            <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
              <h2 className="text-lg font-black uppercase tracking-wider text-foreground mb-3">
                Summary
              </h2>
              <p className="text-sm text-foreground leading-relaxed">{result.extraction.summary}</p>
            </div>

            {/* Key Decisions */}
            {result.extraction.key_decisions.length > 0 && (
              <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
                <h2 className="flex items-center gap-2 text-lg font-black uppercase tracking-wider text-foreground mb-3">
                  <CheckCircle2 className="h-5 w-5" />
                  Key Decisions
                </h2>
                <ul className="space-y-2">
                  {result.extraction.key_decisions.map((decision, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-foreground">
                      <span className="mt-1 h-2 w-2 shrink-0 bg-foreground" />
                      <span>{decision}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action Items */}
            {result.extraction.action_items.length > 0 && (
              <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
                <h2 className="flex items-center gap-2 text-lg font-black uppercase tracking-wider text-foreground mb-3">
                  <CheckSquare className="h-5 w-5" />
                  Action Items ({result.extraction.action_items.length})
                </h2>
                <div className="space-y-3">
                  {result.extraction.action_items.map((item, i) => (
                    <div key={i} className="border-l-4 border-orange-600 bg-orange-50 p-3 dark:bg-orange-950">
                      <p className="font-bold text-sm text-foreground">{item.task}</p>
                      <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="font-bold uppercase text-muted-foreground">Department:</span>
                          <p className="text-foreground">{item.department}</p>
                        </div>
                        <div>
                          <span className="font-bold uppercase text-muted-foreground">Deadline:</span>
                          <p className="text-foreground">{item.deadline || "TBD"}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="mt-3 text-xs text-muted-foreground font-bold uppercase">
                  {result.created_action_requests} action requests created in system
                </p>
              </div>
            )}

            {/* Departments */}
            {result.extraction.departments.length > 0 && (
              <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
                <h2 className="flex items-center gap-2 text-lg font-black uppercase tracking-wider text-foreground mb-3">
                  <Users className="h-5 w-5" />
                  Departments Involved
                </h2>
                <div className="flex flex-wrap gap-2">
                  {result.extraction.departments.map((dept, i) => (
                    <span
                      key={i}
                      className="border-2 border-foreground bg-foreground px-3 py-1 text-xs font-bold uppercase text-background"
                    >
                      {dept}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Priority Issues */}
            {result.extraction.priority_issues.length > 0 && (
              <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
                <h2 className="flex items-center gap-2 text-lg font-black uppercase tracking-wider text-foreground mb-3">
                  <AlertTriangle className="h-5 w-5" />
                  Priority Issues
                </h2>
                <ul className="space-y-2">
                  {result.extraction.priority_issues.map((issue, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-foreground">
                      <span className="mt-1 h-2 w-2 shrink-0 bg-red-600" />
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Created Items */}
            <div className="grid gap-3 sm:grid-cols-2">
              {result.meeting_draft_id && (
                <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="h-5 w-5" />
                    <p className="font-bold uppercase tracking-wider text-foreground">Generated Draft</p>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">Minutes of Meeting</p>
                  <p className="font-mono text-xs text-foreground break-all">{result.meeting_draft_id}</p>
                </div>
              )}
              <div className="border-3 border-foreground bg-card p-4 shadow-[4px_4px_0px_0px] shadow-foreground/20">
                <div className="flex items-center gap-2 mb-2">
                  <CheckSquare className="h-5 w-5" />
                  <p className="font-bold uppercase tracking-wider text-foreground">Action Requests</p>
                </div>
                <p className="text-xs text-muted-foreground mb-2">Created in system</p>
                <p className="text-2xl font-black text-foreground">{result.created_action_requests}</p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={reset}
              className="border-2 border-foreground bg-background px-4 py-2 text-xs font-bold uppercase tracking-wider text-foreground hover:bg-muted transition-colors"
            >
              Process another meeting
            </button>
          </div>
        </>
      )}
    </main>
  )
}
