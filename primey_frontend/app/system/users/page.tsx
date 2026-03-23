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
  Clock3,
} from "lucide-react"

import { toast } from "sonner"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

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
   Types
====================================================== */

type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"
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
   Locale
====================================================== */

const translations = {
  ar: {
    pageTitle: "مستخدمي النظام",
    pageSubtitle:
      "إدارة مستخدمي المنصة الداخليين مثل السوبر أدمن ومدير النظام والدعم",
    refresh: "تحديث",
    addUser: "إضافة مستخدم",
    addUserTitle: "إضافة مستخدم داخلي",
    addUserDesc: "سيتم إنشاء مستخدم داخلي حقيقي وإسناد الدور المحدد له.",
    fullName: "الاسم الكامل",
    username: "اسم المستخدم",
    email: "البريد الإلكتروني",
    phone: "الهاتف",
    role: "الدور",
    status: "الحالة",
    roleSummary: "ملخص الدور",
    quickPreview: "معاينة سريعة",
    binding: "الربط",
    live: "نشط",
    cancel: "إلغاء",
    saveUser: "حفظ المستخدم",
    creating: "جارٍ الإنشاء...",
    totalUsers: "إجمالي المستخدمين",
    active: "النشطون",
    systemAdmin: "مدير النظام",
    support: "الدعم",
    allInternalUsers: "جميع مستخدمي المنصة الداخليين",
    activeAccounts: "الحسابات النشطة حالياً",
    operationalAccess: "صلاحيات الإدارة التشغيلية",
    supportTeam: "فريق الدعم والمتابعة",
    accessOverview: "نظرة على الصلاحيات",
    internalAccessDistribution: "توزيع صلاحيات الوصول الداخلي",
    superAdmin: "سوبر أدمن",
    inactiveAccounts: "الحسابات غير النشطة",
    filters: "الفلاتر",
    filtersDesc: "ابحث وصفِّ مستخدمي النظام الداخليين",
    searchPlaceholder: "ابحث عن مستخدم...",
    allRoles: "كل الأدوار",
    allStatus: "كل الحالات",
    reset: "إعادة تعيين",
    usersTableTitle: "مستخدمي النظام",
    totalResults: "إجمالي النتائج",
    user: "المستخدم",
    contact: "التواصل",
    created: "تاريخ الإنشاء",
    password: "كلمة المرور",
    actions: "الإجراءات",
    noUsersFound: "لا يوجد مستخدمون",
    loadingUsers: "جارٍ تحميل مستخدمي النظام...",
    resetPassword: "إعادة تعيين",
    actionsLabel: "الإجراءات",
    viewProfile: "عرض الملف الشخصي",
    disableUser: "تعطيل المستخدم",
    enableUser: "تفعيل المستخدم",
    changeRole: "تغيير الدور",
    userProfile: "الملف الشخصي للمستخدم",
    userProfileDesc: "تفاصيل حساب المستخدم الداخلي وبيانات التواصل",
    contactDetails: "بيانات التواصل",
    accountDetails: "تفاصيل الحساب",
    createdAt: "تاريخ الإنشاء",
    lastLogin: "آخر تسجيل دخول",
    neverLoggedIn: "لم يسجل الدخول مطلقًا",
    close: "إغلاق",
    changePassword: "تغيير كلمة المرور",
    changePasswordDesc: "أدخل كلمة المرور الجديدة لهذا المستخدم",
    newPassword: "كلمة المرور الجديدة",
    confirmPassword: "تأكيد كلمة المرور",
    updatePassword: "تحديث كلمة المرور",
    fullNameRequired: "الاسم الكامل مطلوب",
    usernameRequired: "اسم المستخدم مطلوب",
    usernameMin: "اسم المستخدم يجب أن يكون 3 أحرف على الأقل",
    emailInvalid: "يرجى إدخال بريد إلكتروني صحيح",
    createSuccess: "تم إنشاء المستخدم بنجاح",
    createSuccessDesc: "تم حفظ المستخدم بنجاح.",
    createError: "تعذر إنشاء المستخدم",
    usersLoadError: "تعذر تحميل مستخدمي النظام",
    statusUpdateSuccess: "تم تحديث حالة المستخدم بنجاح",
    statusUpdateError: "تعذر تحديث حالة المستخدم",
    roleUpdateSuccess: "تم تحديث دور المستخدم بنجاح",
    roleUpdateError: "تعذر تحديث دور المستخدم",
    passwordMin: "كلمة المرور يجب أن تكون 6 أحرف على الأقل",
    passwordMismatch: "كلمتا المرور غير متطابقتين",
    passwordUpdateSuccess: "تم تحديث كلمة المرور بنجاح",
    passwordUpdateError: "تعذر تحديث كلمة المرور",
    filtersReset: "تمت إعادة تعيين الفلاتر بنجاح",
    selectRole: "اختر الدور",
    selectStatus: "اختر الحالة",
    exampleName: "مثال: أحمد الحربي",
    exampleUsername: "مثال: ahmed.admin",
    exampleEmail: "example@primeyhrm.com",
    examplePhone: "+9665xxxxxxxx",
    activeStatus: "نشط",
    inactiveStatus: "غير نشط",
    superAdminRole: "Super Admin",
    systemAdminRole: "System Admin",
    supportRole: "Support",
  },
  en: {
    pageTitle: "System Users",
    pageSubtitle:
      "Manage internal platform users such as Super Admin, System Admin, and Support",
    refresh: "Refresh",
    addUser: "Add User",
    addUserTitle: "Add Internal User",
    addUserDesc:
      "This will create a real internal platform user and assign the selected role.",
    fullName: "Full Name",
    username: "Username",
    email: "Email",
    phone: "Phone",
    role: "Role",
    status: "Status",
    roleSummary: "Role Summary",
    quickPreview: "Quick preview",
    binding: "Binding",
    live: "Live",
    cancel: "Cancel",
    saveUser: "Save User",
    creating: "Creating...",
    totalUsers: "Total Users",
    active: "Active",
    systemAdmin: "System Admin",
    support: "Support",
    allInternalUsers: "All internal platform users",
    activeAccounts: "Currently active accounts",
    operationalAccess: "Operational management access",
    supportTeam: "Support and follow-up team",
    accessOverview: "Access Overview",
    internalAccessDistribution: "Internal access distribution",
    superAdmin: "Super Admin",
    inactiveAccounts: "Inactive Accounts",
    filters: "Filters",
    filtersDesc: "Search and filter internal users",
    searchPlaceholder: "Search user...",
    allRoles: "All Roles",
    allStatus: "All Status",
    reset: "Reset",
    usersTableTitle: "System Users",
    totalResults: "Total results",
    user: "User",
    contact: "Contact",
    created: "Created",
    password: "Password",
    actions: "Actions",
    noUsersFound: "No users found",
    loadingUsers: "Loading system users...",
    resetPassword: "Reset",
    actionsLabel: "Actions",
    viewProfile: "View Profile",
    disableUser: "Disable User",
    enableUser: "Enable User",
    changeRole: "Change Role",
    userProfile: "User Profile",
    userProfileDesc: "Internal user account details and contact information",
    contactDetails: "Contact Details",
    accountDetails: "Account Details",
    createdAt: "Created At",
    lastLogin: "Last Login",
    neverLoggedIn: "Never logged in",
    close: "Close",
    changePassword: "Change Password",
    changePasswordDesc: "Enter the new password for this user",
    newPassword: "New Password",
    confirmPassword: "Confirm Password",
    updatePassword: "Update Password",
    fullNameRequired: "Full name is required",
    usernameRequired: "Username is required",
    usernameMin: "Username must be at least 3 characters",
    emailInvalid: "Please enter a valid email address",
    createSuccess: "User created successfully",
    createSuccessDesc: "The user was saved successfully.",
    createError: "Failed to create user",
    usersLoadError: "Failed to load system users",
    statusUpdateSuccess: "User status updated successfully",
    statusUpdateError: "Failed to update user status",
    roleUpdateSuccess: "User role updated successfully",
    roleUpdateError: "Failed to update user role",
    passwordMin: "Password must be at least 6 characters",
    passwordMismatch: "Passwords do not match",
    passwordUpdateSuccess: "Password updated successfully",
    passwordUpdateError: "Failed to update password",
    filtersReset: "Filters reset successfully",
    selectRole: "Select role",
    selectStatus: "Select status",
    exampleName: "Example: Ahmed Alharbi",
    exampleUsername: "Example: ahmed.admin",
    exampleEmail: "example@primeyhrm.com",
    examplePhone: "+9665xxxxxxxx",
    activeStatus: "Active",
    inactiveStatus: "Inactive",
    superAdminRole: "Super Admin",
    systemAdminRole: "System Admin",
    supportRole: "Support",
  },
} as const

/* ======================================================
   Helpers
====================================================== */

function getDocumentLocale(): Locale {
  if (typeof document === "undefined") return "en"

  const htmlLang = (document.documentElement.lang || "").toLowerCase().trim()
  if (htmlLang.startsWith("ar")) return "ar"
  if (htmlLang.startsWith("en")) return "en"

  const bodyLang = (document.body?.getAttribute("lang") || "").toLowerCase().trim()
  if (bodyLang.startsWith("ar")) return "ar"
  if (bodyLang.startsWith("en")) return "en"

  const dir = (document.documentElement.dir || "").toLowerCase().trim()
  if (dir === "rtl") return "ar"
  if (dir === "ltr") return "en"

  return "en"
}

function getDocumentDirection(locale: Locale): Direction {
  if (typeof document === "undefined") {
    return locale === "ar" ? "rtl" : "ltr"
  }

  const dir = (document.documentElement.dir || "").toLowerCase().trim()
  if (dir === "rtl" || dir === "ltr") return dir as Direction

  return locale === "ar" ? "rtl" : "ltr"
}

function getCookie(name: string): string {
  if (typeof document === "undefined") return ""

  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : ""
}

function formatNumberEn(value: number) {
  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

function formatDate(value: string | null) {
  if (!value) return "--"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "--"

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")

  return `${year}/${month}/${day}`
}

function formatDateTime(value: string | null, locale: Locale) {
  const t = translations[locale]

  if (!value) return t.neverLoggedIn

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return t.neverLoggedIn

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  const hour = String(date.getHours()).padStart(2, "0")
  const minute = String(date.getMinutes()).padStart(2, "0")

  return `${year}/${month}/${day} ${hour}:${minute}`
}

function getRoleLabel(role: InternalRole, locale: Locale) {
  const t = translations[locale]

  switch (role) {
    case "SUPER_ADMIN":
      return t.superAdminRole
    case "SYSTEM_ADMIN":
      return t.systemAdminRole
    case "SUPPORT":
      return t.supportRole
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
      return "border-yellow-200 bg-yellow-50 text-yellow-700"
    case "SYSTEM_ADMIN":
      return "border-blue-200 bg-blue-50 text-blue-700"
    case "SUPPORT":
      return "border-violet-200 bg-violet-50 text-violet-700"
    default:
      return "border-zinc-200 bg-zinc-50 text-zinc-700"
  }
}

function UserStatusPill({
  status,
  locale,
}: {
  status: UserStatus
  locale: Locale
}) {
  const t = translations[locale]
  const isActive = status === "ACTIVE"

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        isActive
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-red-200 bg-red-50 text-red-700",
      ].join(" ")}
    >
      {isActive ? (
        <CheckCircle2 className="me-1 h-3.5 w-3.5" />
      ) : (
        <XCircle className="me-1 h-3.5 w-3.5" />
      )}
      {isActive ? t.activeStatus : t.inactiveStatus}
    </span>
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
  valueClassName,
}: {
  title: string
  value: number
  description: string
  icon: React.ComponentType<{ className?: string }>
  valueClassName?: string
}) {
  return (
    <Card className="border-border/60">
      <CardContent className="flex items-center justify-between p-5">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className={cn("text-3xl font-semibold tabular-nums", valueClassName)}>
            {formatNumberEn(value)}
          </p>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>

        <div className="rounded-2xl border bg-muted/40 p-3">
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  )
}

/* ======================================================
   Page
====================================================== */

export default function SystemUsersPage() {
  const [locale, setLocale] = useState<Locale>("en")
  const [direction, setDirection] = useState<Direction>("ltr")

  const [users, setUsers] = useState<SystemUser[]>([])
  const [roles, setRoles] = useState<RoleOption[]>([
    { code: "SUPER_ADMIN", label: "Super Admin" },
    { code: "SYSTEM_ADMIN", label: "System Admin" },
    { code: "SUPPORT", label: "Support" },
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

  const t = translations[locale]
  const isArabic = locale === "ar"

  useEffect(() => {
    const syncLocale = () => {
      const nextLocale = getDocumentLocale()
      const nextDirection = getDocumentDirection(nextLocale)
      setLocale(nextLocale)
      setDirection(nextDirection)
    }

    syncLocale()

    if (typeof document === "undefined") return

    const observer = new MutationObserver(() => {
      syncLocale()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    window.addEventListener("languagechange", syncLocale)
    window.addEventListener("focus", syncLocale)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", syncLocale)
      window.removeEventListener("focus", syncLocale)
    }
  }, [])

  const fetchUsers = useCallback(
    async (showLoader = true) => {
      try {
        if (showLoader) setLoading(true)
        else setRefreshing(true)

        const response = await fetch(`${API_BASE}/system/users/`, {
          method: "GET",
          credentials: "include",
          headers: {
            Accept: "application/json",
          },
        })

        const data: UsersListResponse = await response.json()

        if (!response.ok || !data.success) {
          throw new Error(data.error || t.usersLoadError)
        }

        setUsers(data.users || [])

        if (data.roles?.length) {
          setRoles(data.roles)
        }
      } catch (error) {
        console.error("Fetch system users error:", error)
        toast.error(t.usersLoadError)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [t.usersLoadError]
  )

  const fetchRoles = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/system/users/roles/`, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
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
      toast.error(t.fullNameRequired)
      return
    }

    if (!safeUsername) {
      toast.error(t.usernameRequired)
      return
    }

    if (safeUsername.length < 3) {
      toast.error(t.usernameMin)
      return
    }

    if (!safeEmail || !isValidEmail(safeEmail)) {
      toast.error(t.emailInvalid)
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
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          full_name: safeFullName,
          username: safeUsername,
          email: safeEmail,
          phone: safePhone,
          role,
          status,
        }),
      })

      const data: GenericApiResponse = await response.json()

      if (!response.ok || !data.success) {
        const firstError =
          data.errors && Object.keys(data.errors).length > 0
            ? data.errors[Object.keys(data.errors)[0]]
            : null

        throw new Error(firstError || data.error || t.createError)
      }

      toast.success(t.createSuccess, {
        description: data.temporary_password
          ? `Temporary password: ${data.temporary_password}`
          : t.createSuccessDesc,
      })

      resetForm()
      setOpenCreateDialog(false)
      await fetchUsers(false)
    } catch (error) {
      console.error("Create system user error:", error)
      toast.error(error instanceof Error ? error.message : t.createError)
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
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ user_id: userId }),
      })

      const data: GenericApiResponse = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || t.statusUpdateError)
      }

      toast.success(t.statusUpdateSuccess)
      await fetchUsers(false)
    } catch (error) {
      console.error("Toggle system user status error:", error)
      toast.error(error instanceof Error ? error.message : t.statusUpdateError)
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
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          user_id: userId,
          role: newRole,
        }),
      })

      const data: GenericApiResponse = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || t.roleUpdateError)
      }

      toast.success(t.roleUpdateSuccess)
      await fetchUsers(false)
    } catch (error) {
      console.error("Change system user role error:", error)
      toast.error(error instanceof Error ? error.message : t.roleUpdateError)
    } finally {
      setActionLoadingId(null)
    }
  }

  async function handleResetPassword() {
    if (!resetUserId) return

    if (!newPassword || newPassword.length < 6) {
      toast.error(t.passwordMin)
      return
    }

    if (newPassword !== confirmPassword) {
      toast.error(t.passwordMismatch)
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
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          user_id: resetUserId,
          new_password: newPassword,
        }),
      })

      const data: GenericApiResponse = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || t.passwordUpdateError)
      }

      toast.success(t.passwordUpdateSuccess)

      setOpenResetDialog(false)
      setNewPassword("")
      setConfirmPassword("")
      setResetUserId(null)
    } catch (error) {
      console.error("Reset password error:", error)
      toast.error(error instanceof Error ? error.message : t.passwordUpdateError)
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
    <div dir={direction} className="space-y-6 p-6">
      <div className="flex flex-col items-start justify-between gap-4 lg:flex-row">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            {t.pageTitle}
          </h1>
          <p className="text-muted-foreground">{t.pageSubtitle}</p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => fetchUsers(false)}
            disabled={refreshing}
            className="gap-2"
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCcw className="h-4 w-4" />
            )}
            {t.refresh}
          </Button>

          <Dialog open={openCreateDialog} onOpenChange={setOpenCreateDialog}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <UserPlus className="h-4 w-4" />
                {t.addUser}
              </Button>
            </DialogTrigger>

            <DialogContent dir={direction} className="sm:max-w-3xl">
              <DialogHeader>
                <DialogTitle>{t.addUserTitle}</DialogTitle>
                <DialogDescription>{t.addUserDesc}</DialogDescription>
              </DialogHeader>

              <div className="grid grid-cols-1 gap-6 py-2 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.fullName}</label>
                      <Input
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder={t.exampleName}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.username}</label>
                      <Input
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder={t.exampleUsername}
                        dir="ltr"
                        lang="en"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.email}</label>
                      <Input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder={t.exampleEmail}
                        dir="ltr"
                        lang="en"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.phone}</label>
                      <Input
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder={t.examplePhone}
                        dir="ltr"
                        lang="en"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.role}</label>
                      <Select
                        value={role}
                        onValueChange={(value) => setRole(value as InternalRole)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={t.selectRole} />
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
                      <label className="text-sm font-medium">{t.status}</label>
                      <Select
                        value={status}
                        onValueChange={(value) => setStatus(value as UserStatus)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={t.selectStatus} />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ACTIVE">{t.activeStatus}</SelectItem>
                          <SelectItem value="INACTIVE">{t.inactiveStatus}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                <Card className="h-fit border-border/60">
                  <CardHeader>
                    <CardTitle className="text-sm">{t.roleSummary}</CardTitle>
                    <CardDescription>{t.quickPreview}</CardDescription>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium gap-1",
                        getRoleBadgeClass(role)
                      )}
                    >
                      {getRoleIcon(role)}
                      {getRoleLabel(role, locale)}
                    </span>

                    <Separator />

                    <div className="space-y-3 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">{t.status}</span>
                        <span className="font-medium">
                          {status === "ACTIVE" ? t.activeStatus : t.inactiveStatus}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">{t.binding}</span>
                        <span className="font-medium text-emerald-600">{t.live}</span>
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
                  {t.cancel}
                </Button>

                <Button type="button" onClick={handleCreateUser} disabled={submitting} className="gap-2">
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {t.creating}
                    </>
                  ) : (
                    <>
                      <UserPlus className="h-4 w-4" />
                      {t.saveUser}
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title={t.totalUsers}
          value={total}
          description={t.allInternalUsers}
          icon={Users}
        />

        <StatCard
          title={t.active}
          value={active}
          description={t.activeAccounts}
          icon={CheckCircle2}
          valueClassName="text-emerald-600"
        />

        <StatCard
          title={t.systemAdmin}
          value={systemAdmins}
          description={t.operationalAccess}
          icon={Shield}
          valueClassName="text-blue-600"
        />

        <StatCard
          title={t.support}
          value={supportUsers}
          description={t.supportTeam}
          icon={Headset}
          valueClassName="text-violet-600"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-1">
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle>{t.accessOverview}</CardTitle>
            <CardDescription>{t.internalAccessDistribution}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span>{t.superAdmin}</span>
              <span className="inline-flex items-center rounded-full border border-yellow-200 bg-yellow-50 px-2.5 py-1 text-xs font-medium text-yellow-700">
                {formatNumberEn(superAdmins)}
              </span>
            </div>

            <div className="flex justify-between">
              <span>{t.systemAdmin}</span>
              <span className="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
                {formatNumberEn(systemAdmins)}
              </span>
            </div>

            <div className="flex justify-between">
              <span>{t.support}</span>
              <span className="inline-flex items-center rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1 text-xs font-medium text-violet-700">
                {formatNumberEn(supportUsers)}
              </span>
            </div>

            <Separator />

            <div className="flex justify-between font-medium">
              <span>{t.inactiveAccounts}</span>
              <span className="tabular-nums">{formatNumberEn(inactive)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/60">
        <CardHeader>
          <CardTitle>{t.filters}</CardTitle>
          <CardDescription>{t.filtersDesc}</CardDescription>
        </CardHeader>

        <CardContent>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative w-full max-w-sm">
              <Search
                className={cn(
                  "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                  isArabic ? "right-3" : "left-3"
                )}
              />
              <Input
                placeholder={t.searchPlaceholder}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className={isArabic ? "pr-9" : "pl-9"}
              />
            </div>

            <Select
              value={roleFilter}
              onValueChange={(value) => setRoleFilter(value as "ALL" | InternalRole)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={t.allRoles} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">{t.allRoles}</SelectItem>
                {roles.map((item) => (
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
                <SelectValue placeholder={t.allStatus} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">{t.allStatus}</SelectItem>
                <SelectItem value="ACTIVE">{t.activeStatus}</SelectItem>
                <SelectItem value="INACTIVE">{t.inactiveStatus}</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline" onClick={handleResetFilters} className="gap-2">
              <RefreshCcw className="h-4 w-4" />
              {t.reset}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/60">
        <CardHeader>
          <CardTitle>{t.usersTableTitle}</CardTitle>
          <CardDescription>
            {t.totalResults}: {formatNumberEn(filteredUsers.length)}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground">
              <Loader2 className="me-2 h-5 w-5 animate-spin" />
              {t.loadingUsers}
            </div>
          ) : (
            <div className="w-full">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-[220px]">{t.user}</TableHead>
                    <TableHead className="min-w-[220px]">{t.contact}</TableHead>
                    <TableHead className="min-w-[140px]">{t.role}</TableHead>
                    <TableHead className="min-w-[110px]">{t.status}</TableHead>
                    <TableHead className="min-w-[120px]">{t.created}</TableHead>
                    <TableHead className="min-w-[110px]">{t.password}</TableHead>
                    <TableHead className="min-w-[70px]">{t.actions}</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {filteredUsers.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="py-10 text-center text-muted-foreground">
                        {t.noUsersFound}
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
                            <div className="truncate text-xs text-muted-foreground" dir="ltr">
                              @{user.username}
                            </div>
                          </div>
                        </div>
                      </TableCell>

                      <TableCell>
                        <div className="space-y-1 text-sm">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Mail className="h-3.5 w-3.5 shrink-0" />
                            <span className="truncate" dir="ltr">
                              {user.email || "--"}
                            </span>
                          </div>

                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Phone className="h-3.5 w-3.5 shrink-0" />
                            <span className="truncate" dir="ltr">
                              {user.phone || "--"}
                            </span>
                          </div>
                        </div>
                      </TableCell>

                      <TableCell>
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium gap-1",
                            getRoleBadgeClass(user.role)
                          )}
                        >
                          {getRoleIcon(user.role)}
                          {getRoleLabel(user.role, locale)}
                        </span>
                      </TableCell>

                      <TableCell>
                        <UserStatusPill status={user.status} locale={locale} />
                      </TableCell>

                      <TableCell className="tabular-nums" dir="ltr">
                        {formatDate(user.created_at)}
                      </TableCell>

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
                          className="gap-2"
                        >
                          {actionLoadingId === user.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <KeyRound className="h-4 w-4" />
                          )}
                          {t.resetPassword}
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
                            <DropdownMenuLabel>{t.actionsLabel}</DropdownMenuLabel>
                            <DropdownMenuSeparator />

                            <DropdownMenuItem onClick={() => openUserProfile(user)}>
                              <Eye className="me-2 h-4 w-4" />
                              {t.viewProfile}
                            </DropdownMenuItem>

                            <DropdownMenuItem onClick={() => handleToggleStatus(user.id)}>
                              {user.status === "ACTIVE" ? t.disableUser : t.enableUser}
                            </DropdownMenuItem>

                            <DropdownMenuSeparator />
                            <DropdownMenuLabel>{t.changeRole}</DropdownMenuLabel>

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
        <DialogContent dir={direction} className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t.userProfile}</DialogTitle>
            <DialogDescription>{t.userProfileDesc}</DialogDescription>
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
                  <div className="text-lg font-semibold">{selectedUser.full_name}</div>
                  <div className="text-sm text-muted-foreground" dir="ltr">
                    @{selectedUser.username}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium gap-1",
                        getRoleBadgeClass(selectedUser.role)
                      )}
                    >
                      {getRoleIcon(selectedUser.role)}
                      {getRoleLabel(selectedUser.role, locale)}
                    </span>

                    <UserStatusPill status={selectedUser.status} locale={locale} />
                  </div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <Card className="border-border/60">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">{t.contactDetails}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div className="flex items-start gap-3">
                      <Mail className="mt-0.5 h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-muted-foreground">{t.email}</div>
                        <div className="font-medium" dir="ltr">
                          {selectedUser.email || "--"}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Phone className="mt-0.5 h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-muted-foreground">{t.phone}</div>
                        <div className="font-medium" dir="ltr">
                          {selectedUser.phone || "--"}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border/60">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">{t.accountDetails}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <div className="flex items-start gap-3">
                      <CalendarDays className="mt-0.5 h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-muted-foreground">{t.createdAt}</div>
                        <div className="font-medium tabular-nums" dir="ltr">
                          {formatDate(selectedUser.created_at)}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <Clock3 className="mt-0.5 h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-muted-foreground">{t.lastLogin}</div>
                        <div className="font-medium tabular-nums" dir="ltr">
                          {formatDateTime(selectedUser.last_login, locale)}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          ) : null}

          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenProfileDialog(false)}>
              {t.close}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* RESET PASSWORD DIALOG */}
      <Dialog open={openResetDialog} onOpenChange={setOpenResetDialog}>
        <DialogContent dir={direction} className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t.changePassword}</DialogTitle>
            <DialogDescription>{t.changePasswordDesc}</DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">{t.newPassword}</label>

              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder={t.newPassword}
                dir="ltr"
                lang="en"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">{t.confirmPassword}</label>

              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder={t.confirmPassword}
                dir="ltr"
                lang="en"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenResetDialog(false)}>
              {t.cancel}
            </Button>

            <Button
              onClick={handleResetPassword}
              disabled={actionLoadingId === resetUserId}
              className="gap-2"
            >
              {actionLoadingId === resetUserId ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : null}
              {t.updatePassword}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}