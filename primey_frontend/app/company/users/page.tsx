"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Search,
  Users,
  Mail,
  Phone,
  RefreshCcw,
  MoreHorizontal,
  CheckCircle2,
  XCircle,
  Shield,
  Briefcase,
  UserCheck,
  Crown,
  Loader2,
  Eye,
} from "lucide-react"

import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
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
   Helpers
====================================================== */

function getCookie(name: string): string {
  if (typeof document === "undefined") return ""

  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : ""
}

function formatDate(value: string | null | undefined) {
  if (!value) return "--"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date)
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

function normalizeRole(role?: string | null): CompanyRole | "" {
  const safe = (role || "").toUpperCase()

  if (
    safe === "OWNER" ||
    safe === "ADMIN" ||
    safe === "HR" ||
    safe === "MANAGER" ||
    safe === "EMPLOYEE"
  ) {
    return safe
  }

  return ""
}

/* ======================================================
   Types
====================================================== */

type CompanyRole = "OWNER" | "ADMIN" | "HR" | "MANAGER" | "EMPLOYEE"
type UserStatus = "ACTIVE" | "INACTIVE"

interface CompanyUserRow {
  id: number
  full_name: string
  username: string
  email: string
  phone: string
  avatar?: string | null
  role: CompanyRole | string
  status: UserStatus
  is_active: boolean
  created_at?: string | null
}

interface CompanyUsersApiResponse {
  status?: "ok" | "error" | "success"
  employees?: CompanyUserRow[]
  message?: string
  success?: boolean
  results?: CompanyUserRow[]
  count?: number
  error?: string
}

interface GenericApiResponse {
  success?: boolean
  status?: "ok" | "error" | "success"
  message?: string
  error?: string
  details?: string
  role?: string
}

interface RoleFilterOption {
  code: "ALL" | CompanyRole
  label: string
}

interface AssignableRoleOption {
  code: CompanyRole
  label: string
}

interface WhoAmIResponse {
  authenticated?: boolean
  role?: string | null
  user?: {
    id?: number
    username?: string
  } | null
}

/* ======================================================
   UI Helpers
====================================================== */

function getRoleLabel(role: string) {
  switch ((role || "").toUpperCase()) {
    case "OWNER":
      return "Owner"
    case "ADMIN":
      return "Admin"
    case "HR":
      return "HR"
    case "MANAGER":
      return "Manager"
    case "EMPLOYEE":
      return "Employee"
    default:
      return role || "Employee"
  }
}

function getRoleIcon(role: string) {
  switch ((role || "").toUpperCase()) {
    case "OWNER":
      return <Crown className="h-4 w-4" />
    case "ADMIN":
      return <Shield className="h-4 w-4" />
    case "HR":
      return <Briefcase className="h-4 w-4" />
    case "MANAGER":
      return <UserCheck className="h-4 w-4" />
    case "EMPLOYEE":
      return <Users className="h-4 w-4" />
    default:
      return <Users className="h-4 w-4" />
  }
}

function getRoleBadgeClass(role: string) {
  switch ((role || "").toUpperCase()) {
    case "OWNER":
      return "border-yellow-500/30 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300"
    case "ADMIN":
      return "border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300"
    case "HR":
      return "border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-300"
    case "MANAGER":
      return "border-cyan-500/30 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300"
    case "EMPLOYEE":
      return "border-slate-500/30 bg-slate-500/10 text-slate-700 dark:text-slate-300"
    default:
      return "border-slate-500/30 bg-slate-500/10 text-slate-700 dark:text-slate-300"
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

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  valueClassName,
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

export default function CompanyUsersPage() {
  const router = useRouter()

  const [users, setUsers] = useState<CompanyUserRow[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null)
  const [currentUserRole, setCurrentUserRole] = useState<CompanyRole | "">("")

  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState<"ALL" | CompanyRole>("ALL")
  const [statusFilter, setStatusFilter] = useState<"ALL" | UserStatus>("ALL")

  const roleOptions: RoleFilterOption[] = [
    { code: "ALL", label: "All Roles" },
    { code: "OWNER", label: "Owner" },
    { code: "ADMIN", label: "Admin" },
    { code: "HR", label: "HR" },
    { code: "MANAGER", label: "Manager" },
    { code: "EMPLOYEE", label: "Employee" },
  ]

  const assignableRoleOptions = useMemo<AssignableRoleOption[]>(() => {
    const base: AssignableRoleOption[] = [
      { code: "ADMIN", label: "Admin" },
      { code: "HR", label: "HR" },
      { code: "MANAGER", label: "Manager" },
      { code: "EMPLOYEE", label: "Employee" },
    ]

    if (currentUserRole === "OWNER") {
      return [{ code: "OWNER", label: "Owner" }, ...base]
    }

    return base
  }, [currentUserRole])

  const fetchUsers = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) setLoading(true)
      else setRefreshing(true)

      const response = await fetch(`${API_BASE}/company/employees/`, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      })

      const data: CompanyUsersApiResponse = await response.json()

      const normalizedUsers = data.employees || data.results || []

      const isSuccess =
        data.status === "ok" ||
        data.success === true ||
        response.ok

      if (!response.ok || !isSuccess) {
        throw new Error(data.message || data.error || "Failed to load company users")
      }

      setUsers(normalizedUsers)
    } catch (error) {
      console.error("Fetch company users error:", error)
      toast.error("Failed to load company users")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  const fetchCurrentUserRole = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/whoami/`, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
      })

      if (!response.ok) return

      const data: WhoAmIResponse = await response.json()
      setCurrentUserRole(normalizeRole(data.role))
    } catch (error) {
      console.error("Fetch current user role error:", error)
    }
  }, [])

  useEffect(() => {
    fetchUsers(true)
    fetchCurrentUserRole()
  }, [fetchUsers, fetchCurrentUserRole])

  const filteredUsers = useMemo(() => {
    const keyword = search.trim().toLowerCase()

    return users.filter((user) => {
      const matchesSearch =
        !keyword ||
        (user.full_name || "").toLowerCase().includes(keyword) ||
        (user.username || "").toLowerCase().includes(keyword) ||
        (user.email || "").toLowerCase().includes(keyword) ||
        (user.phone || "").toLowerCase().includes(keyword)

      const normalizedRole = (user.role || "").toUpperCase()
      const matchesRole = roleFilter === "ALL" ? true : normalizedRole === roleFilter
      const matchesStatus =
        statusFilter === "ALL" ? true : user.status === statusFilter

      return matchesSearch && matchesRole && matchesStatus
    })
  }, [users, search, roleFilter, statusFilter])

  const total = users.length
  const active = users.filter((u) => u.status === "ACTIVE").length
  const inactive = users.filter((u) => u.status === "INACTIVE").length
  const owners = users.filter((u) => (u.role || "").toUpperCase() === "OWNER").length
  const admins = users.filter((u) => (u.role || "").toUpperCase() === "ADMIN").length
  const hrUsers = users.filter((u) => (u.role || "").toUpperCase() === "HR").length
  const managers = users.filter((u) => (u.role || "").toUpperCase() === "MANAGER").length
  const employees = users.filter((u) => (u.role || "").toUpperCase() === "EMPLOYEE").length

  async function handleToggleStatus(userId: number) {
    try {
      setActionLoadingId(userId)

      const csrfToken = getCookie("csrftoken")

      const response = await fetch(
        `${API_BASE}/company/employees/${userId}/toggle-status/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({}),
        }
      )

      const data: GenericApiResponse = await response.json()

      if (!response.ok || data.status === "error" || data.success === false) {
        throw new Error(data.error || data.message || "Failed to update user status")
      }

      toast.success("User status updated successfully")
      await fetchUsers(false)
    } catch (error) {
      console.error("Toggle company user status error:", error)
      toast.error(
        error instanceof Error ? error.message : "Failed to update user status"
      )
    } finally {
      setActionLoadingId(null)
    }
  }

  async function handleChangeRole(userId: number, role: CompanyRole) {
    try {
      setActionLoadingId(userId)

      const csrfToken = getCookie("csrftoken")

      const response = await fetch(
        `${API_BASE}/company/employees/${userId}/change-role/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({ role }),
        }
      )

      const data: GenericApiResponse = await response.json()

      if (!response.ok || data.status === "error" || data.success === false) {
        throw new Error(data.error || data.message || "Failed to update user role")
      }

      toast.success(data.message || "User role updated successfully")
      await fetchUsers(false)
    } catch (error) {
      console.error("Change company user role error:", error)
      toast.error(
        error instanceof Error ? error.message : "Failed to update user role"
      )
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
          <h1 className="text-2xl font-bold tracking-tight">Company Users</h1>
          <p className="text-muted-foreground">
            Manage company access overview and review all linked users
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
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Users"
          value={total}
          description="All company linked users"
          icon={Users}
        />

        <StatCard
          title="Active"
          value={active}
          description="Currently active accounts"
          icon={UserCheck}
          valueClassName="text-green-600"
        />

        <StatCard
          title="Admins"
          value={admins}
          description="Administrative company access"
          icon={Shield}
          valueClassName="text-blue-600"
        />

        <StatCard
          title="Employees"
          value={employees}
          description="Standard employee accounts"
          icon={Briefcase}
          valueClassName="text-violet-600"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-1">
        <Card>
          <CardHeader>
            <CardTitle>Access Overview</CardTitle>
            <CardDescription>Company access distribution</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span>Owner</span>
              <Badge className="border-yellow-500/30 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300">
                {owners}
              </Badge>
            </div>

            <div className="flex justify-between">
              <span>Admin</span>
              <Badge className="border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300">
                {admins}
              </Badge>
            </div>

            <div className="flex justify-between">
              <span>HR</span>
              <Badge className="border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-300">
                {hrUsers}
              </Badge>
            </div>

            <div className="flex justify-between">
              <span>Manager</span>
              <Badge className="border-cyan-500/30 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300">
                {managers}
              </Badge>
            </div>

            <div className="flex justify-between">
              <span>Employee</span>
              <Badge className="border-slate-500/30 bg-slate-500/10 text-slate-700 dark:text-slate-300">
                {employees}
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
          <CardDescription>Search and filter company users</CardDescription>
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
              onValueChange={(value) => setRoleFilter(value as "ALL" | CompanyRole)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All roles" />
              </SelectTrigger>
              <SelectContent>
                {roleOptions.map((item) => (
                  <SelectItem key={item.code} value={item.code}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={statusFilter}
              onValueChange={(value) => setStatusFilter(value as "ALL" | UserStatus)}
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
          <CardTitle>Company Users</CardTitle>
          <CardDescription>Total results: {filteredUsers.length}</CardDescription>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Loading company users...
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
                    <TableHead className="min-w-[70px]"></TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {filteredUsers.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground">
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
                            <AvatarFallback>
                              {getInitials(user.full_name || user.username)}
                            </AvatarFallback>
                          </Avatar>

                          <div className="min-w-0">
                            <div className="truncate font-medium">
                              {user.full_name}
                            </div>
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
                              onClick={() =>
                                router.push(`/company/profile?user_id=${user.id}`)
                              }
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              Open Profile
                            </DropdownMenuItem>

                            <DropdownMenuItem
                              onClick={() => handleToggleStatus(user.id)}
                            >
                              {user.status === "ACTIVE" ? "Disable User" : "Enable User"}
                            </DropdownMenuItem>

                            <DropdownMenuSeparator />
                            <DropdownMenuLabel>Change Role</DropdownMenuLabel>

                            <DropdownMenuSub>
                              <DropdownMenuSubTrigger>
                                Select Role
                              </DropdownMenuSubTrigger>

                              <DropdownMenuSubContent>
                                {assignableRoleOptions.map((item) => (
                                  <DropdownMenuItem
                                    key={`${user.id}-${item.code}`}
                                    onClick={() => handleChangeRole(user.id, item.code)}
                                  >
                                    {item.label}
                                  </DropdownMenuItem>
                                ))}
                              </DropdownMenuSubContent>
                            </DropdownMenuSub>
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
    </div>
  )
}