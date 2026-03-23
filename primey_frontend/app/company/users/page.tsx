"use client"

import type { ReactNode } from "react"
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
  Filter,
  UserRound,
  CalendarDays,
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

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
    maximumFractionDigits: 0,
  }).format(value || 0)
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
type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"

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

interface Dictionary {
  pageTitle: string
  pageDescription: string
  refresh: string
  totalUsers: string
  totalUsersDesc: string
  activeUsers: string
  activeUsersDesc: string
  adminUsers: string
  adminUsersDesc: string
  employeeUsers: string
  employeeUsersDesc: string
  accessOverview: string
  accessOverviewDesc: string
  owner: string
  admin: string
  hr: string
  manager: string
  employee: string
  inactiveAccounts: string
  filtersTitle: string
  filtersDesc: string
  searchPlaceholder: string
  allRoles: string
  allStatus: string
  active: string
  inactive: string
  reset: string
  usersTitle: string
  totalResults: string
  loadingUsers: string
  noUsersFound: string
  user: string
  contact: string
  role: string
  status: string
  created: string
  actions: string
  openProfile: string
  disableUser: string
  enableUser: string
  changeRole: string
  selectRole: string
  failedLoadUsers: string
  failedUpdateStatus: string
  failedUpdateRole: string
  statusUpdated: string
  roleUpdated: string
  filtersReset: string
  emailUnavailable: string
  phoneUnavailable: string
  profileUsernamePrefix: string
}

const dictionaryMap: Record<Locale, Dictionary> = {
  ar: {
    pageTitle: "مستخدمو الشركة",
    pageDescription: "إدارة مستخدمي الشركة ومراجعة جميع الحسابات المرتبطة",
    refresh: "تحديث",
    totalUsers: "إجمالي المستخدمين",
    totalUsersDesc: "جميع المستخدمين المرتبطين بالشركة",
    activeUsers: "النشطون",
    activeUsersDesc: "الحسابات النشطة حاليًا",
    adminUsers: "المديرون",
    adminUsersDesc: "الحسابات الإدارية داخل الشركة",
    employeeUsers: "الموظفون",
    employeeUsersDesc: "حسابات الموظفين القياسية",
    accessOverview: "نظرة عامة على الصلاحيات",
    accessOverviewDesc: "توزيع صلاحيات الوصول داخل الشركة",
    owner: "المالك",
    admin: "مدير",
    hr: "الموارد البشرية",
    manager: "مدير قسم",
    employee: "موظف",
    inactiveAccounts: "الحسابات غير النشطة",
    filtersTitle: "البحث والفلاتر",
    filtersDesc: "ابحث وصفِّ المستخدمين حسب الدور والحالة",
    searchPlaceholder: "ابحث باسم المستخدم أو البريد أو الجوال...",
    allRoles: "كل الأدوار",
    allStatus: "كل الحالات",
    active: "نشط",
    inactive: "غير نشط",
    reset: "إعادة تعيين",
    usersTitle: "قائمة المستخدمين",
    totalResults: "إجمالي النتائج",
    loadingUsers: "جاري تحميل مستخدمي الشركة...",
    noUsersFound: "لا يوجد مستخدمون مطابقون",
    user: "المستخدم",
    contact: "التواصل",
    role: "الدور",
    status: "الحالة",
    created: "تاريخ الإنشاء",
    actions: "الإجراءات",
    openProfile: "فتح الملف الشخصي",
    disableUser: "تعطيل المستخدم",
    enableUser: "تفعيل المستخدم",
    changeRole: "تغيير الدور",
    selectRole: "اختيار الدور",
    failedLoadUsers: "فشل في تحميل مستخدمي الشركة",
    failedUpdateStatus: "فشل في تحديث حالة المستخدم",
    failedUpdateRole: "فشل في تحديث دور المستخدم",
    statusUpdated: "تم تحديث حالة المستخدم بنجاح",
    roleUpdated: "تم تحديث دور المستخدم بنجاح",
    filtersReset: "تمت إعادة تعيين الفلاتر بنجاح",
    emailUnavailable: "--",
    phoneUnavailable: "--",
    profileUsernamePrefix: "@",
  },
  en: {
    pageTitle: "Company Users",
    pageDescription: "Manage company users and review all linked accounts",
    refresh: "Refresh",
    totalUsers: "Total Users",
    totalUsersDesc: "All company linked users",
    activeUsers: "Active Users",
    activeUsersDesc: "Currently active accounts",
    adminUsers: "Admins",
    adminUsersDesc: "Administrative company access",
    employeeUsers: "Employees",
    employeeUsersDesc: "Standard employee accounts",
    accessOverview: "Access Overview",
    accessOverviewDesc: "Company access distribution",
    owner: "Owner",
    admin: "Admin",
    hr: "HR",
    manager: "Manager",
    employee: "Employee",
    inactiveAccounts: "Inactive Accounts",
    filtersTitle: "Search & Filters",
    filtersDesc: "Search and filter company users",
    searchPlaceholder: "Search by name, username, email, or phone...",
    allRoles: "All Roles",
    allStatus: "All Status",
    active: "Active",
    inactive: "Inactive",
    reset: "Reset",
    usersTitle: "Company Users",
    totalResults: "Total Results",
    loadingUsers: "Loading company users...",
    noUsersFound: "No users found",
    user: "User",
    contact: "Contact",
    role: "Role",
    status: "Status",
    created: "Created",
    actions: "Actions",
    openProfile: "Open Profile",
    disableUser: "Disable User",
    enableUser: "Enable User",
    changeRole: "Change Role",
    selectRole: "Select Role",
    failedLoadUsers: "Failed to load company users",
    failedUpdateStatus: "Failed to update user status",
    failedUpdateRole: "Failed to update user role",
    statusUpdated: "User status updated successfully",
    roleUpdated: "User role updated successfully",
    filtersReset: "Filters reset successfully",
    emailUnavailable: "--",
    phoneUnavailable: "--",
    profileUsernamePrefix: "@",
  },
}

/* ======================================================
   Language / Direction Helpers
====================================================== */

function detectLocaleFromDocument(): Locale {
  if (typeof document === "undefined") return "en"
  const lang = (document.documentElement.lang || "en").toLowerCase()
  return lang.startsWith("ar") ? "ar" : "en"
}

function detectDirectionFromDocument(): Direction {
  if (typeof document === "undefined") return "ltr"
  const dir = (document.documentElement.dir || "ltr").toLowerCase()
  return dir === "rtl" ? "rtl" : "ltr"
}

/* ======================================================
   UI Helpers
====================================================== */

function getRoleLabel(role: string, t: Dictionary) {
  switch ((role || "").toUpperCase()) {
    case "OWNER":
      return t.owner
    case "ADMIN":
      return t.admin
    case "HR":
      return t.hr
    case "MANAGER":
      return t.manager
    case "EMPLOYEE":
      return t.employee
    default:
      return t.employee
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

function getStatusBadge(status: UserStatus, t: Dictionary) {
  if (status === "ACTIVE") {
    return (
      <Badge className="gap-1 border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
        <CheckCircle2 className="h-3.5 w-3.5" />
        {t.active}
      </Badge>
    )
  }

  return (
    <Badge className="gap-1 border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300">
      <XCircle className="h-3.5 w-3.5" />
      {t.inactive}
    </Badge>
  )
}

function StatCard({
  title,
  value,
  description,
  icon,
  valueClassName,
}: {
  title: string
  value: number
  description: string
  icon: ReactNode
  valueClassName?: string
}) {
  return (
    <Card className="h-full rounded-2xl border-border/60">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="text-sm font-semibold">{title}</CardTitle>
            <CardDescription className="text-xs">{description}</CardDescription>
          </div>

          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-border/60 bg-muted/40 text-muted-foreground">
            {icon}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className={cn("text-2xl font-bold tracking-tight", valueClassName)}>
          {formatNumber(value)}
        </div>
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

  const [locale, setLocale] = useState<Locale>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  useEffect(() => {
    const updateLangState = () => {
      setLocale(detectLocaleFromDocument())
      setDirection(detectDirectionFromDocument())
    }

    updateLangState()

    if (typeof document === "undefined") return

    const observer = new MutationObserver(() => {
      updateLangState()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    return () => observer.disconnect()
  }, [])

  const t = dictionaryMap[locale]

  const roleOptions: RoleFilterOption[] = useMemo(
    () => [
      { code: "ALL", label: t.allRoles },
      { code: "OWNER", label: t.owner },
      { code: "ADMIN", label: t.admin },
      { code: "HR", label: t.hr },
      { code: "MANAGER", label: t.manager },
      { code: "EMPLOYEE", label: t.employee },
    ],
    [t]
  )

  const assignableRoleOptions = useMemo<AssignableRoleOption[]>(() => {
    const base: AssignableRoleOption[] = [
      { code: "ADMIN", label: t.admin },
      { code: "HR", label: t.hr },
      { code: "MANAGER", label: t.manager },
      { code: "EMPLOYEE", label: t.employee },
    ]

    if (currentUserRole === "OWNER") {
      return [{ code: "OWNER", label: t.owner }, ...base]
    }

    return base
  }, [currentUserRole, t])

  const fetchUsers = useCallback(
    async (showLoader = true) => {
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
          data.status === "ok" || data.success === true || response.ok

        if (!response.ok || !isSuccess) {
          throw new Error(data.message || data.error || t.failedLoadUsers)
        }

        setUsers(normalizedUsers)
      } catch (error) {
        console.error("Fetch company users error:", error)
        toast.error(
          error instanceof Error ? error.message : t.failedLoadUsers
        )
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [t.failedLoadUsers]
  )

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

      const normalizedUserRole = (user.role || "").toUpperCase()
      const matchesRole =
        roleFilter === "ALL" ? true : normalizedUserRole === roleFilter
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
        throw new Error(data.error || data.message || t.failedUpdateStatus)
      }

      toast.success(data.message || t.statusUpdated)
      await fetchUsers(false)
    } catch (error) {
      console.error("Toggle company user status error:", error)
      toast.error(
        error instanceof Error ? error.message : t.failedUpdateStatus
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
        throw new Error(data.error || data.message || t.failedUpdateRole)
      }

      toast.success(data.message || t.roleUpdated)
      await fetchUsers(false)
    } catch (error) {
      console.error("Change company user role error:", error)
      toast.error(error instanceof Error ? error.message : t.failedUpdateRole)
    } finally {
      setActionLoadingId(null)
    }
  }

  function handleResetFilters() {
    setSearch("")
    setRoleFilter("ALL")
    setStatusFilter("ALL")
    toast.success(t.filtersReset)
  }

  return (
    <div
      dir={direction}
      className="space-y-6 p-4 md:p-6"
    >
      {/* =========================================
          Header
      ========================================= */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">{t.pageTitle}</h1>
          <p className="text-sm text-muted-foreground">{t.pageDescription}</p>
        </div>

        <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
          <Button
            variant="outline"
            onClick={() => fetchUsers(false)}
            disabled={refreshing}
            className="h-11 rounded-xl"
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCcw className="h-4 w-4" />
            )}
            <span>{t.refresh}</span>
          </Button>
        </div>
      </div>

      {/* =========================================
          Statistics
      ========================================= */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title={t.totalUsers}
          value={total}
          description={t.totalUsersDesc}
          icon={<Users className="h-5 w-5" />}
        />

        <StatCard
          title={t.activeUsers}
          value={active}
          description={t.activeUsersDesc}
          icon={<UserCheck className="h-5 w-5" />}
          valueClassName="text-emerald-600"
        />

        <StatCard
          title={t.adminUsers}
          value={admins}
          description={t.adminUsersDesc}
          icon={<Shield className="h-5 w-5" />}
          valueClassName="text-blue-600"
        />

        <StatCard
          title={t.employeeUsers}
          value={employees}
          description={t.employeeUsersDesc}
          icon={<Briefcase className="h-5 w-5" />}
          valueClassName="text-violet-600"
        />
      </div>

      {/* =========================================
          Overview + Filters
      ========================================= */}
      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Card className="rounded-2xl border-border/60">
          <CardHeader className="pb-4">
            <CardTitle className="text-base">{t.accessOverview}</CardTitle>
            <CardDescription>{t.accessOverviewDesc}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between gap-3 rounded-xl border border-border/50 bg-muted/20 px-3 py-2">
                <span>{t.owner}</span>
                <Badge className="border-yellow-500/30 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300">
                  {formatNumber(owners)}
                </Badge>
              </div>

              <div className="flex items-center justify-between gap-3 rounded-xl border border-border/50 bg-muted/20 px-3 py-2">
                <span>{t.admin}</span>
                <Badge className="border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300">
                  {formatNumber(admins)}
                </Badge>
              </div>

              <div className="flex items-center justify-between gap-3 rounded-xl border border-border/50 bg-muted/20 px-3 py-2">
                <span>{t.hr}</span>
                <Badge className="border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-300">
                  {formatNumber(hrUsers)}
                </Badge>
              </div>

              <div className="flex items-center justify-between gap-3 rounded-xl border border-border/50 bg-muted/20 px-3 py-2">
                <span>{t.manager}</span>
                <Badge className="border-cyan-500/30 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300">
                  {formatNumber(managers)}
                </Badge>
              </div>

              <div className="flex items-center justify-between gap-3 rounded-xl border border-border/50 bg-muted/20 px-3 py-2">
                <span>{t.employee}</span>
                <Badge className="border-slate-500/30 bg-slate-500/10 text-slate-700 dark:text-slate-300">
                  {formatNumber(employees)}
                </Badge>
              </div>
            </div>

            <Separator />

            <div className="flex items-center justify-between gap-3 text-sm font-medium">
              <span>{t.inactiveAccounts}</span>
              <span className="text-muted-foreground">{formatNumber(inactive)}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/60">
          <CardHeader className="pb-4">
            <CardTitle className="text-base">{t.filtersTitle}</CardTitle>
            <CardDescription>{t.filtersDesc}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(0,1.5fr)_200px_200px_auto]">
              <div className="relative">
                <Search
                  className={cn(
                    "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                    direction === "rtl" ? "right-3" : "left-3"
                  )}
                />
                <Input
                  placeholder={t.searchPlaceholder}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className={cn(
                    "h-11 rounded-xl",
                    direction === "rtl" ? "pr-9" : "pl-9"
                  )}
                />
              </div>

              <Select
                value={roleFilter}
                onValueChange={(value) => setRoleFilter(value as "ALL" | CompanyRole)}
              >
                <SelectTrigger className="h-11 rounded-xl">
                  <SelectValue placeholder={t.allRoles} />
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
                <SelectTrigger className="h-11 rounded-xl">
                  <SelectValue placeholder={t.allStatus} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">{t.allStatus}</SelectItem>
                  <SelectItem value="ACTIVE">{t.active}</SelectItem>
                  <SelectItem value="INACTIVE">{t.inactive}</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                onClick={handleResetFilters}
                className="h-11 rounded-xl"
              >
                <RefreshCcw className="h-4 w-4" />
                <span>{t.reset}</span>
              </Button>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <div className="inline-flex items-center gap-2 rounded-full border border-border/60 px-3 py-1.5">
                <Filter className="h-3.5 w-3.5" />
                <span>
                  {t.totalResults}: {formatNumber(filteredUsers.length)}
                </span>
              </div>

              <div className="inline-flex items-center gap-2 rounded-full border border-border/60 px-3 py-1.5">
                <Users className="h-3.5 w-3.5" />
                <span>
                  {t.totalUsers}: {formatNumber(total)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* =========================================
          Users Table / Mobile Cards
      ========================================= */}
      <Card className="rounded-2xl border-border/60">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle className="text-base">{t.usersTitle}</CardTitle>
              <CardDescription>
                {t.totalResults}: {formatNumber(filteredUsers.length)}
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          {loading ? (
            <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className={cn(direction === "rtl" ? "mr-2" : "ml-2")}>
                {t.loadingUsers}
              </span>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border/70 py-16 text-center text-sm text-muted-foreground">
              {t.noUsersFound}
            </div>
          ) : (
            <>
              {/* Desktop / Tablet Table */}
              <div className="hidden overflow-x-auto lg:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="min-w-[240px]">{t.user}</TableHead>
                      <TableHead className="min-w-[250px]">{t.contact}</TableHead>
                      <TableHead className="min-w-[140px]">{t.role}</TableHead>
                      <TableHead className="min-w-[120px]">{t.status}</TableHead>
                      <TableHead className="min-w-[130px]">{t.created}</TableHead>
                      <TableHead className="w-[70px] text-center"></TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {filteredUsers.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Avatar className="h-11 w-11 shrink-0 rounded-xl">
                              <AvatarImage
                                src={user.avatar || ""}
                                alt={user.full_name || user.username}
                              />
                              <AvatarFallback className="rounded-xl">
                                {getInitials(user.full_name || user.username)}
                              </AvatarFallback>
                            </Avatar>

                            <div className="min-w-0">
                              <div className="truncate font-medium">
                                {user.full_name || "--"}
                              </div>
                              <div className="truncate text-xs text-muted-foreground">
                                {t.profileUsernamePrefix}
                                {user.username || "--"}
                              </div>
                            </div>
                          </div>
                        </TableCell>

                        <TableCell>
                          <div className="space-y-1.5 text-sm">
                            <div className="flex items-center gap-2 text-muted-foreground">
                              <Mail className="h-3.5 w-3.5 shrink-0" />
                              <span className="truncate" dir="ltr">
                                {user.email || t.emailUnavailable}
                              </span>
                            </div>

                            <div className="flex items-center gap-2 text-muted-foreground">
                              <Phone className="h-3.5 w-3.5 shrink-0" />
                              <span className="truncate" dir="ltr">
                                {user.phone || t.phoneUnavailable}
                              </span>
                            </div>
                          </div>
                        </TableCell>

                        <TableCell>
                          <Badge className={cn("gap-1", getRoleBadgeClass(user.role))}>
                            {getRoleIcon(user.role)}
                            {getRoleLabel(user.role, t)}
                          </Badge>
                        </TableCell>

                        <TableCell>{getStatusBadge(user.status, t)}</TableCell>

                        <TableCell dir="ltr">{formatDate(user.created_at)}</TableCell>

                        <TableCell className="text-center">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                size="icon"
                                variant="ghost"
                                disabled={actionLoadingId === user.id}
                                className="rounded-xl"
                              >
                                {actionLoadingId === user.id ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <MoreHorizontal className="h-4 w-4" />
                                )}
                              </Button>
                            </DropdownMenuTrigger>

                            <DropdownMenuContent align={direction === "rtl" ? "start" : "end"}>
                              <DropdownMenuLabel>{t.actions}</DropdownMenuLabel>
                              <DropdownMenuSeparator />

                              <DropdownMenuItem
                                onClick={() =>
                                  router.push(`/company/profile?user_id=${user.id}`)
                                }
                              >
                                <Eye className="h-4 w-4" />
                                <span>{t.openProfile}</span>
                              </DropdownMenuItem>

                              <DropdownMenuItem
                                onClick={() => handleToggleStatus(user.id)}
                              >
                                {user.status === "ACTIVE"
                                  ? t.disableUser
                                  : t.enableUser}
                              </DropdownMenuItem>

                              <DropdownMenuSeparator />
                              <DropdownMenuLabel>{t.changeRole}</DropdownMenuLabel>

                              <DropdownMenuSub>
                                <DropdownMenuSubTrigger>
                                  {t.selectRole}
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

              {/* Mobile / Small Tablet Cards */}
              <div className="grid gap-4 lg:hidden">
                {filteredUsers.map((user) => (
                  <Card
                    key={user.id}
                    className="rounded-2xl border border-border/60 shadow-none"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex min-w-0 items-center gap-3">
                          <Avatar className="h-12 w-12 shrink-0 rounded-xl">
                            <AvatarImage
                              src={user.avatar || ""}
                              alt={user.full_name || user.username}
                            />
                            <AvatarFallback className="rounded-xl">
                              {getInitials(user.full_name || user.username)}
                            </AvatarFallback>
                          </Avatar>

                          <div className="min-w-0 space-y-1">
                            <div className="truncate font-semibold">
                              {user.full_name || "--"}
                            </div>
                            <div className="truncate text-xs text-muted-foreground">
                              {t.profileUsernamePrefix}
                              {user.username || "--"}
                            </div>
                          </div>
                        </div>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              size="icon"
                              variant="ghost"
                              disabled={actionLoadingId === user.id}
                              className="h-9 w-9 rounded-xl"
                            >
                              {actionLoadingId === user.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <MoreHorizontal className="h-4 w-4" />
                              )}
                            </Button>
                          </DropdownMenuTrigger>

                          <DropdownMenuContent align={direction === "rtl" ? "start" : "end"}>
                            <DropdownMenuLabel>{t.actions}</DropdownMenuLabel>
                            <DropdownMenuSeparator />

                            <DropdownMenuItem
                              onClick={() =>
                                router.push(`/company/profile?user_id=${user.id}`)
                              }
                            >
                              <Eye className="h-4 w-4" />
                              <span>{t.openProfile}</span>
                            </DropdownMenuItem>

                            <DropdownMenuItem
                              onClick={() => handleToggleStatus(user.id)}
                            >
                              {user.status === "ACTIVE"
                                ? t.disableUser
                                : t.enableUser}
                            </DropdownMenuItem>

                            <DropdownMenuSeparator />
                            <DropdownMenuLabel>{t.changeRole}</DropdownMenuLabel>

                            <DropdownMenuSub>
                              <DropdownMenuSubTrigger>
                                {t.selectRole}
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
                      </div>

                      <div className="mt-4 grid gap-3">
                        <div className="flex flex-wrap gap-2">
                          <Badge className={cn("gap-1", getRoleBadgeClass(user.role))}>
                            {getRoleIcon(user.role)}
                            {getRoleLabel(user.role, t)}
                          </Badge>

                          {getStatusBadge(user.status, t)}
                        </div>

                        <div className="grid gap-3 rounded-2xl border border-border/50 bg-muted/20 p-3">
                          <div className="flex items-start gap-2 text-sm">
                            <Mail className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                            <div className="min-w-0">
                              <div className="text-xs text-muted-foreground">
                                {t.contact}
                              </div>
                              <div className="truncate" dir="ltr">
                                {user.email || t.emailUnavailable}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-start gap-2 text-sm">
                            <Phone className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                            <div className="min-w-0">
                              <div className="text-xs text-muted-foreground">
                                {t.contact}
                              </div>
                              <div className="truncate" dir="ltr">
                                {user.phone || t.phoneUnavailable}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-start gap-2 text-sm">
                            <CalendarDays className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                            <div className="min-w-0">
                              <div className="text-xs text-muted-foreground">
                                {t.created}
                              </div>
                              <div dir="ltr">{formatDate(user.created_at)}</div>
                            </div>
                          </div>

                          <div className="flex items-start gap-2 text-sm">
                            <UserRound className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                            <div className="min-w-0">
                              <div className="text-xs text-muted-foreground">
                                {t.role}
                              </div>
                              <div>{getRoleLabel(user.role, t)}</div>
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-col gap-2 sm:flex-row">
                          <Button
                            variant="outline"
                            className="h-10 flex-1 rounded-xl"
                            onClick={() =>
                              router.push(`/company/profile?user_id=${user.id}`)
                            }
                          >
                            <Eye className="h-4 w-4" />
                            <span>{t.openProfile}</span>
                          </Button>

                          <Button
                            variant="outline"
                            className="h-10 flex-1 rounded-xl"
                            onClick={() => handleToggleStatus(user.id)}
                            disabled={actionLoadingId === user.id}
                          >
                            {actionLoadingId === user.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : user.status === "ACTIVE" ? (
                              <XCircle className="h-4 w-4" />
                            ) : (
                              <CheckCircle2 className="h-4 w-4" />
                            )}
                            <span>
                              {user.status === "ACTIVE"
                                ? t.disableUser
                                : t.enableUser}
                            </span>
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}