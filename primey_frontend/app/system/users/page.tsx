"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Search,
  UserPlus,
  Users,
  Mail,
  Phone,
  RefreshCcw,
  MoreHorizontal,
  CheckCircle2,
  XCircle,
  Shield,
  Headset,
  Crown,
  UserCog,
  KeyRound,
  Loader2,
  Eye,
  CalendarDays,
  Clock3
} from "lucide-react"

import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card"

import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from "@/components/ui/dialog"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

/* ======================================================
   API Config
====================================================== */

function normalizeApiBase(raw?: string) {
  const fallback = "http://localhost:8000/api"
  const value = (raw || fallback).replace(/\/$/, "")

  if (value.endsWith("/api")) return value
  return `${value}/api`
}

const API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_URL)

/* ======================================================
   Types
====================================================== */

type InternalRole = "SUPER_ADMIN" | "SYSTEM_ADMIN" | "SUPPORT"
type UserStatus = "ACTIVE" | "INACTIVE"

interface SystemUser {
  id: number
  full_name: string
  username: string
  email: string
  phone: string
  avatar?: string | null
  role: InternalRole
  status: UserStatus
  last_login: string | null
  created_at: string | null
}

interface RoleOption {
  code: InternalRole
  label: string
  description?: string
}

interface UsersListResponse {
  success: boolean
  users?: SystemUser[]
  count?: number
  roles?: RoleOption[]
  error?: string
}

interface RolesResponse {
  success: boolean
  roles?: RoleOption[]
  error?: string
}

interface GenericApiResponse {
  success: boolean
  message?: string
  error?: string
  details?: string
  temporary_password?: string
  user?: SystemUser
  errors?: Record<string, string>
}

/* ======================================================
   Helpers
====================================================== */

function getCookie(name: string): string {
  if (typeof document === "undefined") return ""

  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : ""
}

function formatDate(value: string | null) {
  if (!value) return "--"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit"
  }).format(date)
}

function formatDateTime(value: string | null) {
  if (!value) return "Never logged in"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date)
}

function getRoleLabel(role: InternalRole) {
  switch (role) {
    case "SUPER_ADMIN":
      return "Super Admin"
    case "SYSTEM_ADMIN":
      return "System Admin"
    case "SUPPORT":
      return "Support"
    default:
      return role
  }
}

function getRoleIcon(role: InternalRole) {
  switch (role) {
    case "SUPER_ADMIN":
      return <Crown className="h-4 w-4" />
    case "SYSTEM_ADMIN":
      return <Shield className="h-4 w-4" />
    case "SUPPORT":
      return <Headset className="h-4 w-4" />
    default:
      return <UserCog className="h-4 w-4" />
  }
}

function getRoleBadgeClass(role: InternalRole) {
  switch (role) {
    case "SUPER_ADMIN":
      return "border-yellow-500/30 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300"
    case "SYSTEM_ADMIN":
      return "border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300"
    case "SUPPORT":
      return "border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-300"
    default:
      return "border-border"
  }
}

function getStatusBadge(status: UserStatus) {
  if (status === "ACTIVE") {
    return (
      <Badge className="gap-1 border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
        <CheckCircle2 className="h-3.5 w-3.5" />
        Active
      </Badge>
    )
  }

  return (
    <Badge className="gap-1 border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300">
      <XCircle className="h-3.5 w-3.5" />
      Inactive
    </Badge>
  )
}

function getInitials(name: string) {
  return (
    name
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "U"
  )
}

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  valueClassName
}: {
  title: string
  value: number
  description: string
  icon: React.ComponentType<{ className?: string }>
  valueClassName?: string
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{title}</CardTitle>
          <Icon className="h-4 w-4 text-muted-foreground" />
        </div>
      </CardHeader>

      <CardContent>
        <div className={cn("text-2xl font-bold", valueClassName)}>{value}</div>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )
}

/* ======================================================
   Page
====================================================== */

export default function SystemUsersPage() {
  const [users, setUsers] = useState<SystemUser[]>([])
  const [roles, setRoles] = useState<RoleOption[]>([
    { code: "SUPER_ADMIN", label: "Super Admin" },
    { code: "SYSTEM_ADMIN", label: "System Admin" },
    { code: "SUPPORT", label: "Support" }
  ])

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState<"ALL" | InternalRole>("ALL")
  const [statusFilter, setStatusFilter] = useState<"ALL" | UserStatus>("ALL")
  const [openCreateDialog, setOpenCreateDialog] = useState(false)
  const [openProfileDialog, setOpenProfileDialog] = useState(false)
  const [selectedUser, setSelectedUser] = useState<SystemUser | null>(null)

  const [fullName, setFullName] = useState("")
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [role, setRole] = useState<InternalRole>("SYSTEM_ADMIN")
  const [status, setStatus] = useState<UserStatus>("ACTIVE")
  const [submitting, setSubmitting] = useState(false)
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null)
  const [resetUserId, setResetUserId] = useState<number | null>(null)
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [openResetDialog, setOpenResetDialog] = useState(false)

  const fetchUsers = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) setLoading(true)
      else setRefreshing(true)

      const response = await fetch(`${API_BASE}/system/users/`, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json"
        }
      })

      const data: UsersListResponse = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Failed to load system users")
      }

      setUsers(data.users || [])

      if (data.roles?.length) {
        setRoles(data.roles)
      }
    } catch (error) {
      console.error("Fetch system users error:", error)
      toast.error("Failed to load system users")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  const fetchRoles = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/system/users/roles/`, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json"
        }
      })

      const data: RolesResponse = await response.json()

      if (!response.ok || !data.success) {
        return
      }

      if (data.roles?.length) {
        setRoles(data.roles)
      }
    } catch (error) {
      console.error("Fetch roles error:", error)
    }
  }, [])

  useEffect(() => {
    fetchUsers(true)
    fetchRoles()
  }, [fetchUsers, fetchRoles])

  const filteredUsers = useMemo(() => {
    const keyword = search.trim().toLowerCase()

    return users.filter((user) => {
      const matchesSearch =
        !keyword ||
        user.full_name.toLowerCase().includes(keyword) ||
        user.username.toLowerCase().includes(keyword) ||
        user.email.toLowerCase().includes(keyword) ||
        (user.phone || "").toLowerCase().includes(keyword)

      const matchesRole = roleFilter === "ALL" ? true : user.role === roleFilter
      const matchesStatus =
        statusFilter === "ALL" ? true : user.status === statusFilter

      return matchesSearch && matchesRole && matchesStatus
    })
  }, [users, search, roleFilter, statusFilter])

  const total = users.length
  const active = users.filter((u) => u.status === "ACTIVE").length
  const inactive = users.filter((u) => u.status === "INACTIVE").length
  const superAdmins = users.filter((u) => u.role === "SUPER_ADMIN").length
  const systemAdmins = users.filter((u) => u.role === "SYSTEM_ADMIN").length
  const supportUsers = users.filter((u) => u.role === "SUPPORT").length

  function resetForm() {
    setFullName("")
    setUsername("")
    setEmail("")
    setPhone("")
    setRole("SYSTEM_ADMIN")
    setStatus("ACTIVE")
  }

  function openUserProfile(user: SystemUser) {
    setSelectedUser(user)
    setOpenProfileDialog(true)
  }

  async function handleCreateUser() {
    const safeFullName = fullName.trim()
    const safeUsername = username.trim().toLowerCase()
    const safeEmail = email.trim().toLowerCase()
    const safePhone = phone.trim()

    if (!safeFullName) {
      toast.error("Full name is required")
      return
    }

    if (!safeUsername) {
      toast.error("Username is required")
      return
    }

    if (safeUsername.length < 3) {
      toast.error("Username must be at least 3 characters")
      return
    }

    if (!safeEmail || !isValidEmail(safeEmail)) {
      toast.error("Please enter a valid email address")
      return
    }

    setSubmitting(true)

    try {
      const csrfToken = getCookie("csrftoken")

      const response = await fetch(`${API_BASE}/system/users/create/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({
          full_name: safeFullName,
          username: safeUsername,
          email: safeEmail,
          phone: safePhone,
          role,
          status
        })
      })

      const data: GenericApiResponse = await response.json()

      if (!response.ok || !data.success) {
        const firstError =
          data.errors && Object.keys(data.errors).length > 0
            ? data.errors[Object.keys(data.errors)[0]]
            : null

        throw new Error(firstError || data.error || "Failed to create system user")
      }

      toast.success("User created successfully", {
        description: data.temporary_password
          ? `Temporary password: ${data.temporary_password}`
          : "The user was saved successfully."
      })

      resetForm()
      setOpenCreateDialog(false)
      await fetchUsers(false)
    } catch (error) {
      console.error("Create system user error:", error)
      toast.error(error instanceof Error ? error.message : "Failed to create user")
    } finally {
      setSubmitting(false)
    }
  }

  async function handleToggleStatus(userId: number) {
    try {
      setActionLoadingId(userId)

      const csrfToken = getCookie("csrftoken")

      const response = await fetch(`${API_BASE}/system/users/toggle-status/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ user_id: userId })
      })

      const data: GenericApiResponse = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Failed to update user status")
      }

      toast.success("User status updated successfully")
      await fetchUsers(false)
    } catch (error) {
      console.error("Toggle system user status error:", error)
      toast.error(error instanceof Error ? error.message : "Failed to update user status")
    } finally {
      setActionLoadingId(null)
    }
  }

  async function handleChangeRole(userId: number, newRole: InternalRole) {
    try {
      setActionLoadingId(userId)

      const csrfToken = getCookie("csrftoken")

      const response = await fetch(`${API_BASE}/system/users/change-role/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({
          user_id: userId,
          role: newRole
        })
      })

      const data: GenericApiResponse = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Failed to update user role")
      }

      toast.success("User role updated successfully")
      await fetchUsers(false)
    } catch (error) {
      console.error("Change system user role error:", error)
      toast.error(error instanceof Error ? error.message : "Failed to update user role")
    } finally {
      setActionLoadingId(null)
    }
  }

  async function handleResetPassword() {
    if (!resetUserId) return

    if (!newPassword || newPassword.length < 6) {
      toast.error("Password must be at least 6 characters")
      return
    }

    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match")
      return
    }

    try {
      setActionLoadingId(resetUserId)

      const csrfToken = getCookie("csrftoken")

      const response = await fetch(`${API_BASE}/system/users/reset-password/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({
          user_id: resetUserId,
          new_password: newPassword
        })
      })

      const data: GenericApiResponse = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Failed to change password")
      }

      toast.success("Password updated successfully")

      setOpenResetDialog(false)
      setNewPassword("")
      setConfirmPassword("")
      setResetUserId(null)
    } catch (error) {
      console.error(error)
      toast.error("Failed to update password")
    } finally {
      setActionLoadingId(null)
    }
  }

  function handleResetFilters() {
    setSearch("")
    setRoleFilter("ALL")
    setStatusFilter("ALL")
    toast.success("Filters reset successfully")
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col items-start justify-between gap-4 lg:flex-row">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">System Users</h1>
          <p className="text-muted-foreground">
            Manage internal platform users such as Super Admin, System Admin, and Support
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => fetchUsers(false)}
            disabled={refreshing}
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCcw className="h-4 w-4" />
            )}
            Refresh
          </Button>

          <Dialog open={openCreateDialog} onOpenChange={setOpenCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <UserPlus className="h-4 w-4" />
                Add User
              </Button>
            </DialogTrigger>

            <DialogContent className="sm:max-w-3xl">
              <DialogHeader>
                <DialogTitle>Add Internal User</DialogTitle>
                <DialogDescription>
                  This will create a real internal platform user and assign the selected role.
                </DialogDescription>
              </DialogHeader>

              <div className="grid grid-cols-1 gap-6 py-2 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Full Name</label>
                      <Input
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="Example: Ahmed Alharbi"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Username</label>
                      <Input
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Example: ahmed.admin"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Email</label>
                      <Input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="example@primeyhrm.com"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Phone</label>
                      <Input
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="+9665xxxxxxxx"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Role</label>
                      <Select
                        value={role}
                        onValueChange={(value) => setRole(value as InternalRole)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select role" />
                        </SelectTrigger>
                        <SelectContent>
                          {roles.map((item) => (
                            <SelectItem key={item.code} value={item.code}>
                              {item.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Status</label>
                      <Select
                        value={status}
                        onValueChange={(value) => setStatus(value as UserStatus)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select status" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ACTIVE">Active</SelectItem>
                          <SelectItem value="INACTIVE">Inactive</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                <Card className="h-fit">
                  <CardHeader>
                    <CardTitle className="text-sm">Role Summary</CardTitle>
                    <CardDescription>Quick preview</CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <Badge className={cn("gap-1", getRoleBadgeClass(role))}>
                      {getRoleIcon(role)}
                      {getRoleLabel(role)}
                    </Badge>

                    <Separator />

                    <div className="space-y-3 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Status</span>
                        <span className="font-medium">
                          {status === "ACTIVE" ? "Active" : "Inactive"}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Binding</span>
                        <span className="font-medium text-emerald-600">Live</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    resetForm()
                    setOpenCreateDialog(false)
                  }}
                >
                  Cancel
                </Button>

                <Button type="button" onClick={handleCreateUser} disabled={submitting}>
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <UserPlus className="h-4 w-4" />
                      Save User
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Users"
          value={total}
          description="All internal platform users"
          icon={Users}
        />

        <StatCard
          title="Active"
          value={active}
          description="Currently active accounts"
          icon={CheckCircle2}
          valueClassName="text-green-600"
        />

        <StatCard
          title="System Admin"
          value={systemAdmins}
          description="Operational management access"
          icon={Shield}
          valueClassName="text-blue-600"
        />

        <StatCard
          title="Support"
          value={supportUsers}
          description="Support and follow-up team"
          icon={Headset}
          valueClassName="text-violet-600"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-1">
        <Card>
          <CardHeader>
            <CardTitle>Access Overview</CardTitle>
            <CardDescription>Internal access distribution</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span>Super Admin</span>
              <Badge className="border-yellow-500/30 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300">
                {superAdmins}
              </Badge>
            </div>

            <div className="flex justify-between">
              <span>System Admin</span>
              <Badge className="border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300">
                {systemAdmins}
              </Badge>
            </div>

            <div className="flex justify-between">
              <span>Support</span>
              <Badge className="border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-300">
                {supportUsers}
              </Badge>
            </div>

            <Separator />

            <div className="flex justify-between font-medium">
              <span>Inactive Accounts</span>
              <span>{inactive}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Search and filter internal users</CardDescription>
        </CardHeader>

        <CardContent>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative w-full max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search user..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            <Select
              value={roleFilter}
              onValueChange={(value) =>
                setRoleFilter(value as "ALL" | InternalRole)
              }
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All roles" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All Roles</SelectItem>
                {roles.map((item) => (
                  <SelectItem key={item.code} value={item.code}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={statusFilter}
              onValueChange={(value) =>
                setStatusFilter(value as "ALL" | UserStatus)
              }
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All Status</SelectItem>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="INACTIVE">Inactive</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline" onClick={handleResetFilters}>
              <RefreshCcw className="h-4 w-4" />
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>System Users</CardTitle>
          <CardDescription>Total results: {filteredUsers.length}</CardDescription>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Loading system users...
            </div>
          ) : (
            <div className="w-full">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-[220px]">User</TableHead>
                    <TableHead className="min-w-[220px]">Contact</TableHead>
                    <TableHead className="min-w-[140px]">Role</TableHead>
                    <TableHead className="min-w-[110px]">Status</TableHead>
                    <TableHead className="min-w-[120px]">Created</TableHead>
                    <TableHead className="min-w-[110px]">Password</TableHead>
                    <TableHead className="min-w-[70px]"></TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {filteredUsers.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground">
                        No users found
                      </TableCell>
                    </TableRow>
                  )}

                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-10 w-10 shrink-0">
                            <AvatarImage
                              src={user.avatar || ""}
                              alt={user.full_name || user.username}
                            />
                            <AvatarFallback>{getInitials(user.full_name)}</AvatarFallback>
                          </Avatar>
                          <div className="min-w-0">
                            <div className="truncate font-medium">{user.full_name}</div>
                            <div className="truncate text-xs text-muted-foreground">
                              @{user.username}
                            </div>
                          </div>
                        </div>
                      </TableCell>

                      <TableCell>
                        <div className="space-y-1 text-sm">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Mail className="h-3.5 w-3.5 shrink-0" />
                            <span className="truncate">{user.email || "--"}</span>
                          </div>

                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Phone className="h-3.5 w-3.5 shrink-0" />
                            <span className="truncate">{user.phone || "--"}</span>
                          </div>
                        </div>
                      </TableCell>

                      <TableCell>
                        <Badge className={cn("gap-1", getRoleBadgeClass(user.role))}>
                          {getRoleIcon(user.role)}
                          {getRoleLabel(user.role)}
                        </Badge>
                      </TableCell>

                      <TableCell>{getStatusBadge(user.status)}</TableCell>

                      <TableCell>{formatDate(user.created_at)}</TableCell>

                      <TableCell>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={actionLoadingId === user.id}
                          onClick={() => {
                            setResetUserId(user.id)
                            setNewPassword("")
                            setConfirmPassword("")
                            setOpenResetDialog(true)
                          }}
                        >
                          {actionLoadingId === user.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <KeyRound className="h-4 w-4" />
                          )}
                          Reset
                        </Button>
                      </TableCell>

                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              size="icon"
                              variant="ghost"
                              disabled={actionLoadingId === user.id}
                            >
                              {actionLoadingId === user.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <MoreHorizontal className="h-4 w-4" />
                              )}
                            </Button>
                          </DropdownMenuTrigger>

                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />

                            <DropdownMenuItem
                              onClick={() => openUserProfile(user)}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Profile
                            </DropdownMenuItem>

                            <DropdownMenuItem
                              onClick={() => handleToggleStatus(user.id)}
                            >
                              {user.status === "ACTIVE" ? "Disable User" : "Enable User"}
                            </DropdownMenuItem>

                            <DropdownMenuSeparator />
                            <DropdownMenuLabel>Change Role</DropdownMenuLabel>

                            {roles.map((item) => (
                              <DropdownMenuItem
                                key={`${user.id}-${item.code}`}
                                onClick={() => handleChangeRole(user.id, item.code)}
                              >
                                {item.label}
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* USER PROFILE DIALOG */}
      <Dialog open={openProfileDialog} onOpenChange={setOpenProfileDialog}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>User Profile</DialogTitle>
            <DialogDescription>
              Internal user account details and contact information
            </DialogDescription>
          </DialogHeader>

          {selectedUser ? (
            <div className="space-y-6 py-2">
              <div className="flex items-center gap-4 rounded-2xl border p-4">
                <Avatar className="h-16 w-16 shrink-0">
                  <AvatarImage
                    src={selectedUser.avatar || ""}
                    alt={selectedUser.full_name || selectedUser.username}
                  />
                  <AvatarFallback className="text-lg">
                    {getInitials(selectedUser.full_name)}
                  </AvatarFallback>
                </Avatar>

                <div className="min-w-0 space-y-1">
                  <div className="text-lg font-semibold">
                    {selectedUser.full_name}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    @{selectedUser.username}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <Badge className={cn("gap-1", getRoleBadgeClass(selectedUser.role))}>
                      {getRoleIcon(selectedUser.role)}
                      {getRoleLabel(selectedUser.role)}
                    </Badge>
                    {getStatusBadge(selectedUser.status)}
                  </div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Contact Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div className="flex items-start gap-3">
                      <Mail className="mt-0.5 h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-muted-foreground">Email</div>
                        <div className="font-medium">{selectedUser.email || "--"}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Phone className="mt-0.5 h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-muted-foreground">Phone</div>
                        <div className="font-medium">{selectedUser.phone || "--"}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Account Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div className="flex items-start gap-3">
                      <CalendarDays className="mt-0.5 h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-muted-foreground">Created At</div>
                        <div className="font-medium">{formatDate(selectedUser.created_at)}</div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Clock3 className="mt-0.5 h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-muted-foreground">Last Login</div>
                        <div className="font-medium">{formatDateTime(selectedUser.last_login)}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          ) : null}

          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenProfileDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* RESET PASSWORD DIALOG */}
      <Dialog open={openResetDialog} onOpenChange={setOpenResetDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>
              Enter the new password for this user
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                New Password
              </label>

              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Confirm Password
              </label>

              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm password"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setOpenResetDialog(false)}
            >
              Cancel
            </Button>

            <Button
              onClick={handleResetPassword}
              disabled={actionLoadingId === resetUserId}
            >
              {actionLoadingId === resetUserId ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Update Password"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}