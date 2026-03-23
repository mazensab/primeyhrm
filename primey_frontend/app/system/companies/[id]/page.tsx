"use client"

import type { ReactNode } from "react"
import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
  Activity,
  Building2,
  Calendar,
  CheckCircle2,
  Crown,
  FileText,
  KeyRound,
  Landmark,
  Loader2,
  LogIn,
  Mail,
  MapPin,
  MoreHorizontal,
  PencilLine,
  Phone,
  Power,
  Shield,
  UserCog,
  Users,
  XCircle
} from "lucide-react"

/* =========================================================
   Types
========================================================= */

type Locale = "ar" | "en"
type Dir = "rtl" | "ltr"

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

const COMPANY_USER_ROLE_OPTIONS: { value: CompanyUserRole; labelAr: string; labelEn: string }[] = [
  { value: "OWNER", labelAr: "المالك", labelEn: "Owner" },
  { value: "ADMIN", labelAr: "المدير", labelEn: "Admin" },
  { value: "HR", labelAr: "الموارد البشرية", labelEn: "HR" },
  { value: "MANAGER", labelAr: "المدير المباشر", labelEn: "Manager" },
  { value: "EMPLOYEE", labelAr: "الموظف", labelEn: "Employee" }
]

/* =========================================================
   i18n
========================================================= */

const messages = {
  ar: {
    pageSubtitle: "إدارة الشركة واستخدام المنصة",
    active: "نشطة",
    disabled: "معطلة",

    tabs: {
      overview: "نظرة عامة",
      users: "المستخدمون",
      subscription: "الاشتراك",
      invoices: "الفواتير",
      activity: "النشاط"
    },

    companyInfoTitle: "بيانات الشركة",
    companyInfoDesc: "البيانات الرئيسية للشركة، والبيانات الضريبية، والعنوان الوطني.",
    edit: "تعديل",
    cancel: "إلغاء",
    saveChanges: "حفظ التغييرات",
    saving: "جارٍ الحفظ...",

    basicInfo: "المعلومات الأساسية",
    nationalAddress: "العنوان الوطني",
    status: "الحالة",
    metadata: "البيانات التعريفية",
    subscriptionTitle: "الاشتراك",

    fields: {
      companyName: "اسم الشركة",
      owner: "المالك",
      companyEmail: "البريد الإلكتروني للشركة",
      phone: "الهاتف",
      commercialNo: "السجل التجاري",
      vatNo: "الرقم الضريبي",
      buildingNo: "رقم المبنى",
      street: "الشارع",
      district: "الحي",
      city: "المدينة",
      postalCode: "الرمز البريدي",
      shortAddress: "العنوان المختصر",
      plan: "الخطة",
      users: "المستخدمون",
      created: "تاريخ الإنشاء",
      currentStatus: "الحالة الحالية",
      companyId: "رقم الشركة",
      billingCycle: "دورة الفوترة",
      startDate: "تاريخ البداية",
      endDate: "تاريخ النهاية",
      role: "الدور",
      contact: "التواصل",
      user: "المستخدم",
      password: "كلمة المرور"
    },

    usersTitle: "مستخدمو الشركة",
    usersDesc: "إدارة مستخدمي الشركة والصلاحيات وحالة التفعيل.",
    refresh: "تحديث",
    refreshing: "جارٍ التحديث...",
    noUsersFound: "لا يوجد مستخدمون",
    reset: "إعادة تعيين",
    editUser: "تعديل المستخدم",
    changeRole: "تغيير الدور",
    enterAsUser: "الدخول كمستخدم",
    resetPassword: "إعادة تعيين كلمة المرور",
    disableUser: "تعطيل المستخدم",
    enableUser: "تفعيل المستخدم",
    actions: "الإجراءات",

    noSubscriptionFound: "لا يوجد اشتراك",
    subscriptionDetails: "تفاصيل الاشتراك",
    subscriptionExpiresInDays: "ينتهي الاشتراك خلال {days} يوم",
    renewSubscription: "تجديد الاشتراك",

    invoicesTitle: "فواتير الشركة",
    noInvoicesFound: "لا توجد فواتير",

    activityTitle: "سجل النشاط",
    noActivityYet: "لا يوجد نشاط حتى الآن",

    dialog: {
      editUserTitle: "تعديل مستخدم الشركة",
      editUserDesc: "تحديث بيانات المستخدم الأساسية دون التأثير على بيانات الشركة الأخرى.",
      roleTitle: "تغيير دور المستخدم",
      roleDesc: "تحديث مستوى الصلاحية لهذا المستخدم داخل الشركة.",
      toggleDisableTitle: "تعطيل المستخدم",
      toggleEnableTitle: "تفعيل المستخدم",
      toggleDisableDesc: "سيتم منع هذا المستخدم من الدخول حتى إعادة تفعيله.",
      toggleEnableDesc: "سيستعيد هذا المستخدم إمكانية الوصول إلى منصة الشركة.",
      resetPasswordTitle: "تغيير كلمة المرور",
      resetPasswordDesc: "أدخل كلمة المرور الجديدة لهذا المستخدم.",
      currentRole: "الدور الحالي",
      username: "اسم المستخدم",
      email: "البريد الإلكتروني",
      newPassword: "كلمة المرور الجديدة",
      confirmPassword: "تأكيد كلمة المرور",
      selectRole: "اختر الدور",
      saveRole: "حفظ الدور",
      processing: "جارٍ التنفيذ...",
      updating: "جارٍ التحديث..."
    },

    placeholders: {
      companyName: "اسم الشركة",
      companyEmail: "البريد الإلكتروني للشركة",
      phone: "الهاتف",
      commercialNumber: "رقم السجل التجاري",
      vatNumber: "الرقم الضريبي",
      buildingNumber: "رقم المبنى",
      street: "الشارع",
      district: "الحي",
      city: "المدينة",
      postalCode: "الرمز البريدي",
      shortAddress: "العنوان المختصر",
      username: "اسم المستخدم",
      email: "البريد الإلكتروني",
      newPassword: "أدخل كلمة المرور الجديدة",
      confirmPassword: "أكد كلمة المرور"
    },

    companyNotFound: "الشركة غير موجودة",

    toasts: {
      loadUsersFailed: "فشل تحميل مستخدمي الشركة",
      usernameRequired: "اسم المستخدم مطلوب",
      emailRequired: "البريد الإلكتروني مطلوب",
      userUpdateFailed: "فشل تحديث المستخدم",
      userUpdated: "تم تحديث المستخدم بنجاح",
      userUpdateServerError: "خطأ في الخادم أثناء تحديث المستخدم",
      roleChangeFailed: "فشل تغيير دور المستخدم",
      roleUpdated: "تم تحديث دور المستخدم بنجاح",
      roleServerError: "خطأ في الخادم أثناء تغيير الدور",
      statusChangeFailed: "فشل تغيير حالة المستخدم",
      userEnabled: "تم تفعيل المستخدم بنجاح",
      userDisabled: "تم تعطيل المستخدم بنجاح",
      statusServerError: "خطأ في الخادم أثناء تغيير حالة المستخدم",
      enterFailed: "فشل الدخول إلى جلسة الشركة",
      enteredAs: "تم الدخول كمستخدم {username}",
      enterServerError: "خطأ في الخادم أثناء الدخول كمستخدم",
      passwordMin: "يجب أن تكون كلمة المرور 6 أحرف على الأقل",
      passwordsMismatch: "كلمتا المرور غير متطابقتين",
      passwordUpdateFailed: "فشل تحديث كلمة المرور",
      passwordUpdated: "تم تحديث كلمة المرور بنجاح",
      passwordServerError: "خطأ في الخادم أثناء تحديث كلمة المرور",
      companyUpdateFailed: "فشل تحديث بيانات الشركة",
      companyUpdated: "تم تحديث بيانات الشركة بنجاح",
      companyServerError: "خطأ في الخادم أثناء تحديث بيانات الشركة",
      renewFailed: "فشل التجديد",
      renewalInvoiceCreated: "تم إنشاء فاتورة التجديد",
      serverError: "خطأ في الخادم",
      companyFetchFailed: "فشل تحميل بيانات الشركة"
    }
  },
  en: {
    pageSubtitle: "Company administration and platform usage",
    active: "ACTIVE",
    disabled: "DISABLED",

    tabs: {
      overview: "Overview",
      users: "Users",
      subscription: "Subscription",
      invoices: "Invoices",
      activity: "Activity"
    },

    companyInfoTitle: "Company Information",
    companyInfoDesc: "Main company data, tax details, and national address.",
    edit: "Edit",
    cancel: "Cancel",
    saveChanges: "Save Changes",
    saving: "Saving...",

    basicInfo: "Basic Information",
    nationalAddress: "National Address",
    status: "Status",
    metadata: "Metadata",
    subscriptionTitle: "Subscription",

    fields: {
      companyName: "Company Name",
      owner: "Owner",
      companyEmail: "Company Email",
      phone: "Phone",
      commercialNo: "Commercial No.",
      vatNo: "VAT No.",
      buildingNo: "Building No.",
      street: "Street",
      district: "District",
      city: "City",
      postalCode: "Postal Code",
      shortAddress: "Short Address",
      plan: "Plan",
      users: "Users",
      created: "Created",
      currentStatus: "Current Status",
      companyId: "Company ID",
      billingCycle: "Billing Cycle",
      startDate: "Start Date",
      endDate: "End Date",
      role: "Role",
      contact: "Contact",
      user: "User",
      password: "Password"
    },

    usersTitle: "Company Users",
    usersDesc: "Manage company users, permissions, and activation status.",
    refresh: "Refresh",
    refreshing: "Refreshing...",
    noUsersFound: "No users found",
    reset: "Reset",
    editUser: "Edit User",
    changeRole: "Change Role",
    enterAsUser: "Enter as User",
    resetPassword: "Reset Password",
    disableUser: "Disable User",
    enableUser: "Enable User",
    actions: "Actions",

    noSubscriptionFound: "No subscription found",
    subscriptionDetails: "Subscription Details",
    subscriptionExpiresInDays: "Subscription expires in {days} days",
    renewSubscription: "Renew Subscription",

    invoicesTitle: "Company Invoices",
    noInvoicesFound: "No invoices found",

    activityTitle: "Activity Logs",
    noActivityYet: "No activity yet",

    dialog: {
      editUserTitle: "Edit Company User",
      editUserDesc: "Update basic user information without affecting other company data.",
      roleTitle: "Change User Role",
      roleDesc: "Update the company permission level for this user.",
      toggleDisableTitle: "Disable User",
      toggleEnableTitle: "Enable User",
      toggleDisableDesc: "This user will lose access until re-enabled.",
      toggleEnableDesc: "This user will regain access to the company platform.",
      resetPasswordTitle: "Change Password",
      resetPasswordDesc: "Enter the new password for this company user.",
      currentRole: "Current role",
      username: "Username",
      email: "Email",
      newPassword: "New Password",
      confirmPassword: "Confirm Password",
      selectRole: "Select role",
      saveRole: "Save Role",
      processing: "Processing...",
      updating: "Updating..."
    },

    placeholders: {
      companyName: "Company Name",
      companyEmail: "Company Email",
      phone: "Phone",
      commercialNumber: "Commercial Number",
      vatNumber: "VAT Number",
      buildingNumber: "Building Number",
      street: "Street",
      district: "District",
      city: "City",
      postalCode: "Postal Code",
      shortAddress: "Short Address",
      username: "Username",
      email: "Email address",
      newPassword: "Enter new password",
      confirmPassword: "Confirm password"
    },

    companyNotFound: "Company not found",

    toasts: {
      loadUsersFailed: "Failed to load company users",
      usernameRequired: "Username is required",
      emailRequired: "Email is required",
      userUpdateFailed: "Failed to update company user",
      userUpdated: "User updated successfully",
      userUpdateServerError: "Server error while updating company user",
      roleChangeFailed: "Failed to change user role",
      roleUpdated: "User role updated successfully",
      roleServerError: "Server error while changing user role",
      statusChangeFailed: "Failed to change user status",
      userEnabled: "User enabled successfully",
      userDisabled: "User disabled successfully",
      statusServerError: "Server error while changing user status",
      enterFailed: "Failed to enter company session",
      enteredAs: "Entered as {username}",
      enterServerError: "Server error while entering company session",
      passwordMin: "Password must be at least 6 characters",
      passwordsMismatch: "Passwords do not match",
      passwordUpdateFailed: "Failed to update password",
      passwordUpdated: "Password updated successfully",
      passwordServerError: "Server error while updating password",
      companyUpdateFailed: "Failed to update company information",
      companyUpdated: "Company information updated successfully",
      companyServerError: "Server error while updating company information",
      renewFailed: "Renew failed",
      renewalInvoiceCreated: "Renewal invoice created",
      serverError: "Server error",
      companyFetchFailed: "Failed to fetch company"
    }
  }
} as const

/* =========================================================
   Helpers
========================================================= */

function detectLocale(): Locale {
  if (typeof document === "undefined") return "en"
  const lang = (document.documentElement.lang || "").toLowerCase()
  return lang.startsWith("ar") ? "ar" : "en"
}

function detectDir(): Dir {
  if (typeof document === "undefined") return "ltr"
  return document.documentElement.dir === "rtl" ? "rtl" : "ltr"
}

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

function getApiBase() {
  const envBase = process.env.NEXT_PUBLIC_BACKEND_ORIGIN?.trim()
  if (envBase) return envBase.replace(/\/+$/, "")

  if (typeof window === "undefined") return ""

  const { hostname } = window.location
  const isLocal =
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "0.0.0.0"

  if (isLocal) return "http://localhost:8000"

  return ""
}

function apiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  return `${getApiBase()}${normalizedPath}`
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

function formatNumber(value?: number | string | null) {
  if (value === null || value === undefined || value === "") return "-"
  const num = typeof value === "number" ? value : Number(value)
  if (Number.isNaN(num)) return String(value)

  return new Intl.NumberFormat("en-US", {
    numberingSystem: "latn",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(num)
}

function formatDate(value?: string | null) {
  if (!value) return "--"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    numberingSystem: "latn"
  }).format(date)
}

function daysRemaining(date?: string) {
  if (!date) return null

  const end = new Date(date)
  const today = new Date()

  if (Number.isNaN(end.getTime())) return null

  const diff = end.getTime() - today.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function replaceVars(template: string, vars: Record<string, string | number>) {
  return template.replace(/\{(\w+)\}/g, (_, key) => String(vars[key] ?? ""))
}

function normalizeCompanyUserRole(role?: string | null): CompanyUserRole {
  const value = String(role || "").trim().toUpperCase()

  if (value === "OWNER") return "OWNER"
  if (value === "ADMIN") return "ADMIN"
  if (value === "HR") return "HR"
  if (value === "MANAGER") return "MANAGER"

  return "EMPLOYEE"
}

function getCompanyUserRoleLabel(role: string | null | undefined, locale: Locale) {
  const normalized = normalizeCompanyUserRole(role)
  const found = COMPANY_USER_ROLE_OPTIONS.find((item) => item.value === normalized)
  if (!found) return normalized
  return locale === "ar" ? found.labelAr : found.labelEn
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

function OverviewField({
  label,
  value,
  icon,
  alignClass = "text-start"
}: {
  label: string
  value: string
  icon?: ReactNode
  alignClass?: string
}) {
  return (
    <div className={`rounded-xl border bg-muted/20 px-4 py-3 ${alignClass}`}>
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

function getCompanyUserStatusBadge(isActive: boolean, t: typeof messages.en) {
  if (isActive) {
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
      {t.disabled}
    </Badge>
  )
}

/* =========================================================
   Page
========================================================= */

export default function CompanyDetailsPage() {
  const params = useParams()
  const router = useRouter()

  const companyId = useMemo(() => {
    const rawId = params?.id
    return Array.isArray(rawId) ? rawId[0] : String(rawId || "")
  }, [params])

  const [locale, setLocale] = useState<Locale>("en")
  const [dir, setDir] = useState<Dir>("ltr")

  const t = messages[locale]
  const textAlignClass = dir === "rtl" ? "text-right" : "text-left"

  const [company, setCompany] = useState<CompanyDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [users, setUsers] = useState<CompanyUser[]>([])
  const [subscription, setSubscription] = useState<CompanySubscription | null>(null)
  const [invoices, setInvoices] = useState<CompanyInvoice[]>([])
  const [activityLogs, setActivityLogs] = useState<any[]>([])

  const remainingDays = daysRemaining(subscription?.ends_at)

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

  useEffect(() => {
    const syncDocumentLanguage = () => {
      setLocale(detectLocale())
      setDir(detectDir())
    }

    syncDocumentLanguage()

    const observer = new MutationObserver(() => {
      syncDocumentLanguage()
    })

    if (typeof document !== "undefined") {
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["lang", "dir"]
      })
    }

    return () => observer.disconnect()
  }, [])

  const usersCountLabel = useMemo(() => {
    const count = formatNumber(users.length)
    return locale === "ar" ? `${count} مستخدم` : `${count} users`
  }, [users.length, locale])

  /* =========================================================
     Company Users Helpers
  ========================================================= */

  async function loadCompanyUsers() {
    if (!companyId) return

    setUsersLoading(true)

    try {
      const usersRes = await fetch(
        apiUrl(`/api/system/companies/${companyId}/users/`),
        { credentials: "include" }
      )

      if (!usersRes.ok) {
        throw new Error(t.toasts.loadUsersFailed)
      }

      const usersData = await usersRes.json()
      setUsers(Array.isArray(usersData.results) ? usersData.results : [])
    } catch (error) {
      console.error("Company users fetch error:", error)
      toast.error(t.toasts.loadUsersFailed)
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
    if (!selectedUser || !companyId) return

    const username = editUserForm.username.trim()
    const email = editUserForm.email.trim()

    if (!username) {
      toast.error(t.toasts.usernameRequired)
      return
    }

    if (!email) {
      toast.error(t.toasts.emailRequired)
      return
    }

    setSavingUserEdit(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        apiUrl(`/api/system/companies/${companyId}/users/${selectedUser.id}/update/`),
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
        const rawFirstError = data?.errors ? Object.values(data.errors)[0] : null
        const firstError = Array.isArray(rawFirstError) ? rawFirstError[0] : rawFirstError

        toast.error(
          typeof firstError === "string"
            ? firstError
            : data.error || t.toasts.userUpdateFailed
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
      toast.success(data.message || t.toasts.userUpdated)
    } catch (error) {
      console.error("Update company user error:", error)
      toast.error(t.toasts.userUpdateServerError)
    } finally {
      setSavingUserEdit(false)
    }
  }

  async function handleChangeUserRole() {
    if (!selectedUser || !companyId) return

    setSavingRoleChange(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        apiUrl(`/api/system/companies/${companyId}/users/${selectedUser.id}/change-role/`),
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
        toast.error(data.error || t.toasts.roleChangeFailed)
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
      toast.success(data.message || t.toasts.roleUpdated)
    } catch (error) {
      console.error("Change company user role error:", error)
      toast.error(t.toasts.roleServerError)
    } finally {
      setSavingRoleChange(false)
    }
  }

  async function handleToggleUserStatus() {
    if (!selectedUser || !companyId) return

    setTogglingUserStatus(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        apiUrl(`/api/system/companies/${companyId}/users/${selectedUser.id}/toggle-status/`),
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
        toast.error(data.error || t.toasts.statusChangeFailed)
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
          (nextIsActive ? t.toasts.userEnabled : t.toasts.userDisabled)
      )
    } catch (error) {
      console.error("Toggle company user status error:", error)
      toast.error(t.toasts.statusServerError)
    } finally {
      setTogglingUserStatus(false)
    }
  }

  async function handleEnterAsUser(user: CompanyUser) {
    if (!user?.id || !companyId) return

    setEnteringUserId(user.id)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        apiUrl(`/api/system/companies/${companyId}/users/${user.id}/enter/`),
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
        toast.error(data.error || t.toasts.enterFailed)
        return
      }

      toast.success(
        data.message ||
          replaceVars(t.toasts.enteredAs, { username: user.username })
      )

      window.location.href = data.redirect_to || "/company"
    } catch (error) {
      console.error("Enter as company user error:", error)
      toast.error(t.toasts.enterServerError)
    } finally {
      setEnteringUserId(null)
    }
  }

  async function handleResetPassword() {
    if (!resetUserId || !selectedUser || !companyId) return

    if (!newPassword || newPassword.length < 6) {
      toast.error(t.toasts.passwordMin)
      return
    }

    if (newPassword !== confirmPassword) {
      toast.error(t.toasts.passwordsMismatch)
      return
    }

    setResettingPassword(true)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        apiUrl(`/api/system/companies/${companyId}/users/${resetUserId}/reset-password/`),
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
        toast.error(data.error || t.toasts.passwordUpdateFailed)
        return
      }

      toast.success(data.message || t.toasts.passwordUpdated)

      setResetPasswordDialogOpen(false)
      setResetUserId(null)
      setNewPassword("")
      setConfirmPassword("")
      setSelectedUser(null)
    } catch (error) {
      console.error("Reset company user password error:", error)
      toast.error(t.toasts.passwordServerError)
    } finally {
      setResettingPassword(false)
    }
  }

  /* =========================================================
     Fetch Company
  ========================================================= */

  useEffect(() => {
    if (!companyId) return

    let isMounted = true

    async function loadCompany() {
      setLoading(true)

      try {
        const res = await fetch(
          apiUrl(`/api/system/companies/${companyId}/`),
          { credentials: "include" }
        )

        if (!res.ok) {
          throw new Error(t.toasts.companyFetchFailed)
        }

        const data = await res.json()

        if (!isMounted) return

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

        try {
          const subRes = await fetch(
            apiUrl(`/api/system/companies/${companyId}/subscription/`),
            { credentials: "include" }
          )

          if (subRes.ok && isMounted) {
            const subData = await subRes.json()
            setSubscription(subData.subscription || null)
          }
        } catch (error) {
          console.error("Subscription fetch error:", error)
        }

        try {
          const invoicesRes = await fetch(
            apiUrl(`/api/system/companies/${companyId}/invoices/`),
            { credentials: "include" }
          )

          if (invoicesRes.ok && isMounted) {
            const invoicesData = await invoicesRes.json()
            setInvoices(Array.isArray(invoicesData.data?.results) ? invoicesData.data.results : [])
          }
        } catch (error) {
          console.error("Invoices fetch error:", error)
        }

        try {
          const activityRes = await fetch(
            apiUrl(`/api/system/companies/${companyId}/activity/`),
            { credentials: "include" }
          )

          if (activityRes.ok && isMounted) {
            const activityData = await activityRes.json()
            setActivityLogs(Array.isArray(activityData.data?.results) ? activityData.data.results : [])
          }
        } catch (error) {
          console.error("Activity fetch error:", error)
        }

        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadCompany()

    return () => {
      isMounted = false
    }
  }, [companyId, t.toasts.companyFetchFailed])

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
    if (!company || !companyId) return

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
        apiUrl(`/api/system/companies/${companyId}/update/`),
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
        toast.error(data.error || t.toasts.companyUpdateFailed)
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
      toast.success(data.message || t.toasts.companyUpdated)
    } catch (error) {
      console.error("Update company info error:", error)
      toast.error(t.toasts.companyServerError)
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
        apiUrl(`/api/system/subscriptions/${subscription.id}/renew/`),
        {
          method: "POST",
          credentials: "include"
        }
      )

      const data = await res.json()

      if (!res.ok) {
        toast.error(data.error || t.toasts.renewFailed)
        return
      }

      toast.success(t.toasts.renewalInvoiceCreated)
      router.push(`/system/invoices/${data.invoice_id}`)
    } catch (error) {
      console.error("Renew subscription error:", error)
      toast.error(t.toasts.serverError)
    }
  }

  /* =========================================================
     Loading / Empty
  ========================================================= */

  if (loading) {
    return (
      <div dir={dir} className="space-y-4">
        <Skeleton className="h-8 w-60" />
        <Skeleton className="h-56 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  if (!company) {
    return (
      <div dir={dir} className={`text-muted-foreground ${textAlignClass}`}>
        {t.companyNotFound}
      </div>
    )
  }

  /* =========================================================
     UI
  ========================================================= */

  return (
    <>
      <div dir={dir} className="space-y-6">
        <div className="rounded-2xl border bg-background p-4 shadow-sm sm:p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className={`space-y-2 ${textAlignClass}`}>
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
                <Building2 className="h-6 w-6" />
              </div>

              <div>
                <h1 className="text-2xl font-semibold leading-tight">
                  {company.name}
                </h1>

                <p className="mt-1 text-sm text-muted-foreground">
                  {t.pageSubtitle}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Badge
                variant={company.is_active ? "secondary" : "destructive"}
                className="px-3 py-1 text-sm"
              >
                {company.is_active ? t.active : t.disabled}
              </Badge>
            </div>
          </div>
        </div>

        <Tabs defaultValue="overview" className="w-full">
          <div className="overflow-x-auto">
            <TabsList className="inline-flex min-w-full gap-1 sm:grid sm:w-full sm:grid-cols-5 md:max-w-2xl">
              <TabsTrigger value="overview">{t.tabs.overview}</TabsTrigger>
              <TabsTrigger value="users">{t.tabs.users}</TabsTrigger>
              <TabsTrigger value="subscription">{t.tabs.subscription}</TabsTrigger>
              <TabsTrigger value="invoices">{t.tabs.invoices}</TabsTrigger>
              <TabsTrigger value="activity">{t.tabs.activity}</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="overview" className="mt-6 space-y-6">
            <Card className="border shadow-sm">
              <CardHeader className="flex flex-col gap-4 border-b bg-muted/20 pb-5 sm:flex-row sm:items-center sm:justify-between">
                <div className={textAlignClass}>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Building2 className="h-5 w-5" />
                    {t.companyInfoTitle}
                  </CardTitle>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {t.companyInfoDesc}
                  </p>
                </div>

                {!isEditingCompanyInfo ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleStartEditCompanyInfo}
                  >
                    {t.edit}
                  </Button>
                ) : (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCancelEditCompanyInfo}
                      disabled={savingCompanyInfo}
                    >
                      {t.cancel}
                    </Button>

                    <Button
                      size="sm"
                      onClick={handleSaveCompanyInfo}
                      disabled={savingCompanyInfo}
                    >
                      {savingCompanyInfo ? t.saving : t.saveChanges}
                    </Button>
                  </div>
                )}
              </CardHeader>

              <CardContent className="space-y-8 pt-6">
                {!isEditingCompanyInfo ? (
                  <>
                    <div className="space-y-4">
                      <div className={`flex items-center gap-2 text-sm font-semibold text-muted-foreground ${textAlignClass}`}>
                        <FileText className="h-4 w-4" />
                        {t.basicInfo}
                      </div>

                      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                        <OverviewField
                          label={t.fields.companyName}
                          value={displayValue(company.name)}
                          icon={<Building2 className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.owner}
                          value={displayValue(company.owner?.email)}
                          icon={<Users className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.companyEmail}
                          value={displayValue(company.email)}
                          icon={<Mail className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.phone}
                          value={displayValue(company.phone)}
                          icon={<Phone className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.commercialNo}
                          value={displayValue(company.commercial_number)}
                          icon={<FileText className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.vatNo}
                          value={displayValue(company.vat_number)}
                          icon={<Landmark className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className={`flex items-center gap-2 text-sm font-semibold text-muted-foreground ${textAlignClass}`}>
                        <MapPin className="h-4 w-4" />
                        {t.nationalAddress}
                      </div>

                      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                        <OverviewField
                          label={t.fields.buildingNo}
                          value={displayValue(company.national_address?.building_number)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.street}
                          value={displayValue(company.national_address?.street)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.district}
                          value={displayValue(company.national_address?.district)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.city}
                          value={displayValue(company.national_address?.city)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.postalCode}
                          value={displayValue(company.national_address?.postal_code)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                        <OverviewField
                          label={t.fields.shortAddress}
                          value={displayValue(company.national_address?.short_address)}
                          icon={<MapPin className="h-3.5 w-3.5" />}
                          alignClass={textAlignClass}
                        />
                      </div>
                    </div>

                    <div className={`rounded-xl border bg-muted/20 px-4 py-3 ${textAlignClass}`}>
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-sm font-medium text-muted-foreground">
                          {t.status}
                        </span>

                        <Badge
                          variant={company.is_active ? "secondary" : "destructive"}
                        >
                          {company.is_active ? t.active : t.disabled}
                        </Badge>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="space-y-4">
                      <div className={`flex items-center gap-2 text-sm font-semibold text-muted-foreground ${textAlignClass}`}>
                        <FileText className="h-4 w-4" />
                        {t.basicInfo}
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.companyName}
                          </span>
                          <Input
                            value={companyInfoForm.name}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("name", e.target.value)
                            }
                            placeholder={t.placeholders.companyName}
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.owner}
                          </span>
                          <Input
                            value={displayValue(company.owner?.email)}
                            disabled
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.companyEmail}
                          </span>
                          <Input
                            type="email"
                            value={companyInfoForm.email}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("email", e.target.value)
                            }
                            placeholder={t.placeholders.companyEmail}
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.phone}
                          </span>
                          <Input
                            value={companyInfoForm.phone}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("phone", e.target.value)
                            }
                            placeholder={t.placeholders.phone}
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.commercialNo}
                          </span>
                          <Input
                            value={companyInfoForm.commercial_number}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("commercial_number", e.target.value)
                            }
                            placeholder={t.placeholders.commercialNumber}
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.vatNo}
                          </span>
                          <Input
                            value={companyInfoForm.vat_number}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("vat_number", e.target.value)
                            }
                            placeholder={t.placeholders.vatNumber}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className={`flex items-center gap-2 text-sm font-semibold text-muted-foreground ${textAlignClass}`}>
                        <MapPin className="h-4 w-4" />
                        {t.nationalAddress}
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.buildingNo}
                          </span>
                          <Input
                            value={companyInfoForm.building_number}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("building_number", e.target.value)
                            }
                            placeholder={t.placeholders.buildingNumber}
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.street}
                          </span>
                          <Input
                            value={companyInfoForm.street}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("street", e.target.value)
                            }
                            placeholder={t.placeholders.street}
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.district}
                          </span>
                          <Input
                            value={companyInfoForm.district}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("district", e.target.value)
                            }
                            placeholder={t.placeholders.district}
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.city}
                          </span>
                          <Input
                            value={companyInfoForm.city}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("city", e.target.value)
                            }
                            placeholder={t.placeholders.city}
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.postalCode}
                          </span>
                          <Input
                            value={companyInfoForm.postal_code}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("postal_code", e.target.value)
                            }
                            placeholder={t.placeholders.postalCode}
                          />
                        </div>

                        <div className={`space-y-2 ${textAlignClass}`}>
                          <span className="text-sm text-muted-foreground">
                            {t.fields.shortAddress}
                          </span>
                          <Input
                            value={companyInfoForm.short_address}
                            onChange={(e) =>
                              handleCompanyInfoInputChange("short_address", e.target.value)
                            }
                            placeholder={t.placeholders.shortAddress}
                          />
                        </div>
                      </div>
                    </div>

                    <div className={`rounded-xl border bg-muted/20 px-4 py-3 ${textAlignClass}`}>
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-sm font-medium text-muted-foreground">
                          {t.status}
                        </span>

                        <Badge
                          variant={company.is_active ? "secondary" : "destructive"}
                        >
                          {company.is_active ? t.active : t.disabled}
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
                  {t.subscriptionTitle}
                </CardTitle>
              </CardHeader>

              <CardContent className="pt-6">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  <OverviewField
                    label={t.fields.plan}
                    value={company.subscription?.plan || "-"}
                    icon={<Crown className="h-3.5 w-3.5" />}
                    alignClass={textAlignClass}
                  />
                  <OverviewField
                    label={t.fields.users}
                    value={formatNumber(company.users_count)}
                    icon={<Users className="h-3.5 w-3.5" />}
                    alignClass={textAlignClass}
                  />
                  <OverviewField
                    label={t.status}
                    value={company.subscription?.status || "-"}
                    icon={<Calendar className="h-3.5 w-3.5" />}
                    alignClass={textAlignClass}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="border shadow-sm">
              <CardHeader className="border-b bg-muted/20">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Calendar className="h-5 w-5" />
                  {t.metadata}
                </CardTitle>
              </CardHeader>

              <CardContent className="pt-6">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  <OverviewField
                    label={t.fields.companyId}
                    value={formatNumber(company.id)}
                    icon={<Building2 className="h-3.5 w-3.5" />}
                    alignClass={textAlignClass}
                  />
                  <OverviewField
                    label={t.fields.created}
                    value={formatDate(company.created_at)}
                    icon={<Calendar className="h-3.5 w-3.5" />}
                    alignClass={textAlignClass}
                  />
                  <OverviewField
                    label={t.fields.currentStatus}
                    value={company.is_active ? t.active : t.disabled}
                    icon={<Activity className="h-3.5 w-3.5" />}
                    alignClass={textAlignClass}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="users">
            <Card className="mt-4 border shadow-sm">
              <CardHeader className="border-b bg-muted/20">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className={textAlignClass}>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Users className="h-5 w-5" />
                      {t.usersTitle}
                    </CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {t.usersDesc}
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
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>{t.refreshing}</span>
                        </>
                      ) : (
                        t.refresh
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
                          <TableHead className="min-w-[240px]">{t.fields.user}</TableHead>
                          <TableHead className="min-w-[220px]">{t.fields.contact}</TableHead>
                          <TableHead className="min-w-[140px]">{t.fields.role}</TableHead>
                          <TableHead className="min-w-[120px]">{t.status}</TableHead>
                          <TableHead className="min-w-[120px]">{t.fields.created}</TableHead>
                          <TableHead className="min-w-[120px]">{t.fields.password}</TableHead>
                          <TableHead className="min-w-[100px]">{t.edit}</TableHead>
                          <TableHead className="min-w-[70px]"></TableHead>
                        </TableRow>
                      </TableHeader>

                      <TableBody>
                        {users.length === 0 && (
                          <TableRow>
                            <TableCell colSpan={8} className="text-center text-muted-foreground">
                              {t.noUsersFound}
                            </TableCell>
                          </TableRow>
                        )}

                        {users.map((user) => {
                          const preferredName = displayValue(user.full_name)
                          const displayName = preferredName !== "-" ? preferredName : user.username

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
                                  {getCompanyUserRoleLabel(user.role, locale)}
                                </Badge>
                              </TableCell>

                              <TableCell>
                                {getCompanyUserStatusBadge(user.is_active, t)}
                              </TableCell>

                              <TableCell>{formatDate(user.created_at)}</TableCell>

                              <TableCell>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openResetPasswordDialog(user)}
                                  disabled={resettingPassword && resetUserId === user.id}
                                >
                                  {resettingPassword && resetUserId === user.id ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <KeyRound className="h-4 w-4" />
                                  )}
                                  <span>{t.reset}</span>
                                </Button>
                              </TableCell>

                              <TableCell>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openEditUserDialog(user)}
                                >
                                  <PencilLine className="h-4 w-4" />
                                  <span>{t.edit}</span>
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
                                    <DropdownMenuLabel>{t.actions}</DropdownMenuLabel>
                                    <DropdownMenuSeparator />

                                    <DropdownMenuItem onClick={() => openEditUserDialog(user)}>
                                      <PencilLine className="h-4 w-4" />
                                      {t.editUser}
                                    </DropdownMenuItem>

                                    <DropdownMenuItem onClick={() => openRoleDialog(user)}>
                                      <Shield className="h-4 w-4" />
                                      {t.changeRole}
                                    </DropdownMenuItem>

                                    <DropdownMenuItem
                                      onClick={() => handleEnterAsUser(user)}
                                      disabled={!user.is_active || enteringUserId === user.id}
                                    >
                                      {enteringUserId === user.id ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                      ) : (
                                        <LogIn className="h-4 w-4" />
                                      )}
                                      {t.enterAsUser}
                                    </DropdownMenuItem>

                                    <DropdownMenuItem onClick={() => openResetPasswordDialog(user)}>
                                      <KeyRound className="h-4 w-4" />
                                      {t.resetPassword}
                                    </DropdownMenuItem>

                                    <DropdownMenuSeparator />

                                    <DropdownMenuItem onClick={() => openToggleDialog(user)}>
                                      <Power className="h-4 w-4" />
                                      {user.is_active ? t.disableUser : t.enableUser}
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
            <Card className="mt-4 border shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Crown className="h-4 w-4" />
                  {t.subscriptionDetails}
                </CardTitle>
              </CardHeader>

              <CardContent>
                {!subscription ? (
                  <div className={`text-muted-foreground ${textAlignClass}`}>
                    {t.noSubscriptionFound}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">{t.fields.plan}</span>
                      <span className="font-medium">{subscription.plan || "-"}</span>
                    </div>

                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">{t.status}</span>
                      <Badge variant="secondary">{subscription.status || "-"}</Badge>
                    </div>

                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">{t.fields.billingCycle}</span>
                      <span className="font-medium">
                        {subscription.billing_cycle || "-"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">{t.fields.startDate}</span>
                      <span className="font-medium">
                        {formatDate(subscription.started_at)}
                      </span>
                    </div>

                    {remainingDays !== null && remainingDays <= 10 && (
                      <div className="text-sm font-medium text-amber-600">
                        {replaceVars(t.subscriptionExpiresInDays, {
                          days: formatNumber(remainingDays)
                        })}
                      </div>
                    )}

                    {remainingDays !== null && remainingDays <= 10 && (
                      <div className="pt-2">
                        <Button onClick={handleRenew}>
                          {t.renewSubscription}
                        </Button>
                      </div>
                    )}

                    <div className="flex items-center justify-between gap-4">
                      <span className="text-muted-foreground">{t.fields.endDate}</span>
                      <span className="font-medium">
                        {formatDate(subscription.ends_at)}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="invoices">
            <Card className="mt-4 border shadow-sm">
              <CardHeader>
                <CardTitle>{t.invoicesTitle}</CardTitle>
              </CardHeader>

              <CardContent>
                {invoices.length === 0 ? (
                  <div className={`text-muted-foreground ${textAlignClass}`}>
                    {t.noInvoicesFound}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {invoices.map((inv) => (
                      <div
                        key={inv.id}
                        className="flex flex-col gap-3 border-b pb-3 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className={`min-w-0 ${textAlignClass}`}>
                          <Link
                            href={`/system/invoices/${inv.number}`}
                            className="font-medium text-primary hover:underline"
                          >
                            {inv.number || `Invoice #${formatNumber(inv.id)}`}
                          </Link>

                          <div className="text-sm text-muted-foreground">
                            {formatDate(inv.issue_date)}
                          </div>
                        </div>

                        <div className="flex items-center gap-3 self-start sm:self-auto">
                          <Badge variant="outline">
                            {inv.status}
                          </Badge>

                          <div className="font-medium">
                            {inv.total_amount !== null && inv.total_amount !== undefined
                              ? `${formatNumber(inv.total_amount)} ${inv.currency || "SAR"}`
                              : "-"}
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
            <Card className="mt-4 border shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  {t.activityTitle}
                </CardTitle>
              </CardHeader>

              <CardContent>
                {activityLogs.length === 0 ? (
                  <div className={`text-muted-foreground ${textAlignClass}`}>
                    {t.noActivityYet}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activityLogs.map((log, i) => (
                      <div
                        key={log.id || `${log.created_at || "log"}-${i}`}
                        className="flex flex-col gap-3 border-b pb-3 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className={`min-w-0 ${textAlignClass}`}>
                          <div className="font-medium">
                            {displayValue(log.title)}
                          </div>

                          <div className="text-sm text-muted-foreground">
                            {displayValue(log.message)}
                          </div>
                        </div>

                        <div className="text-sm text-muted-foreground">
                          {formatDate(log.created_at)}
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
        <DialogContent dir={dir} className="sm:max-w-lg">
          <DialogHeader className={textAlignClass}>
            <DialogTitle className="flex items-center gap-2">
              <UserCog className="h-5 w-5" />
              {t.dialog.editUserTitle}
            </DialogTitle>
            <DialogDescription>
              {t.dialog.editUserDesc}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className={`space-y-2 ${textAlignClass}`}>
              <span className="text-sm text-muted-foreground">
                {t.dialog.username}
              </span>
              <Input
                value={editUserForm.username}
                onChange={(e) =>
                  handleEditUserInputChange("username", e.target.value)
                }
                placeholder={t.placeholders.username}
              />
            </div>

            <div className={`space-y-2 ${textAlignClass}`}>
              <span className="text-sm text-muted-foreground">
                {t.dialog.email}
              </span>
              <Input
                type="email"
                value={editUserForm.email}
                onChange={(e) =>
                  handleEditUserInputChange("email", e.target.value)
                }
                placeholder={t.placeholders.email}
              />
            </div>

            {selectedUser && (
              <div className={`rounded-xl border bg-muted/20 px-4 py-3 text-sm text-muted-foreground ${textAlignClass}`}>
                {t.dialog.currentRole}:{" "}
                <span className="font-medium text-foreground">
                  {getCompanyUserRoleLabel(selectedUser.role, locale)}
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
              {t.cancel}
            </Button>

            <Button
              onClick={handleSaveUserEdit}
              disabled={savingUserEdit}
            >
              {savingUserEdit ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t.saving}
                </>
              ) : (
                t.saveChanges
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={roleDialogOpen} onOpenChange={setRoleDialogOpen}>
        <DialogContent dir={dir} className="sm:max-w-lg">
          <DialogHeader className={textAlignClass}>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              {t.dialog.roleTitle}
            </DialogTitle>
            <DialogDescription>
              {t.dialog.roleDesc}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {selectedUser && (
              <div className={`rounded-xl border bg-muted/20 px-4 py-3 ${textAlignClass}`}>
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

            <div className={`space-y-2 ${textAlignClass}`}>
              <span className="text-sm text-muted-foreground">
                {t.fields.role}
              </span>
              <Select
                value={selectedRole}
                onValueChange={(value) =>
                  setSelectedRole(value as CompanyUserRole)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder={t.dialog.selectRole} />
                </SelectTrigger>

                <SelectContent>
                  {COMPANY_USER_ROLE_OPTIONS.map((role) => (
                    <SelectItem key={role.value} value={role.value}>
                      {locale === "ar" ? role.labelAr : role.labelEn}
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
              {t.cancel}
            </Button>

            <Button
              onClick={handleChangeUserRole}
              disabled={savingRoleChange}
            >
              {savingRoleChange ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t.saving}
                </>
              ) : (
                t.dialog.saveRole
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={toggleDialogOpen} onOpenChange={setToggleDialogOpen}>
        <DialogContent dir={dir} className="sm:max-w-lg">
          <DialogHeader className={textAlignClass}>
            <DialogTitle className="flex items-center gap-2">
              <Power className="h-5 w-5" />
              {selectedUser?.is_active ? t.dialog.toggleDisableTitle : t.dialog.toggleEnableTitle}
            </DialogTitle>
            <DialogDescription>
              {selectedUser?.is_active ? t.dialog.toggleDisableDesc : t.dialog.toggleEnableDesc}
            </DialogDescription>
          </DialogHeader>

          {selectedUser && (
            <div className={`rounded-xl border bg-muted/20 px-4 py-3 ${textAlignClass}`}>
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
              {t.cancel}
            </Button>

            <Button
              variant={selectedUser?.is_active ? "destructive" : "default"}
              onClick={handleToggleUserStatus}
              disabled={togglingUserStatus}
            >
              {togglingUserStatus ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t.dialog.processing}
                </>
              ) : selectedUser?.is_active ? (
                t.disableUser
              ) : (
                t.enableUser
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={resetPasswordDialogOpen} onOpenChange={setResetPasswordDialogOpen}>
        <DialogContent dir={dir} className="sm:max-w-md">
          <DialogHeader className={textAlignClass}>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5" />
              {t.dialog.resetPasswordTitle}
            </DialogTitle>
            <DialogDescription>
              {t.dialog.resetPasswordDesc}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {selectedUser && (
              <div className={`rounded-xl border bg-muted/20 px-4 py-3 ${textAlignClass}`}>
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

            <div className={`space-y-2 ${textAlignClass}`}>
              <label className="text-sm font-medium">
                {t.dialog.newPassword}
              </label>

              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder={t.placeholders.newPassword}
              />
            </div>

            <div className={`space-y-2 ${textAlignClass}`}>
              <label className="text-sm font-medium">
                {t.dialog.confirmPassword}
              </label>

              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder={t.placeholders.confirmPassword}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setResetPasswordDialogOpen(false)}
              disabled={resettingPassword}
            >
              {t.cancel}
            </Button>

            <Button
              onClick={handleResetPassword}
              disabled={resettingPassword}
            >
              {resettingPassword ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t.dialog.updating}
                </>
              ) : (
                t.resetPassword
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}