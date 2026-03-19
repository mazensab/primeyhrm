"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu"
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

import {
  Building2,
  Users,
  Calendar,
  Crown,
  Activity,
  Mail,
  Phone,
  MapPin,
  FileText,
  Landmark,
  MoreHorizontal,
  UserCog,
  Power,
  Shield,
  Loader2,
  PencilLine,
  CheckCircle2,
  XCircle,
  KeyRound,
  LogIn
} from "lucide-react"
/* =========================================================
   Types
========================================================= */

interface CompanyNationalAddress {
  building_number?: string | null
  street?: string | null
  district?: string | null
  city?: string | null
  postal_code?: string | null
  short_address?: string | null
}

interface CompanyDetails {
  id: number
  name: string
  is_active: boolean
  created_at: string
  commercial_number?: string | null
  vat_number?: string | null
  phone?: string | null
  email?: string | null
  national_address?: CompanyNationalAddress

  owner?: {
    email?: string
  }

  subscription?: {
    plan?: string
    status?: string
  }

  users_count: number
}

interface CompanyUser {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  full_name?: string | null
  phone?: string | null
  avatar?: string | null
  created_at?: string | null
}

interface CompanySubscription {
  id: number
  plan: string
  status: string
  billing_cycle?: string
  started_at?: string
  ends_at?: string
}

interface CompanyInvoice {
  id: number
  number: string
  status: string
  total_amount?: number
  currency?: string
  created_at?: string
  issue_date?: string
}

interface CompanyInfoForm {
  name: string
  commercial_number: string
  vat_number: string
  phone: string
  email: string
  building_number: string
  street: string
  district: string
  city: string
  postal_code: string
  short_address: string
}

interface EditCompanyUserForm {
  username: string
  email: string
}

interface CompanyUserApiResponse {
  success?: boolean
  message?: string
  error?: string
  errors?: Record<string, string | string[]>
  details?: string
  temporary_password?: string
  redirect_to?: string
  user?: CompanyUser
}

type CompanyUserRole = "OWNER" | "ADMIN" | "HR" | "MANAGER" | "EMPLOYEE"

const COMPANY_USER_ROLE_OPTIONS: { value: CompanyUserRole; label: string }[] = [
  { value: "OWNER", label: "Owner" },
  { value: "ADMIN", label: "Admin" },
  { value: "HR", label: "HR" },
  { value: "MANAGER", label: "Manager" },
  { value: "EMPLOYEE", label: "Employee" }
]

/* =========================================================
   Helpers
========================================================= */

function displayValue(value?: string | null) {
  if (value === null || value === undefined) return "-"
  const clean = String(value).trim()
  return clean ? clean : "-"
}

function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null
  }

  return null
}

function buildCompanyInfoForm(companyData: CompanyDetails): CompanyInfoForm {
  return {
    name: companyData.name || "",
    commercial_number: companyData.commercial_number || "",
    vat_number: companyData.vat_number || "",
    phone: companyData.phone || "",
    email: companyData.email || "",
    building_number: companyData.national_address?.building_number || "",
    street: companyData.national_address?.street || "",
    district: companyData.national_address?.district || "",
    city: companyData.national_address?.city || "",
    postal_code: companyData.national_address?.postal_code || "",
    short_address: companyData.national_address?.short_address || ""
  }
}

function buildEditCompanyUserForm(user: CompanyUser): EditCompanyUserForm {
  return {
    username: user.username || "",
    email: user.email || ""
  }
}

function OverviewField({
  label,
  value,
  icon
}: {
  label: string
  value: string
  icon?: React.ReactNode
}) {
  return (
    <div className="rounded-xl border bg-muted/20 px-4 py-3">
      <div className="mb-1 flex items-center gap-2 text-xs font-medium text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <div className="break-words text-sm font-semibold text-foreground">
        {value}
      </div>
    </div>
  )
}

function normalizeCompanyUserRole(role?: string | null): CompanyUserRole {
  const value = String(role || "").trim().toUpperCase()

  if (value === "OWNER") return "OWNER"
  if (value === "ADMIN") return "ADMIN"
  if (value === "HR") return "HR"
  if (value === "MANAGER") return "MANAGER"

  return "EMPLOYEE"
}

function getCompanyUserRoleLabel(role?: string | null) {
  const normalized = normalizeCompanyUserRole(role)
  const found = COMPANY_USER_ROLE_OPTIONS.find((item) => item.value === normalized)
  return found?.label || normalized
}

function getCompanyUserRoleBadgeClass(role?: string | null) {
  const normalized = normalizeCompanyUserRole(role)

  switch (normalized) {
    case "OWNER":
      return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300"
    case "ADMIN":
      return "border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300"
    case "HR":
      return "border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-300"
    case "MANAGER":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
    default:
      return "border-slate-500/30 bg-slate-500/10 text-slate-700 dark:text-slate-300"
  }
}

function getInitials(value?: string | null) {
  const safe = String(value || "").trim()
  if (!safe) return "U"

  return (
    safe
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "U"
  )
}

function getCompanyUserStatusBadge(isActive: boolean) {
  if (isActive) {
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
        Disabled
      </Badge>
  )
}

function formatDate(value?: string | null) {
  if (!value) return "--"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit"
  }).format(date)
}

function daysRemaining(date?: string) {
  if (!date) return null

  const end = new Date(date)
  const today = new Date()

  const diff = end.getTime() - today.getTime()

  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

/* =========================================================
   Page
========================================================= */

export default function CompanyDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const companyId = params.id

  const [company, setCompany] = useState<CompanyDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [users, setUsers] = useState<CompanyUser[]>([])
  const [subscription, setSubscription] = useState<CompanySubscription | null>(null)
  const remainingDays = daysRemaining(subscription?.ends_at)
  const [invoices, setInvoices] = useState<CompanyInvoice[]>([])
  const [activityLogs, setActivityLogs] = useState<any[]>([])

  const [isEditingCompanyInfo, setIsEditingCompanyInfo] = useState(false)
  const [savingCompanyInfo, setSavingCompanyInfo] = useState(false)
  const [companyInfoForm, setCompanyInfoForm] = useState<CompanyInfoForm>({
    name: "",
    commercial_number: "",
    vat_number: "",
    phone: "",
    email: "",
    building_number: "",
    street: "",
    district: "",
    city: "",
    postal_code: "",
    short_address: ""
  })

  /* =========================================================
     Company Users State
  ========================================================= */

  const [usersLoading, setUsersLoading] = useState(false)
  const [selectedUser, setSelectedUser] = useState<CompanyUser | null>(null)
  const [enteringUserId, setEnteringUserId] = useState<number | null>(null)
  
  const [editUserDialogOpen, setEditUserDialogOpen] = useState(false)
  const [editUserForm, setEditUserForm] = useState<EditCompanyUserForm>({
    username: "",
    email: ""
  })
  const [savingUserEdit, setSavingUserEdit] = useState(false)

  const [roleDialogOpen, setRoleDialogOpen] = useState(false)
  const [selectedRole, setSelectedRole] = useState<CompanyUserRole>("EMPLOYEE")
  const [savingRoleChange, setSavingRoleChange] = useState(false)

  const [toggleDialogOpen, setToggleDialogOpen] = useState(false)
  const [togglingUserStatus, setTogglingUserStatus] = useState(false)

  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false)
  const [resetUserId, setResetUserId] = useState<number | null>(null)
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [resettingPassword, setResettingPassword] = useState(false)

  const usersCountLabel = useMemo(() => {
    return `${users.length} users`
  }, [users])

  /* =========================================================
     Company Users Helpers
  ========================================================= */

  async function loadCompanyUsers() {
    setUsersLoading(true)

    try {
      const usersRes = await fetch(
        `http://localhost:8000/api/system/companies/${companyId}/users/`,
        { credentials: "include" }
      )

      if (!usersRes.ok) {
        throw new Error("Failed to fetch company users")
      }

      const usersData = await usersRes.json()
      setUsers(usersData.results || [])
    } catch (error) {
      console.error("Company users fetch error:", error)
      toast.error("Failed to load company users")
    } finally {
      setUsersLoading(false)
    }
  }

  function openEditUserDialog(user: CompanyUser) {
    setSelectedUser(user)
    setEditUserForm(buildEditCompanyUserForm(user))
    setEditUserDialogOpen(true)
  }

  function openRoleDialog(user: CompanyUser) {
    setSelectedUser(user)
    setSelectedRole(normalizeCompanyUserRole(user.role))
    setRoleDialogOpen(true)
  }

  function openToggleDialog(user: CompanyUser) {
    setSelectedUser(user)
    setToggleDialogOpen(true)
  }

  function openResetPasswordDialog(user: CompanyUser) {
    setSelectedUser(user)
    setResetUserId(user.id)
    setNewPassword("")
    setConfirmPassword("")
    setResetPasswordDialogOpen(true)
  }

  function handleEditUserInputChange(
    field: keyof EditCompanyUserForm,
    value: string
  ) {
    setEditUserForm((prev) => ({
      ...prev,
      [field]: value
    }))
  }

  async function handleSaveUserEdit() {
    if (!selectedUser) return

    const username = editUserForm.username.trim()
    const email = editUserForm.email.trim()

    if (!username) {
      toast.error("Username is required")
      return
    }

    if (!email) {
      toast.error("Email is required")
      return
    }

    setSavingUserEdit(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        `http://localhost:8000/api/system/companies/${companyId}/users/${selectedUser.id}/update/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || ""
          },
          body: JSON.stringify({
            username,
            email
          })
        }
      )

      const data: CompanyUserApiResponse = await res.json()

      if (!res.ok) {
        const rawFirstError = data?.errors
          ? Object.values(data.errors)[0]
          : null

        const firstError = Array.isArray(rawFirstError)
          ? rawFirstError[0]
          : rawFirstError

        toast.error(
          typeof firstError === "string"
            ? firstError
            : data.error || "Failed to update company user"
        )
        return
      }      
      setUsers((prev) =>
        prev.map((item) =>
          item.id === selectedUser.id
            ? {
                ...item,
                username: data.user?.username ?? username,
                email: data.user?.email ?? email,
                full_name: data.user?.full_name ?? item.full_name,
                phone: data.user?.phone ?? item.phone,
                avatar: data.user?.avatar ?? item.avatar,
                role: data.user?.role ?? item.role,
                is_active:
                  typeof data.user?.is_active === "boolean"
                    ? data.user.is_active
                    : item.is_active
              }
            : item
        )
      )

      setEditUserDialogOpen(false)
      setSelectedUser(null)
      toast.success(data.message || "User updated successfully")
    } catch (error) {
      console.error("Update company user error:", error)
      toast.error("Server error while updating company user")
    } finally {
      setSavingUserEdit(false)
    }
  }

  async function handleChangeUserRole() {
    if (!selectedUser) return

    setSavingRoleChange(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        `http://localhost:8000/api/system/companies/${companyId}/users/${selectedUser.id}/change-role/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || ""
          },
          body: JSON.stringify({
            role: selectedRole
          })
        }
      )

      const data: CompanyUserApiResponse = await res.json()

      if (!res.ok) {
        toast.error(data.error || "Failed to change user role")
        return
      }

      setUsers((prev) =>
        prev.map((item) =>
          item.id === selectedUser.id
            ? {
                ...item,
                role: data.user?.role ?? selectedRole
              }
            : item
        )
      )

      setRoleDialogOpen(false)
      setSelectedUser(null)
      toast.success(data.message || "User role updated successfully")
    } catch (error) {
      console.error("Change company user role error:", error)
      toast.error("Server error while changing user role")
    } finally {
      setSavingRoleChange(false)
    }
  }

  async function handleToggleUserStatus() {
    if (!selectedUser) return

    setTogglingUserStatus(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        `http://localhost:8000/api/system/companies/${companyId}/users/${selectedUser.id}/toggle-status/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || ""
          }
        }
      )

      const data: CompanyUserApiResponse = await res.json()

      if (!res.ok) {
        toast.error(data.error || "Failed to change user status")
        return
      }

      const nextIsActive =
        typeof data.user?.is_active === "boolean"
          ? data.user.is_active
          : !selectedUser.is_active

      setUsers((prev) =>
        prev.map((item) =>
          item.id === selectedUser.id
            ? {
                ...item,
                is_active: nextIsActive
              }
            : item
        )
      )

      setToggleDialogOpen(false)
      setSelectedUser(null)
      toast.success(
        data.message ||
          (nextIsActive ? "User enabled successfully" : "User disabled successfully")
      )
    } catch (error) {
      console.error("Toggle company user status error:", error)
      toast.error("Server error while changing user status")
    } finally {
      setTogglingUserStatus(false)
    }
  }

    async function handleEnterAsUser(user: CompanyUser) {
    if (!user?.id) return

    setEnteringUserId(user.id)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        `http://localhost:8000/api/system/companies/${companyId}/users/${user.id}/enter/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || ""
          }
        }
      )

      const data: CompanyUserApiResponse = await res.json()

      if (!res.ok) {
        toast.error(data.error || "Failed to enter company session")
        return
      }

      toast.success(
        data.message || `Entered as ${user.username}`
      )

      window.location.href = data.redirect_to || "/company"
    } catch (error) {
      console.error("Enter as company user error:", error)
      toast.error("Server error while entering company session")
    } finally {
      setEnteringUserId(null)
    }
  }

  async function handleResetPassword() {
    if (!resetUserId || !selectedUser) return

    if (!newPassword || newPassword.length < 6) {
      toast.error("Password must be at least 6 characters")
      return
    }

    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match")
      return
    }

    setResettingPassword(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        `http://localhost:8000/api/system/companies/${companyId}/users/${resetUserId}/reset-password/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || ""
          },
          body: JSON.stringify({
            new_password: newPassword
          })
        }
      )

      const data: CompanyUserApiResponse = await res.json()

      if (!res.ok) {
        toast.error(data.error || "Failed to update password")
        return
      }

      toast.success(data.message || "Password updated successfully")

      setResetPasswordDialogOpen(false)
      setResetUserId(null)
      setNewPassword("")
      setConfirmPassword("")
      setSelectedUser(null)
    } catch (error) {
      console.error("Reset company user password error:", error)
      toast.error("Server error while updating password")
    } finally {
      setResettingPassword(false)
    }
  }

  /* =========================================================
     Fetch Company
  ========================================================= */

  useEffect(() => {
    async function loadCompany() {
      try {
        const res = await fetch(
          `http://localhost:8000/api/system/companies/${companyId}/`,
          { credentials: "include" }
        )

        if (!res.ok) {
          throw new Error("Failed to fetch company")
        }

        const data = await res.json()

        const companyData: CompanyDetails = {
          id: data.company.id,
          name: data.company.name,
          is_active: data.company.is_active,
          created_at: data.company.created_at,
          commercial_number: data.company.commercial_number,
          vat_number: data.company.vat_number,
          phone: data.company.phone,
          email: data.company.email,
          national_address: data.company.national_address || {},
          owner: data.owner,
          subscription: data.subscription,
          users_count: data.users_count
        }

        setCompany(companyData)
        setCompanyInfoForm(buildCompanyInfoForm(companyData))
      } catch (error) {
        console.error("Company fetch error:", error)
      } finally {
        await loadCompanyUsers()

        const subRes = await fetch(
          `http://localhost:8000/api/system/companies/${companyId}/subscription/`,
          { credentials: "include" }
        )

        if (subRes.ok) {
          const subData = await subRes.json()
          setSubscription(subData.subscription || null)
        }

        const invoicesRes = await fetch(
          `http://localhost:8000/api/system/companies/${companyId}/invoices/`,
          { credentials: "include" }
        )

        if (invoicesRes.ok) {
          const invoicesData = await invoicesRes.json()
          setInvoices(invoicesData.data?.results || [])
        }

        const activityRes = await fetch(
          `http://localhost:8000/api/system/companies/${companyId}/activity/`,
          { credentials: "include" }
        )

        if (activityRes.ok) {
          const activityData = await activityRes.json()
          setActivityLogs(activityData.data?.results || [])
        }

        setLoading(false)
      }
    }

    loadCompany()
  }, [companyId])

  /* =========================================================
   Company Info Editing
  ========================================================= */

  function handleCompanyInfoInputChange(
    field: keyof CompanyInfoForm,
    value: string
  ) {
    setCompanyInfoForm((prev) => ({
      ...prev,
      [field]: value
    }))
  }

  function handleStartEditCompanyInfo() {
    if (!company) return
    setCompanyInfoForm(buildCompanyInfoForm(company))
    setIsEditingCompanyInfo(true)
  }

  function handleCancelEditCompanyInfo() {
    if (!company) {
      setIsEditingCompanyInfo(false)
      return
    }

    setCompanyInfoForm(buildCompanyInfoForm(company))
    setIsEditingCompanyInfo(false)
  }

  async function handleSaveCompanyInfo() {
    if (!company) return

    setSavingCompanyInfo(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const payload = {
        name: companyInfoForm.name,
        commercial_number: companyInfoForm.commercial_number,
        vat_number: companyInfoForm.vat_number,
        phone: companyInfoForm.phone,
        email: companyInfoForm.email,
        national_address: {
          building_number: companyInfoForm.building_number,
          street: companyInfoForm.street,
          district: companyInfoForm.district,
          city: companyInfoForm.city,
          postal_code: companyInfoForm.postal_code,
          short_address: companyInfoForm.short_address
        }
      }

      const res = await fetch(
        `http://localhost:8000/api/system/companies/${companyId}/update/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || ""
          },
          body: JSON.stringify(payload)
        }
      )

      const data = await res.json()

      if (!res.ok) {
        toast.error(data.error || "Failed to update company information")
        return
      }

      setCompany((prev) => {
        if (!prev) return prev

        return {
          ...prev,
          name: data.company?.name ?? prev.name,
          commercial_number: data.company?.commercial_number ?? prev.commercial_number,
          vat_number: data.company?.vat_number ?? prev.vat_number,
          phone: data.company?.phone ?? prev.phone,
          email: data.company?.email ?? prev.email,
          national_address: {
            building_number: data.company?.national_address?.building_number ?? "",
            street: data.company?.national_address?.street ?? "",
            district: data.company?.national_address?.district ?? "",
            city: data.company?.national_address?.city ?? "",
            postal_code: data.company?.national_address?.postal_code ?? "",
            short_address: data.company?.national_address?.short_address ?? ""
          }
        }
      })

      setCompanyInfoForm({
        name: data.company?.name ?? companyInfoForm.name,
        commercial_number: data.company?.commercial_number ?? "",
        vat_number: data.company?.vat_number ?? "",
        phone: data.company?.phone ?? "",
        email: data.company?.email ?? "",
        building_number: data.company?.national_address?.building_number ?? "",
        street: data.company?.national_address?.street ?? "",
        district: data.company?.national_address?.district ?? "",
        city: data.company?.national_address?.city ?? "",
        postal_code: data.company?.national_address?.postal_code ?? "",
        short_address: data.company?.national_address?.short_address ?? ""
      })

      setIsEditingCompanyInfo(false)
      toast.success(data.message || "Company information updated successfully")
    } catch (error) {
      console.error("Update company info error:", error)
      toast.error("Server error while updating company information")
    } finally {
      setSavingCompanyInfo(false)
    }
  }

  /* =========================================================
   Renew Subscription
  ========================================================= */

  async function handleRenew() {
    if (!subscription) return

    try {
      const res = await fetch(
        `http://localhost:8000/api/system/subscriptions/${subscription.id}/renew/`,
        {
          method: "POST",
          credentials: "include"
        }
      )

      const data = await res.json()

      if (!res.ok) {
        toast.error(data.error || "Renew failed")
        return
      }

      toast.success("Renewal invoice created")
      router.push(`/system/invoices/${data.invoice_id}`)
    } catch {
      toast.error("Server error")
    }
  }

  /* =========================================================
     Loading
  ========================================================= */

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-60" />
        <Skeleton className="h-56 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  if (!company) {
    return (
      <div className="text-muted-foreground">
        Company not found
      </div>
    )
  }

  /* =========================================================
     UI
  ========================================================= */

  return (
    <>
      <div className="space-y-6">
        <div className="rounded-2xl border bg-background p-6 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
                <Building2 className="h-6 w-6" />
              </div>

              <div>
                <h1 className="text-2xl font-semibold leading-tight">
                  {company.name}
                </h1>

                <p className="mt-1 text-sm text-muted-foreground">
                  Company administration and platform usage
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Badge
                variant={company.is_active ? "secondary" : "destructive"}
                className="px-3 py-1 text-sm"
              >
                {company.is_active ? "ACTIVE" : "DISABLED"}
              </Badge>
            </div>
          </div>
        </div>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-5 md:max-w-2xl">
            <TabsTrigger value="overview">
              Overview
            </TabsTrigger>

            <TabsTrigger value="users">
              Users
            </TabsTrigger>

            <TabsTrigger value="subscription">
              Subscription
            </TabsTrigger>

            <TabsTrigger value="invoices">
              Invoices
            </TabsTrigger>

            <TabsTrigger value="activity">
              Activity
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6 space-y-6">
            <Card className="border shadow-sm">
              <CardHeader className="flex flex-col gap-4 border-b bg-muted/20 pb-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Building2 className="h-5 w-5" />
                    Company Information
                  </CardTitle>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Main company data, tax details, and national address.
                  </p>
                </div>

                {!isEditingCompanyInfo ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleStartEditCompanyInfo}
                  >
                    Edit
                  </Button>
                ) : (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCancelEditCompanyInfo}
                      disabled={savingCompanyInfo}
                    >
                      Cancel
                    </Button>

                    <Button
                      size="sm"
                      onClick={handleSaveCompanyInfo}
                      disabled={savingCompanyInfo}
                    >
                      {savingCompanyInfo ? "Saving..." : "Save Changes"}
                    </Button>
                  </div>
                )}
              </CardHeader>

              <CardContent className="space-y-8 pt-6">
                {!isEditingCompanyInfo ? (
                  <>
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                        <FileText className="h-4 w-4" />
                        Basic Information
                      </div>

                      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                        <OverviewField
                          label="Company Name"
                          value={displayValue(company.name)}
                          icon={<Building2 className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="Owner"
                          value={displayValue(company.owner?.email)}
                          icon={<Users className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="Company Email"
                          value={displayValue(company.email)}
                          icon={<Mail className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="Phone"
                          value={displayValue(company.phone)}
                          icon={<Phone className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="Commercial No."
                          value={displayValue(company.commercial_number)}
                          icon={<FileText className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="VAT No."
                          value={displayValue(company.vat_number)}
                          icon={<Landmark className="h-3.5 w-3.5" />}
                        />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                        <MapPin className="h-4 w-4" />
                        National Address
                      </div>

                      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                        <OverviewField
                          label="Building No."
                          value={displayValue(company.national_address?.building_number)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="Street"
                          value={displayValue(company.national_address?.street)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="District"
                          value={displayValue(company.national_address?.district)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="City"
                          value={displayValue(company.national_address?.city)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="Postal Code"
                          value={displayValue(company.national_address?.postal_code)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                        />
                        <OverviewField
                          label="Short Address"
                          value={displayValue(company.national_address?.short_address)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                        />
                      </div>
                    </div>

                    <div className="rounded-xl border bg-muted/20 px-4 py-3">
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-sm font-medium text-muted-foreground">
                          Status
                        </span>

                        <Badge
                          variant={company.is_active ? "secondary" : "destructive"}
                        >
                          {company.is_active ? "ACTIVE" : "DISABLED"}
                        </Badge>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                        <FileText className="h-4 w-4" />
                        Basic Information
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            Company Name
                          </span>
                          <Input
                            value={companyInfoForm.name}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("name", e.target.value)
                            }
                            placeholder="Company Name"
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            Owner
                          </span>
                          <Input
                            value={displayValue(company.owner?.email)}
                            disabled
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            Company Email
                          </span>
                          <Input
                            type="email"
                            value={companyInfoForm.email}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("email", e.target.value)
                            }
                            placeholder="Company Email"
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            Phone
                          </span>
                          <Input
                            value={companyInfoForm.phone}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("phone", e.target.value)
                            }
                            placeholder="Phone"
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            Commercial No.
                          </span>
                          <Input
                            value={companyInfoForm.commercial_number}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("commercial_number", e.target.value)
                            }
                            placeholder="Commercial Number"
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            VAT No.
                          </span>
                          <Input
                            value={companyInfoForm.vat_number}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("vat_number", e.target.value)
                            }
                            placeholder="VAT Number"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                        <MapPin className="h-4 w-4" />
                        National Address
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            Building No.
                          </span>
                          <Input
                            value={companyInfoForm.building_number}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("building_number", e.target.value)
                            }
                            placeholder="Building Number"
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            Street
                          </span>
                          <Input
                            value={companyInfoForm.street}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("street", e.target.value)
                            }
                            placeholder="Street"
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            District
                          </span>
                          <Input
                            value={companyInfoForm.district}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("district", e.target.value)
                            }
                            placeholder="District"
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            City
                          </span>
                          <Input
                            value={companyInfoForm.city}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("city", e.target.value)
                            }
                            placeholder="City"
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            Postal Code
                          </span>
                          <Input
                            value={companyInfoForm.postal_code}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("postal_code", e.target.value)
                            }
                            placeholder="Postal Code"
                          />
                        </div>

                        <div className="space-y-2">
                          <span className="text-sm text-muted-foreground">
                            Short Address
                          </span>
                          <Input
                            value={companyInfoForm.short_address}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("short_address", e.target.value)
                            }
                            placeholder="Short Address"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="rounded-xl border bg-muted/20 px-4 py-3">
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-sm font-medium text-muted-foreground">
                          Status
                        </span>

                        <Badge
                          variant={company.is_active ? "secondary" : "destructive"}
                        >
                          {company.is_active ? "ACTIVE" : "DISABLED"}
                        </Badge>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card className="border shadow-sm">
              <CardHeader className="border-b bg-muted/20">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Crown className="h-5 w-5" />
                  Subscription
                </CardTitle>
              </CardHeader>

              <CardContent className="pt-6">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  <OverviewField
                    label="Plan"
                    value={company.subscription?.plan || "-"}
                    icon={<Crown className="h-3.5 w-3.5" />}
                  />
                  <OverviewField
                    label="Users"
                    value={String(company.users_count)}
                    icon={<Users className="h-3.5 w-3.5" />}
                  />
                  <OverviewField
                    label="Status"
                    value={company.subscription?.status || "-"}
                    icon={<Calendar className="h-3.5 w-3.5" />}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="border shadow-sm">
              <CardHeader className="border-b bg-muted/20">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Calendar className="h-5 w-5" />
                  Metadata
                </CardTitle>
              </CardHeader>

              <CardContent className="pt-6">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  <OverviewField
                    label="Company ID"
                    value={String(company.id)}
                    icon={<Building2 className="h-3.5 w-3.5" />}
                  />
                  <OverviewField
                    label="Created"
                    value={new Date(company.created_at).toLocaleDateString("en-CA")}
                    icon={<Calendar className="h-3.5 w-3.5" />}
                  />
                  <OverviewField
                    label="Current Status"
                    value={company.is_active ? "ACTIVE" : "DISABLED"}
                    icon={<Activity className="h-3.5 w-3.5" />}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users">
            <Card className="mt-4 border shadow-sm">
              <CardHeader className="border-b bg-muted/20">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Users className="h-5 w-5" />
                      Company Users
                    </CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Manage company users, permissions, and activation status.
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="px-3 py-1">
                      {usersCountLabel}
                    </Badge>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={loadCompanyUsers}
                      disabled={usersLoading}
                    >
                      {usersLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Refreshing...
                        </>
                      ) : (
                        "Refresh"
                      )}
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="pt-6">
                {usersLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-14 w-full" />
                    <Skeleton className="h-14 w-full" />
                    <Skeleton className="h-14 w-full" />
                  </div>
                ) : (
                  <div className="w-full overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="min-w-[240px]">User</TableHead>
                          <TableHead className="min-w-[220px]">Contact</TableHead>
                          <TableHead className="min-w-[140px]">Role</TableHead>
                          <TableHead className="min-w-[120px]">Status</TableHead>
                          <TableHead className="min-w-[120px]">Created</TableHead>
                          <TableHead className="min-w-[120px]">Password</TableHead>
                          <TableHead className="min-w-[100px]">Edit</TableHead>
                          <TableHead className="min-w-[70px]"></TableHead>
                        </TableRow>
                      </TableHeader>

                      <TableBody>
                        {users.length === 0 && (
                          <TableRow>
                            <TableCell colSpan={8} className="text-center text-muted-foreground">
                              No users found
                            </TableCell>
                          </TableRow>
                        )}

                        {users.map((user) => {
                          const displayName = displayValue(user.full_name) !== "-"
                            ? displayValue(user.full_name)
                            : user.username

                          return (
                            <TableRow key={user.id}>
                              <TableCell>
                                <div className="flex items-center gap-3">
                                  <Avatar className="h-10 w-10 shrink-0">
                                    <AvatarImage
                                      src={user.avatar || ""}
                                      alt={displayName}
                                    />
                                    <AvatarFallback>
                                      {getInitials(displayName)}
                                    </AvatarFallback>
                                  </Avatar>

                                  <div className="min-w-0">
                                    <div className="truncate font-medium">
                                      {displayName}
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
                                    <span className="truncate">
                                      {displayValue(user.email)}
                                    </span>
                                  </div>

                                  <div className="flex items-center gap-2 text-muted-foreground">
                                    <Phone className="h-3.5 w-3.5 shrink-0" />
                                    <span className="truncate">
                                      {displayValue(user.phone)}
                                    </span>
                                  </div>
                                </div>
                              </TableCell>

                              <TableCell>
                                <Badge className={getCompanyUserRoleBadgeClass(user.role)}>
                                  {getCompanyUserRoleLabel(user.role)}
                                </Badge>
                              </TableCell>

                              <TableCell>
                                {getCompanyUserStatusBadge(user.is_active)}
                              </TableCell>

                              <TableCell>
                                {formatDate(user.created_at)}
                              </TableCell>

                              <TableCell>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openResetPasswordDialog(user)}
                                  disabled={resettingPassword && resetUserId === user.id}
                                >
                                  {resettingPassword && resetUserId === user.id ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                  ) : (
                                    <KeyRound className="mr-2 h-4 w-4" />
                                  )}
                                  Reset
                                </Button>
                              </TableCell>

                              <TableCell>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openEditUserDialog(user)}
                                >
                                  <PencilLine className="mr-2 h-4 w-4" />
                                  Edit
                                </Button>
                              </TableCell>

                              <TableCell>
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <Button size="icon" variant="ghost">
                                      <MoreHorizontal className="h-4 w-4" />
                                    </Button>
                                  </DropdownMenuTrigger>

                                  <DropdownMenuContent align="end">
                                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                    <DropdownMenuSeparator />

                                    <DropdownMenuItem onClick={() => openEditUserDialog(user)}>
                                      <PencilLine className="mr-2 h-4 w-4" />
                                      Edit User
                                    </DropdownMenuItem>

                                    <DropdownMenuItem onClick={() => openRoleDialog(user)}>
                                      <Shield className="mr-2 h-4 w-4" />
                                      Change Role
                                    </DropdownMenuItem>

                                    <DropdownMenuItem
                                      onClick={() => handleEnterAsUser(user)}
                                      disabled={!user.is_active || enteringUserId === user.id}
                                    >
                                      {enteringUserId === user.id ? (
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                      ) : (
                                        <LogIn className="mr-2 h-4 w-4" />
                                      )}
                                      Enter as User
                                    </DropdownMenuItem>

                                    <DropdownMenuItem onClick={() => openResetPasswordDialog(user)}>
                                      <KeyRound className="mr-2 h-4 w-4" />
                                      Reset Password
                                    </DropdownMenuItem>

                                    <DropdownMenuSeparator />

                                    <DropdownMenuItem onClick={() => openToggleDialog(user)}>
                                      <Power className="mr-2 h-4 w-4" />
                                      {user.is_active ? "Disable User" : "Enable User"}
                                    </DropdownMenuItem>                                    
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              </TableCell>
                            </TableRow>
                          )
                        })}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="subscription">
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Crown className="w-4 h-4" />
                  Subscription Details
                </CardTitle>
              </CardHeader>

              <CardContent>
                {!subscription ? (
                  <div className="text-muted-foreground">
                    No subscription found
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Plan</span>
                      <span className="font-medium">{subscription.plan}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant="secondary">
                        {subscription.status}
                      </Badge>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Billing Cycle</span>
                      <span className="font-medium">
                        {subscription.billing_cycle || "-"}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Start Date</span>
                      <span className="font-medium">
                        {subscription.started_at
                          ? new Date(subscription.started_at).toLocaleDateString("en-CA")
                          : "-"
                        }  
                    </span>
                    </div>

                    {remainingDays !== null && remainingDays <= 10 && (
                      <div className="text-sm font-medium text-amber-600">
                        Subscription expires in {remainingDays} days
                      </div>
                    )}

                    {remainingDays !== null && remainingDays <= 10 && (
                      <div className="pt-4">
                        <Button onClick={handleRenew}>
                          Renew Subscription
                        </Button>
                      </div>
                    )}

                    <div className="flex justify-between">
                      <span className="text-muted-foreground">End Date</span>
                      <span className="font-medium">
                        {subscription.ends_at
                          ? new Date(subscription.ends_at).toLocaleDateString("en-CA")
                          : "-"
                        }
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="invoices">
            <Card className="mt-4">
              <CardHeader>
                <CardTitle>
                  Company Invoices
                </CardTitle>
              </CardHeader>

              <CardContent>
                {invoices.length === 0 ? (
                  <div className="text-muted-foreground">
                    No invoices found
                  </div>
                ) : (
                  <div className="space-y-3">
                    {invoices.map((inv) => (
                      <div
                        key={inv.id}
                        className="flex items-center justify-between border-b pb-2"
                      >
                        <div>
                          <Link
                            href={`/system/invoices/${inv.number}`}
                            className="font-medium text-blue-600 hover:text-blue-700 hover:underline"
                        >
                           {inv.number || `Invoice #${inv.id}`}
                         </Link>
                          <div className="text-sm text-muted-foreground">
                            {inv.issue_date
                              ? new Date(inv.issue_date).toLocaleDateString("en-US")
                              : "-"
                            }
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge variant="outline">
                            {inv.status}
                          </Badge>

                          <div className="font-medium">
                            {inv.total_amount
                              ? `${inv.total_amount} ${inv.currency || "SAR"}`
                              : "-"
                            }
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="activity">
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  Activity Logs
                </CardTitle>
              </CardHeader>

              <CardContent>
                {activityLogs.length === 0 ? (
                  <div className="text-muted-foreground">
                    No activity yet
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activityLogs.map((log, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between border-b pb-2"
                      >
                        <div>
                          <div className="font-medium">
                            {log.title}
                          </div>

                          <div className="text-sm text-muted-foreground">
                            {log.message}
                          </div>
                        </div>

                        <div className="text-sm text-muted-foreground">
                          {log.created_at
                            ? new Date(log.created_at).toLocaleDateString("en-US")
                            : "-"
                          }
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      <Dialog open={editUserDialogOpen} onOpenChange={setEditUserDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserCog className="h-5 w-5" />
              Edit Company User
            </DialogTitle>
            <DialogDescription>
              Update basic user information without affecting other company data.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <span className="text-sm text-muted-foreground">Username</span>
              <Input
                value={editUserForm.username}
                onChange={(e) =>
                  handleEditUserInputChange("username", e.target.value)
                }
                placeholder="Username"
              />
            </div>

            <div className="space-y-2">
              <span className="text-sm text-muted-foreground">Email</span>
              <Input
                type="email"
                value={editUserForm.email}
                onChange={(e) =>
                  handleEditUserInputChange("email", e.target.value)
                }
                placeholder="Email address"
              />
            </div>

            {selectedUser && (
              <div className="rounded-xl border bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
                Current role:{" "}
                <span className="font-medium text-foreground">
                  {getCompanyUserRoleLabel(selectedUser.role)}
                </span>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditUserDialogOpen(false)}
              disabled={savingUserEdit}
            >
              Cancel
            </Button>

            <Button
              onClick={handleSaveUserEdit}
              disabled={savingUserEdit}
            >
              {savingUserEdit ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={roleDialogOpen} onOpenChange={setRoleDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Change User Role
            </DialogTitle>
            <DialogDescription>
              Update the company permission level for this user.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {selectedUser && (
              <div className="rounded-xl border bg-muted/20 px-4 py-3">
                <div className="font-medium">
                  {displayValue(selectedUser.full_name) !== "-"
                    ? displayValue(selectedUser.full_name)
                    : selectedUser.username}
                </div>
                <div className="text-sm text-muted-foreground">
                  {selectedUser.email}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <span className="text-sm text-muted-foreground">Role</span>
              <Select
                value={selectedRole}
                onValueChange={(value) =>
                  setSelectedRole(value as CompanyUserRole)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>

                <SelectContent>
                  {COMPANY_USER_ROLE_OPTIONS.map((role) => (
                    <SelectItem key={role.value} value={role.value}>
                      {role.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRoleDialogOpen(false)}
              disabled={savingRoleChange}
            >
              Cancel
            </Button>

            <Button
              onClick={handleChangeUserRole}
              disabled={savingRoleChange}
            >
              {savingRoleChange ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Role"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={toggleDialogOpen} onOpenChange={setToggleDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Power className="h-5 w-5" />
              {selectedUser?.is_active ? "Disable User" : "Enable User"}
            </DialogTitle>
            <DialogDescription>
              {selectedUser?.is_active
                ? "This user will lose access until re-enabled."
                : "This user will regain access to the company platform."}
            </DialogDescription>
          </DialogHeader>

          {selectedUser && (
            <div className="rounded-xl border bg-muted/20 px-4 py-3">
              <div className="font-medium">
                {displayValue(selectedUser.full_name) !== "-"
                  ? displayValue(selectedUser.full_name)
                  : selectedUser.username}
              </div>
              <div className="text-sm text-muted-foreground">
                {selectedUser.email}
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setToggleDialogOpen(false)}
              disabled={togglingUserStatus}
            >
              Cancel
            </Button>

            <Button
              variant={selectedUser?.is_active ? "destructive" : "default"}
              onClick={handleToggleUserStatus}
              disabled={togglingUserStatus}
            >
              {togglingUserStatus ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : selectedUser?.is_active ? (
                "Disable User"
              ) : (
                "Enable User"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={resetPasswordDialogOpen} onOpenChange={setResetPasswordDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5" />
              Change Password
            </DialogTitle>
            <DialogDescription>
              Enter the new password for this company user.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {selectedUser && (
              <div className="rounded-xl border bg-muted/20 px-4 py-3">
                <div className="font-medium">
                  {displayValue(selectedUser.full_name) !== "-"
                    ? displayValue(selectedUser.full_name)
                    : selectedUser.username}
                </div>
                <div className="text-sm text-muted-foreground">
                  {selectedUser.email}
                </div>
              </div>
            )}

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
              onClick={() => setResetPasswordDialogOpen(false)}
              disabled={resettingPassword}
            >
              Cancel
            </Button>

            <Button
              onClick={handleResetPassword}
              disabled={resettingPassword}
            >
              {resettingPassword ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Updating...
                </>
              ) : (
                "Update Password"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}