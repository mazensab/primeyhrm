"use client"

import { useEffect, useRef, useState } from "react"
import { Eye, EyeOff, Loader2, Save, Building2, Shield } from "lucide-react"
import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"

function getCookie(name: string) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift()
  }

  return null
}

interface UserProfile {
  id: number
  username: string
  email: string
  full_name?: string
  role?: string
  last_login?: string
  avatar?: string
  phone?: string
}

interface Activity {
  id: number
  action: string
  created_at: string
}

interface SessionItem {
  id: string
  device: string
  location?: string
  last_active: string
}

interface Company {
  id: number
  name: string
}

export default function CompanyProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const [activities, setActivities] = useState<Activity[]>([])
  const [sessions, setSessions] = useState<SessionItem[]>([])
  const [companies, setCompanies] = useState<Company[]>([])

  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [savingProfile, setSavingProfile] = useState(false)

  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [changing, setChanging] = useState(false)

  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)

  const fileInput = useRef<HTMLInputElement>(null)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/whoami/`,
          { credentials: "include" }
        )

        const data = await res.json().catch(() => null)

        if (!res.ok || !data?.user) {
          toast.error("Failed to load profile")
          return
        }

        setUser(data.user)
        setFullName(data?.user?.full_name || "")
        setEmail(data?.user?.email || "")
        setPhone(data?.user?.phone || "")
      } catch {
        toast.error("Connection error")
      } finally {
        setLoading(false)
      }

      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/activity/`,
          { credentials: "include" }
        )

        if (res.ok) {
          const data = await res.json()
          setActivities(Array.isArray(data) ? data : [])
        }
      } catch {}

      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/sessions/`,
          { credentials: "include" }
        )

        if (res.ok) {
          const data = await res.json()
          setSessions(Array.isArray(data) ? data : [])
        }
      } catch {}

      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/system/my-companies/`,
          { credentials: "include" }
        )

        if (res.ok) {
          const data = await res.json()
          setCompanies(Array.isArray(data) ? data : [])
        }
      } catch {}
    }

    load()
  }, [])

  const saveProfile = async () => {
    if (!fullName.trim()) {
      toast.error("Full name is required")
      return
    }

    if (!email.trim()) {
      toast.error("Email is required")
      return
    }

    setSavingProfile(true)

    try {
      const API = process.env.NEXT_PUBLIC_API_URL

      await fetch(`${API}/api/auth/csrf/`, {
        credentials: "include",
      })

      const csrfToken = getCookie("csrftoken")

      if (!csrfToken) {
        throw new Error("CSRF token missing")
      }

      const res = await fetch(`${API}/api/auth/profile/update/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          full_name: fullName,
          email,
          phone,
        }),
      })

      const data = await res.json().catch(() => null)

      if (!res.ok) {
        toast.error(
          data?.error ||
            data?.errors?.email ||
            data?.errors?.full_name ||
            data?.errors?.phone ||
            "Profile update failed"
        )
        return
      }

      toast.success(data?.message || "Profile updated")

      if (user) {
        setUser({
          ...user,
          full_name: data?.user?.full_name || fullName,
          email: data?.user?.email || email,
          phone: data?.user?.phone || phone,
        })
      }
    } catch (error: any) {
      toast.error(error?.message || "Server error")
    } finally {
      setSavingProfile(false)
    }
  }

  const uploadAvatar = async (file: File) => {
    const form = new FormData()
    form.append("avatar", file)

    try {
      const API = process.env.NEXT_PUBLIC_API_URL

      await fetch(`${API}/api/auth/csrf/`, {
        credentials: "include",
      })

      const csrfToken = getCookie("csrftoken")

      if (!csrfToken) {
        toast.error("CSRF token missing")
        return
      }

      const res = await fetch(`${API}/api/auth/avatar/upload/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "X-CSRFToken": csrfToken,
        },
        body: form,
      })

      if (!res.ok) {
        const error = await res.json().catch(() => null)
        toast.error(error?.error || "Avatar upload failed")
        return
      }

      const data = await res.json()

      toast.success(data?.message || "Avatar updated")

      if (data?.avatar && user) {
        setUser({
          ...user,
          avatar: data.avatar,
        })
      }
    } catch {
      toast.error("Upload error")
    }
  }

  const changePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error("Enter passwords")
      return
    }

    setChanging(true)

    try {
      const API = process.env.NEXT_PUBLIC_API_URL

      await fetch(`${API}/api/auth/csrf/`, {
        credentials: "include",
      })

      const csrfToken = getCookie("csrftoken")

      if (!csrfToken) {
        throw new Error("CSRF token missing")
      }

      const res = await fetch(`${API}/api/auth/change-password/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })

      const data = await res.json().catch(() => null)

      if (!res.ok) {
        toast.error(data?.message || data?.error || "Password change failed")
        return
      }

      toast.success(data?.message || "Password updated")

      if (data?.whatsapp_sent) {
        toast.success("WhatsApp notification sent successfully")
      }

      setCurrentPassword("")
      setNewPassword("")
      setShowCurrentPassword(false)
      setShowNewPassword(false)
    } catch (error: any) {
      toast.error(error?.message || "Server error")
    } finally {
      setChanging(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <Card className="border-border/60">
          <CardContent className="flex min-h-[220px] items-center justify-center">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading profile...
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="p-6">
        <Card className="border-destructive/20">
          <CardContent className="flex min-h-[220px] items-center justify-center text-sm text-muted-foreground">
            User not found
          </CardContent>
        </Card>
      </div>
    )
  }

  const initials = (user.full_name || user.username || "U").charAt(0).toUpperCase()

  return (
    <div className="space-y-6 p-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">My Profile</h1>
        <p className="text-sm text-muted-foreground">
          Manage your company account information, security, sessions, and activity.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Card>
            <CardContent className="flex flex-col gap-5 pt-6 sm:flex-row sm:items-center">
              <Avatar className="h-20 w-20 overflow-hidden border">
                {user.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.username}
                    className="h-full w-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <AvatarFallback className="text-xl">
                    {initials}
                  </AvatarFallback>
                )}
              </Avatar>

              <div className="min-w-0 flex-1 space-y-2">
                <div>
                  <h2 className="truncate text-xl font-semibold">
                    {user.full_name || user.username}
                  </h2>
                  <p className="truncate text-sm text-muted-foreground">
                    {user.email}
                  </p>
                  {phone ? (
                    <p className="truncate text-sm text-muted-foreground">
                      {phone}
                    </p>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  {user.role ? (
                    <Badge variant="secondary" className="gap-1">
                      <Shield className="h-3.5 w-3.5" />
                      {user.role}
                    </Badge>
                  ) : null}

                  {companies.length > 0 ? (
                    <Badge variant="outline" className="gap-1">
                      <Building2 className="h-3.5 w-3.5" />
                      {companies[0]?.name || "Company User"}
                    </Badge>
                  ) : (
                    <Badge variant="outline">Company User</Badge>
                  )}
                </div>

                <div className="pt-1">
                  <input
                    type="file"
                    ref={fileInput}
                    className="hidden"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (!file) return
                      uploadAvatar(file)
                    }}
                  />

                  <Button
                    variant="outline"
                    onClick={() => fileInput.current?.click()}
                  >
                    Upload Avatar
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Username</label>
                <Input value={user.username} disabled />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Full Name</label>
                  <Input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Enter full name"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter email"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Mobile Number</label>
                <Input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Enter mobile number"
                  dir="ltr"
                />
              </div>

              <Button onClick={saveProfile} disabled={savingProfile}>
                {savingProfile ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Save Changes
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Security</CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="relative">
                <Input
                  type={showCurrentPassword ? "text" : "password"}
                  placeholder="Current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="pr-12"
                />

                <button
                  type="button"
                  onClick={() => setShowCurrentPassword((prev) => !prev)}
                  className="absolute right-3 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground"
                  aria-label={
                    showCurrentPassword ? "Hide current password" : "Show current password"
                  }
                >
                  {showCurrentPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>

              <div className="relative">
                <Input
                  type={showNewPassword ? "text" : "password"}
                  placeholder="New password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="pr-12"
                />

                <button
                  type="button"
                  onClick={() => setShowNewPassword((prev) => !prev)}
                  className="absolute right-3 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground"
                  aria-label={
                    showNewPassword ? "Hide new password" : "Show new password"
                  }
                >
                  {showNewPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>

              <Button onClick={changePassword} disabled={changing}>
                {changing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Changing...
                  </>
                ) : (
                  "Change Password"
                )}
              </Button>

              <Separator />

              <div className="text-sm text-muted-foreground">
                Last Login:{" "}
                {user.last_login
                  ? new Date(user.last_login).toLocaleString()
                  : "First Login"}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>

            <CardContent className="space-y-3">
              {activities.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No activity
                </p>
              ) : (
                activities.map((activity) => (
                  <div
                    key={activity.id}
                    className="space-y-1 rounded-lg border p-3"
                  >
                    <p className="text-sm font-medium leading-5">
                      {activity.action}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(activity.created_at).toLocaleString()}
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Active Sessions</CardTitle>
            </CardHeader>

            <CardContent className="space-y-3">
              {sessions.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No active sessions
                </p>
              ) : (
                sessions.map((sessionItem) => (
                  <div
                    key={sessionItem.id}
                    className="rounded-lg border p-3"
                  >
                    <p className="text-sm font-medium">
                      {sessionItem.device} {sessionItem.location || ""}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {new Date(sessionItem.last_active).toLocaleString()}
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Managed Companies</CardTitle>
            </CardHeader>

            <CardContent className="space-y-3">
              {companies.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No companies found
                </p>
              ) : (
                companies.map((company) => (
                  <div
                    key={company.id}
                    className="rounded-lg border p-3 text-sm"
                  >
                    {company.name}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}