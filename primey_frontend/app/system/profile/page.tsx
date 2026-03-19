"use client"

import { useEffect, useState, useRef } from "react"
import { Eye, EyeOff, Loader2, Save } from "lucide-react"
import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
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
  phone?: string
  role?: string
  last_login?: string
  avatar?: string
}

interface Activity {
  id: number
  action: string
  created_at: string
}

interface Session {
  id: string
  device: string
  location?: string
  last_active: string
}

interface Company {
  id: number
  name: string
}

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const [activities, setActivities] = useState<Activity[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
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

  /* =========================================
     Load Profile Data
  ========================================= */
  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/whoami/`,
          { credentials: "include" }
        )

        const data = await res.json()

        if (!res.ok) {
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

      /* Load activity */
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/activity/`,
          { credentials: "include" }
        )

        if (res.ok) {
          setActivities(await res.json())
        }
      } catch {}

      /* Load sessions */
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/sessions/`,
          { credentials: "include" }
        )

        if (res.ok) {
          setSessions(await res.json())
        }
      } catch {}

      /* Load companies */
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/system/my-companies/`,
          { credentials: "include" }
        )

        if (res.ok) {
          setCompanies(await res.json())
        }
      } catch {}
    }

    load()
  }, [])

  /* =========================================
     Save Profile
  ========================================= */
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
        credentials: "include"
      })

      const csrfToken = getCookie("csrftoken")

      if (!csrfToken) {
        throw new Error("CSRF token missing")
      }

      const res = await fetch(
        `${API}/api/auth/profile/update/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          },
          body: JSON.stringify({
            full_name: fullName,
            email: email,
            phone: phone
          })
        }
      )

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

  /* =========================================
     Upload Avatar
  ========================================= */
  const uploadAvatar = async (file: File) => {
    const form = new FormData()
    form.append("avatar", file)

    try {
      const API = process.env.NEXT_PUBLIC_API_URL

      await fetch(`${API}/api/auth/csrf/`, {
        credentials: "include"
      })

      const csrfToken = getCookie("csrftoken")

      if (!csrfToken) {
        toast.error("CSRF token missing")
        return
      }

      const res = await fetch(
        `${API}/api/auth/avatar/upload/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "X-CSRFToken": csrfToken
          },
          body: form
        }
      )

      if (!res.ok) {
        const error = await res.json().catch(() => null)
        toast.error(error?.error || "Avatar upload failed")
        return
      }

      const data = await res.json()

      toast.success(data?.message || "Avatar updated")

      if (data.avatar && user) {
        setUser({
          ...user,
          avatar: data.avatar
        })
      }
    } catch {
      toast.error("Upload error")
    }
  }

  /* =========================================
     Change Password
  ========================================= */
  const changePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error("Enter passwords")
      return
    }

    setChanging(true)

    try {
      const API = process.env.NEXT_PUBLIC_API_URL

      await fetch(`${API}/api/auth/csrf/`, {
        credentials: "include"
      })

      const csrfToken = getCookie("csrftoken")

      if (!csrfToken) {
        throw new Error("CSRF token missing")
      }

      const res = await fetch(
        `${API}/api/auth/change-password/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          },
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
          })
        }
      )

      const data = await res.json().catch(() => null)

      if (!res.ok) {
        toast.error(
          data?.message ||
          data?.error ||
          "Password change failed"
        )
        return
      }

      toast.success(
        data?.message || "Password updated"
      )

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
    return <div className="p-6">Loading profile...</div>
  }

  if (!user) {
    return <div className="p-6">User not found</div>
  }

  const initials =
    (user.full_name || user.username || "U")
      .charAt(0)
      .toUpperCase()

  return (
    <div className="max-w-4xl space-y-6 p-6">
      {/* ============================= */}
      {/* Profile Header */}
      {/* ============================= */}
      <Card>
        <CardContent className="flex items-center gap-6 pt-6">
          <Avatar className="h-20 w-20 overflow-hidden">
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

          <div className="space-y-1">
            <h2 className="text-xl font-semibold">
              {user.full_name || user.username}
            </h2>

            <p className="text-sm text-muted-foreground">
              {user.email}
            </p>

            {user.phone ? (
              <p className="text-sm text-muted-foreground">
                {user.phone}
              </p>
            ) : null}

            {user.role && (
              <Badge className="mt-1">
                {user.role}
              </Badge>
            )}

            <div className="pt-2">
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

      {/* ============================= */}
      {/* Account Info */}
      {/* ============================= */}
      <Card>
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm">Username</label>
            <Input value={user.username} disabled />
          </div>

          <div className="space-y-2">
            <label className="text-sm">Email</label>
            <Input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm">Phone</label>
            <Input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+9665XXXXXXXX"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm">Full Name</label>
            <Input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>

          <Button
            onClick={saveProfile}
            disabled={savingProfile}
          >
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

      {/* ============================= */}
      {/* Change Password */}
      {/* ============================= */}
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
              aria-label={showCurrentPassword ? "Hide current password" : "Show current password"}
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
              aria-label={showNewPassword ? "Hide new password" : "Show new password"}
            >
              {showNewPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>

          <Button
            onClick={changePassword}
            disabled={changing}
          >
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

      {/* ============================= */}
      {/* Recent Activity */}
      {/* ============================= */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>

        <CardContent className="space-y-2">
          {activities.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No activity
            </p>
          )}

          {activities.map((a) => (
            <div
              key={a.id}
              className="flex justify-between text-sm"
            >
              <span>{a.action}</span>
              <span className="text-muted-foreground">
                {new Date(a.created_at).toLocaleString()}
              </span>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* ============================= */}
      {/* Sessions */}
      {/* ============================= */}
      <Card>
        <CardHeader>
          <CardTitle>Active Sessions</CardTitle>
        </CardHeader>

        <CardContent className="space-y-2">
          {sessions.map((s) => (
            <div
              key={s.id}
              className="flex justify-between text-sm"
            >
              <span>
                {s.device}{" "}
                {s.location || ""}
              </span>

              <span className="text-muted-foreground">
                {new Date(s.last_active).toLocaleString()}
              </span>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* ============================= */}
      {/* Managed Companies */}
      {/* ============================= */}
      <Card>
        <CardHeader>
          <CardTitle>Managed Companies</CardTitle>
        </CardHeader>

        <CardContent className="space-y-2">
          {companies.map((c) => (
            <div
              key={c.id}
              className="text-sm"
            >
              {c.name}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}