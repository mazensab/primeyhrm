"use client"

import { useEffect, useMemo, useState } from "react"
import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"

import { Input } from "@/components/ui/input"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

import {
  Bell,
  Search,
  CheckCircle,
  CheckCheck,
  Loader2
} from "lucide-react"

// ======================================================
// CSRF Helper
// ======================================================

function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null
  }

  return null
}

// ======================================================
// API Helper
// ======================================================

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "")
}

function resolveApiBase(): string {
  const envApi = process.env.NEXT_PUBLIC_API_URL?.trim()

  if (envApi) {
    return `${trimTrailingSlash(envApi)}/api`
  }

  if (typeof window !== "undefined") {
    return `${trimTrailingSlash(window.location.origin)}/api`
  }

  return "/api"
}

// ======================================================
// Types
// ======================================================

interface Notification {
  id: number
  title: string
  message: string
  created_at: string
  is_read: boolean
}

// ======================================================
// Helpers
// ======================================================

function formatDate(date: string) {
  try {
    return new Date(date).toLocaleString("ar-SA", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    })
  } catch {
    return date
  }
}

// ======================================================
// Page
// ======================================================

export default function SystemNotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [filtered, setFiltered] = useState<Notification[]>([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)

  const API = useMemo(() => resolveApiBase(), [])

  // ======================================================
  // Fetch Notifications
  // ======================================================

  async function fetchNotifications() {
    try {
      setLoading(true)

      const res = await fetch(`${API}/system/notifications/`, {
        credentials: "include",
        cache: "no-store"
      })

      if (!res.ok) {
        throw new Error(`Failed to load notifications: ${res.status}`)
      }

      const data = await res.json()

      const notificationsData =
        Array.isArray(data) ? data :
        Array.isArray(data?.results) ? data.results :
        Array.isArray(data?.notifications) ? data.notifications :
        []

      setNotifications(notificationsData)
      setFiltered(notificationsData)

    } catch (error) {
      console.error("Failed to load notifications", error)
      toast.error("Failed to load notifications")
      setNotifications([])
      setFiltered([])

    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchNotifications()
  }, [API])

  // ======================================================
  // Search
  // ======================================================

  useEffect(() => {
    const q = search.trim().toLowerCase()

    if (!q) {
      setFiltered(notifications)
      return
    }

    const result = notifications.filter((n) =>
      n.title.toLowerCase().includes(q) ||
      n.message.toLowerCase().includes(q)
    )

    setFiltered(result)
  }, [search, notifications])

  // ======================================================
  // Mark Read
  // ======================================================

  async function markRead(id: number) {
    try {
      setProcessing(true)

      const csrfToken = getCookie("csrftoken")

      const res = await fetch(`${API}/system/notifications/${id}/read/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || ""
        }
      })

      if (!res.ok) {
        throw new Error(`Failed to mark notification as read: ${res.status}`)
      }

      toast.success("تم تعليم الإشعار كمقروء")
      await fetchNotifications()

    } catch (error) {
      console.error("Failed to mark notification as read", error)
      toast.error("فشل تحديث الإشعار")

    } finally {
      setProcessing(false)
    }
  }

  // ======================================================
  // Mark All Read
  // ======================================================

  async function markAllRead() {
    try {
      setProcessing(true)

      const csrfToken = getCookie("csrftoken")

      const res = await fetch(`${API}/system/notifications/read-all/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || ""
        }
      })

      if (!res.ok) {
        throw new Error(`Failed to mark all notifications as read: ${res.status}`)
      }

      toast.success("تم تعليم جميع الإشعارات كمقروءة")
      await fetchNotifications()

    } catch (error) {
      console.error("Failed to mark all notifications as read", error)
      toast.error("فشل تحديث الإشعارات")

    } finally {
      setProcessing(false)
    }
  }

  // ======================================================
  // Stats
  // ======================================================

  const unreadCount = notifications.filter((n) => !n.is_read).length

  // ======================================================
  // UI
  // ======================================================

  return (
    <div className="space-y-6">
      {/* ====================================================== */}
      {/* Header */}
      {/* ====================================================== */}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bell className="h-6 w-6 text-muted-foreground" />

          <div>
            <h1 className="text-2xl font-bold">
              Notifications
            </h1>

            <p className="text-muted-foreground text-sm">
              All platform notifications
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="secondary">
            {unreadCount} Unread
          </Badge>

          <Button
            variant="outline"
            size="sm"
            onClick={markAllRead}
            disabled={processing || unreadCount <= 0}
          >
            {processing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <CheckCheck className="mr-2 h-4 w-4" />
            )}

            Mark all read
          </Button>
        </div>
      </div>

      {/* ====================================================== */}
      {/* Search */}
      {/* ====================================================== */}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Search Notifications</CardTitle>

          <div className="relative w-80">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />

            <Input
              placeholder="Search notifications..."
              className="pl-8"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </CardHeader>
      </Card>

      {/* ====================================================== */}
      {/* Table */}
      {/* ====================================================== */}

      <Card>
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading notifications...
            </div>
          ) : filtered.length === 0 ? (
            <p className="text-muted-foreground">
              No notifications found
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Message</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {filtered.map((n) => (
                  <TableRow key={n.id}>
                    <TableCell className="font-medium">
                      {n.title}
                    </TableCell>

                    <TableCell>
                      {n.message}
                    </TableCell>

                    <TableCell>
                      {formatDate(n.created_at)}
                    </TableCell>

                    <TableCell>
                      {n.is_read ? (
                        <Badge variant="secondary">
                          Read
                        </Badge>
                      ) : (
                        <Badge variant="destructive">
                          Unread
                        </Badge>
                      )}
                    </TableCell>

                    <TableCell className="text-right">
                      {!n.is_read && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => void markRead(n.id)}
                          disabled={processing}
                        >
                          <CheckCircle className="mr-1 h-4 w-4" />
                          Mark read
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}