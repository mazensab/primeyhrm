"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import {
  Search,
  Printer,
  FileSpreadsheet,
  Users,
  UserCheck,
  UserX,
  Building2,
  Briefcase,
  RefreshCw,
  Loader2,
  Mail,
  Phone,
  BadgeCheck,
  Eye,
  UserPlus,
  Shield,
  Crown,
  UserCog,
  Check,
  Plus,
  GitBranch,
  Layers3,
  Clock3,
  Pencil,
  Sparkles,
  Filter,
  CalendarDays,
  ChevronRight,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type EmployeeStatus = "ACTIVE" | "INACTIVE" | "ON_LEAVE"
type CompanyRole = "OWNER" | "ADMIN" | "HR" | "MANAGER" | "EMPLOYEE"
type UserStatus = "ACTIVE" | "INACTIVE"
type ScheduleType = "FULL_TIME" | "PART_TIME" | "HOURLY"

interface EmployeeBranch {
  id: number
  name: string
  biotime_code?: string | null
}

interface EmployeeRow {
  id: number
  employee_code: string
  employee_number?: string | null
  full_name: string
  email: string
  phone: string
  avatar?: string | null
  username?: string
  role?: string
  department: string
  job_title: string
  branch: string
  branches: EmployeeBranch[]
  status: EmployeeStatus
  join_date: string
}

interface EmployeeApiRaw {
  id?: number
  full_name?: string
  name?: string
  email?: string
  phone?: string
  avatar?: string | null
  photo_url?: string | null
  username?: string
  role?: string
  department?: string | null
  job_title?: string | null
  branches?: EmployeeBranch[]
  status?: string
  join_date?: string | null
  employee_number?: string | null
  employee_code?: string | null
  user?: {
    username?: string
    email?: string
  }
}

interface EmployeesApiResponse {
  success?: boolean
  results?: EmployeeApiRaw[]
  employees?: EmployeeApiRaw[]
  data?: EmployeeApiRaw[]
}

interface CompanyRoleOption {
  code: CompanyRole
  label: string
  description?: string
}

interface LookupItem {
  id: number
  name: string
  is_active?: boolean
  biotime_code?: string | null
  start_time?: string | null
  end_time?: string | null
  schedule_type?: string | null
  period1_start?: string | null
  period1_end?: string | null
  period2_start?: string | null
  period2_end?: string | null
  weekend_days?: string | null
  weekend_days_ar?: string | null
  target_daily_hours?: string | number | null
  allow_night_overlap?: boolean
  early_arrival_minutes?: number | null
  early_exit_minutes?: number | null
}

interface LookupListResponse {
  status?: string
  success?: boolean
  message?: string
  error?: string
  results?: LookupItem[]
  data?: LookupItem[]
  items?: LookupItem[]
  departments?: LookupItem[]
  branches?: LookupItem[]
  job_titles?: LookupItem[]
  schedules?: LookupItem[]
  work_schedules?: LookupItem[]
}

interface GenericApiResponse {
  success?: boolean
  status?: string
  message?: string
  error?: string
  details?: string
  temporary_password?: string
  employee_id?: number
  user_id?: number
  id?: number
  name?: string
  data?: {
    message?: string
    temporary_password?: string
    employee_id?: number
    user_id?: number
    id?: number
    name?: string
  }
  errors?: Record<string, string>
}

const COMPANY_ROLE_OPTIONS: CompanyRoleOption[] = [
  { code: "ADMIN", label: "Admin" },
  { code: "HR", label: "HR" },
  { code: "MANAGER", label: "Manager" },
  { code: "EMPLOYEE", label: "Employee" },
]

const WEEKEND_DAY_OPTIONS = [
  { value: "fri", label: "Friday / الجمعة" },
  { value: "sat", label: "Saturday / السبت" },
  { value: "sun", label: "Sunday / الأحد" },
  { value: "mon", label: "Monday / الاثنين" },
  { value: "tue", label: "Tuesday / الثلاثاء" },
  { value: "wed", label: "Wednesday / الأربعاء" },
  { value: "thu", label: "Thursday / الخميس" },
]

const FALLBACK_EMPLOYEES: EmployeeRow[] = [
  {
    id: 1,
    employee_code: "EMP-1001",
    employee_number: "EMP-1001",
    full_name: "أحمد محمد",
    email: "ahmed@company.com",
    phone: "+966500000001",
    avatar: "",
    username: "ahmed",
    role: "HR",
    department: "الموارد البشرية",
    job_title: "HR Manager",
    branch: "المدينة",
    branches: [{ id: 1, name: "المدينة" }],
    status: "ACTIVE",
    join_date: "2025-01-10",
  },
  {
    id: 2,
    employee_code: "EMP-1002",
    employee_number: "EMP-1002",
    full_name: "سارة علي",
    email: "sara@company.com",
    phone: "+966500000002",
    avatar: "",
    username: "sara",
    role: "EMPLOYEE",
    department: "الرواتب",
    job_title: "Payroll Specialist",
    branch: "الرياض",
    branches: [{ id: 2, name: "الرياض" }],
    status: "ACTIVE",
    join_date: "2025-02-14",
  },
  {
    id: 3,
    employee_code: "EMP-1003",
    employee_number: "EMP-1003",
    full_name: "خالد حسن",
    email: "khaled@company.com",
    phone: "+966500000003",
    avatar: "",
    username: "khaled",
    role: "MANAGER",
    department: "التشغيل",
    job_title: "Operations Supervisor",
    branch: "جدة",
    branches: [{ id: 3, name: "جدة" }],
    status: "INACTIVE",
    join_date: "2024-11-03",
  },
  {
    id: 4,
    employee_code: "EMP-1004",
    employee_number: "EMP-1004",
    full_name: "ريم عبدالله",
    email: "reem@company.com",
    phone: "+966500000004",
    avatar: "",
    username: "reem",
    role: "EMPLOYEE",
    department: "المبيعات",
    job_title: "Sales Executive",
    branch: "الدمام",
    branches: [{ id: 4, name: "الدمام" }],
    status: "INACTIVE",
    join_date: "2024-08-20",
  },
]

function getInitials(name: string) {
  const parts = name.trim().split(" ").filter(Boolean)
  if (parts.length === 0) return "EM"
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] || ""}${parts[1][0] || ""}`.toUpperCase()
}

function getStatusBadge(status: EmployeeStatus) {
  switch (status) {
    case "ACTIVE":
      return (
        <Badge className="rounded-full border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-emerald-700 shadow-none hover:bg-emerald-500/10 dark:text-emerald-300">
          Active
        </Badge>
      )
    case "INACTIVE":
      return (
        <Badge className="rounded-full border-rose-500/20 bg-rose-500/10 px-2.5 py-1 text-rose-700 shadow-none hover:bg-rose-500/10 dark:text-rose-300">
          Inactive
        </Badge>
      )
    case "ON_LEAVE":
      return (
        <Badge className="rounded-full border-amber-500/20 bg-amber-500/10 px-2.5 py-1 text-amber-700 shadow-none hover:bg-amber-500/10 dark:text-amber-300">
          On Leave
        </Badge>
      )
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

function normalizeStatus(status?: string): EmployeeStatus {
  if (status === "ACTIVE") return "ACTIVE"
  if (status === "INACTIVE") return "INACTIVE"
  if (status === "ON_LEAVE") return "ON_LEAVE"
  return "INACTIVE"
}

function normalizeEmployeeRow(row: EmployeeApiRaw): EmployeeRow {
  const branches = Array.isArray(row.branches) ? row.branches : []
  const branchNames = branches
    .map((item) => item?.name)
    .filter(Boolean)
    .join(", ")

  const employeeNumber = row.employee_number || row.employee_code || ""

  return {
    id: Number(row.id || 0),
    employee_code: employeeNumber || "-",
    employee_number: employeeNumber || null,
    full_name: row.full_name || row.name || row.user?.username || "-",
    email: row.email || row.user?.email || "",
    phone: row.phone || "",
    avatar: row.avatar || row.photo_url || "",
    username: row.username || row.user?.username || "",
    role: row.role || "",
    department: row.department || "-",
    job_title: row.job_title || "-",
    branch: branchNames || "-",
    branches,
    status: normalizeStatus(row.status),
    join_date: row.join_date || "-",
  }
}

function getCookie(name: string): string {
  if (typeof document === "undefined") return ""

  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : ""
}

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function getRoleLabel(role: CompanyRole) {
  switch (role) {
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
      return role
  }
}

function getRoleIcon(role: CompanyRole) {
  switch (role) {
    case "OWNER":
      return <Crown className="h-4 w-4" />
    case "ADMIN":
      return <Shield className="h-4 w-4" />
    case "HR":
      return <Users className="h-4 w-4" />
    case "MANAGER":
      return <Briefcase className="h-4 w-4" />
    case "EMPLOYEE":
      return <UserCog className="h-4 w-4" />
    default:
      return <UserCog className="h-4 w-4" />
  }
}

function getRoleBadgeClass(role: CompanyRole) {
  switch (role) {
    case "OWNER":
      return "border-yellow-500/20 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300"
    case "ADMIN":
      return "border-blue-500/20 bg-blue-500/10 text-blue-700 dark:text-blue-300"
    case "HR":
      return "border-violet-500/20 bg-violet-500/10 text-violet-700 dark:text-violet-300"
    case "MANAGER":
      return "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300"
    case "EMPLOYEE":
      return "border-slate-500/20 bg-slate-500/10 text-slate-700 dark:text-slate-300"
    default:
      return "border-border"
  }
}

function getScheduleTypeLabel(value?: string | null) {
  switch (value) {
    case "FULL_TIME":
      return "دوام فترة واحدة"
    case "PART_TIME":
      return "دوام فترتين"
    case "HOURLY":
      return "دوام بالساعات"
    default:
      return value || "--"
  }
}

function formatHoursLabel(value?: string | number | null) {
  if (value === null || value === undefined || value === "") return "--"
  return String(value)
}

function downloadExcelFile(rows: EmployeeRow[]) {
  try {
    const html = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office"
            xmlns:x="urn:schemas-microsoft-com:office:excel"
            xmlns="http://www.w3.org/TR/REC-html40">
        <head>
          <meta charset="utf-8" />
          <!--[if gte mso 9]>
          <xml>
            <x:ExcelWorkbook>
              <x:ExcelWorksheets>
                <x:ExcelWorksheet>
                  <x:Name>Employees</x:Name>
                  <x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions>
                </x:ExcelWorksheet>
              </x:ExcelWorksheets>
            </x:ExcelWorkbook>
          </xml>
          <![endif]-->
        </head>
        <body>
          <table border="1">
            <tr>
              <th>ID</th>
              <th>Employee Number</th>
              <th>Full Name</th>
              <th>Username</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Role</th>
              <th>Department</th>
              <th>Job Title</th>
              <th>Branches</th>
              <th>Status</th>
              <th>Join Date</th>
            </tr>
            ${rows
              .map(
                (row) => `
                <tr>
                  <td>${row.id}</td>
                  <td>${row.employee_code}</td>
                  <td>${row.full_name}</td>
                  <td>${row.username || ""}</td>
                  <td>${row.email}</td>
                  <td>${row.phone}</td>
                  <td>${row.role || ""}</td>
                  <td>${row.department}</td>
                  <td>${row.job_title}</td>
                  <td>${row.branch}</td>
                  <td>${row.status}</td>
                  <td>${row.join_date}</td>
                </tr>
              `
              )
              .join("")}
          </table>
        </body>
      </html>
    `

    const blob = new Blob([html], {
      type: "application/vnd.ms-excel;charset=utf-8;",
    })

    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = "company-employees.xls"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    toast.success("تم تصدير ملف الموظفين بنجاح")
  } catch (error) {
    console.error("Excel export error:", error)
    toast.error("فشل تصدير ملف Excel")
  }
}

function extractLookupItems(
  data: LookupListResponse,
  key:
    | "departments"
    | "branches"
    | "job_titles"
    | "schedules"
    | "work_schedules"
): LookupItem[] {
  const direct = data[key]
  if (Array.isArray(direct)) return direct
  if (key === "work_schedules" && Array.isArray(data.schedules)) return data.schedules
  if (key === "schedules" && Array.isArray(data.work_schedules)) return data.work_schedules
  if (Array.isArray(data.results)) return data.results
  if (Array.isArray(data.items)) return data.items
  if (Array.isArray(data.data)) return data.data
  return []
}

function formatTimeLabel(value?: string | null) {
  if (!value) return "--"
  return String(value).slice(0, 5)
}

function formatDateLabel(value?: string | null) {
  if (!value || value === "-") return "-"
  return String(value).slice(0, 10)
}

function MasterDataCard({
  title,
  subtitle,
  count,
  icon,
  items,
  loading,
  emptyText,
  onRefresh,
  open,
  onOpenChange,
  createTitle,
  createDescription,
  createPlaceholder,
  createValue,
  onCreateValueChange,
  onCreate,
  creating,
  itemIcon,
}: {
  title: string
  subtitle: string
  count: number
  icon: React.ReactNode
  items: LookupItem[]
  loading: boolean
  emptyText: string
  onRefresh: () => void
  open: boolean
  onOpenChange: (open: boolean) => void
  createTitle: string
  createDescription: string
  createPlaceholder: string
  createValue: string
  onCreateValueChange: (value: string) => void
  onCreate: () => void
  creating: boolean
  itemIcon: React.ReactNode
}) {
  return (
    <Card className="overflow-hidden rounded-[28px] border-border/60 bg-background shadow-sm transition-all hover:shadow-md">
      <CardHeader className="border-b border-border/50 bg-muted/20 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-border/60 bg-background shadow-sm">
              {icon}
            </div>
            <div>
              <CardTitle className="text-base font-semibold">{title}</CardTitle>
              <CardDescription className="mt-1 text-xs sm:text-sm">
                {subtitle}
              </CardDescription>
            </div>
          </div>

          <Badge
            variant="secondary"
            className="rounded-full px-3 py-1 text-xs font-medium"
          >
            {count}
          </Badge>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogTrigger asChild>
              <Button className="h-10 rounded-xl gap-2">
                <Plus className="h-4 w-4" />
                إضافة
              </Button>
            </DialogTrigger>

            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>{createTitle}</DialogTitle>
                <DialogDescription>{createDescription}</DialogDescription>
              </DialogHeader>

              <div className="space-y-2 py-2">
                <label className="text-sm font-medium">الاسم</label>
                <Input
                  value={createValue}
                  onChange={(e) => onCreateValueChange(e.target.value)}
                  placeholder={createPlaceholder}
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                >
                  إلغاء
                </Button>
                <Button type="button" onClick={onCreate} disabled={creating} className="gap-2">
                  {creating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      جاري الحفظ...
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      حفظ
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Button
            variant="outline"
            className="h-10 rounded-xl gap-2"
            onClick={onRefresh}
          >
            <RefreshCw className="h-4 w-4" />
            تحديث
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-4">
        {loading ? (
          <div className="flex min-h-[260px] items-center justify-center text-muted-foreground">
            <div className="flex items-center gap-2 rounded-2xl border bg-muted/30 px-4 py-3">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>جاري التحميل...</span>
            </div>
          </div>
        ) : items.length === 0 ? (
          <div className="flex min-h-[260px] flex-col items-center justify-center rounded-3xl border border-dashed bg-muted/10 px-4 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border bg-background">
              {icon}
            </div>
            <h3 className="text-base font-semibold">{emptyText}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              يمكنك إضافة عنصر جديد مباشرة من هذا القسم
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="max-h-[320px] space-y-2 overflow-y-auto pr-1">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-2xl border border-border/60 bg-background px-3 py-3 shadow-sm transition-all hover:bg-muted/20"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl border bg-muted/20">
                      {itemIcon}
                    </div>

                    <div className="min-w-0">
                      <div className="truncate text-sm font-semibold">
                        {item.name}
                      </div>

                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        <Badge
                          variant="outline"
                          className="rounded-full text-[11px]"
                        >
                          ID: {item.id}
                        </Badge>

                        <Badge
                          className={cn(
                            "rounded-full text-[11px]",
                            item.is_active === false
                              ? "border-rose-500/20 bg-rose-500/10 text-rose-700 hover:bg-rose-500/10 dark:text-rose-300"
                              : "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/10 dark:text-emerald-300"
                          )}
                        >
                          {item.is_active === false ? "Inactive" : "Active"}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  {item.biotime_code ? (
                    <Badge variant="secondary" className="rounded-full">
                      {item.biotime_code}
                    </Badge>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function WorkScheduleSection({
  items,
  loading,
  onRefresh,
  open,
  onOpenChange,
  createName,
  onCreateNameChange,
  createType,
  onCreateTypeChange,
  createWeekendDay,
  onCreateWeekendDayChange,
  createPeriod1Start,
  onCreatePeriod1StartChange,
  createPeriod1End,
  onCreatePeriod1EndChange,
  createPeriod2Start,
  onCreatePeriod2StartChange,
  createPeriod2End,
  onCreatePeriod2EndChange,
  createTargetHours,
  onCreateTargetHoursChange,
  onCreate,
  creating,
  editItem,
  onEditItem,
}: {
  items: LookupItem[]
  loading: boolean
  onRefresh: () => void
  open: boolean
  onOpenChange: (open: boolean) => void
  createName: string
  onCreateNameChange: (value: string) => void
  createType: ScheduleType
  onCreateTypeChange: (value: ScheduleType) => void
  createWeekendDay: string
  onCreateWeekendDayChange: (value: string) => void
  createPeriod1Start: string
  onCreatePeriod1StartChange: (value: string) => void
  createPeriod1End: string
  onCreatePeriod1EndChange: (value: string) => void
  createPeriod2Start: string
  onCreatePeriod2StartChange: (value: string) => void
  createPeriod2End: string
  onCreatePeriod2EndChange: (value: string) => void
  createTargetHours: string
  onCreateTargetHoursChange: (value: string) => void
  onCreate: () => void
  creating: boolean
  editItem: (item: LookupItem) => void
  onEditItem: (item: LookupItem) => void
}) {
  return (
    <Card className="overflow-hidden rounded-[28px] border-border/60 shadow-sm">
      <CardHeader className="border-b border-border/50 bg-muted/20 pb-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border bg-background shadow-sm">
              <Clock3 className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">فترات العمل</CardTitle>
              <CardDescription className="mt-1">
                عرض وإضافة وتعديل جداول الدوام الحالية
              </CardDescription>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="rounded-full px-3 py-1">
              {items.length}
            </Badge>

            <Dialog open={open} onOpenChange={onOpenChange}>
              <DialogTrigger asChild>
                <Button className="h-10 rounded-xl gap-2">
                  <Plus className="h-4 w-4" />
                  إضافة فترة عمل
                </Button>
              </DialogTrigger>

              <DialogContent className="sm:max-w-2xl">
                <DialogHeader>
                  <DialogTitle>إضافة / تعديل فترة عمل</DialogTitle>
                  <DialogDescription>
                    يمكنك إنشاء فترة جديدة أو تعديل فترة موجودة حسب نوع الدوام
                  </DialogDescription>
                </DialogHeader>

                <div className="grid grid-cols-1 gap-4 py-2 md:grid-cols-2">
                  <div className="space-y-2 md:col-span-2">
                    <label className="text-sm font-medium">اسم الفترة</label>
                    <Input
                      value={createName}
                      onChange={(e) => onCreateNameChange(e.target.value)}
                      placeholder="مثال: الفترة الصباحية"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">نوع الفترة</label>
                    <Select
                      value={createType}
                      onValueChange={(value) =>
                        onCreateTypeChange(value as ScheduleType)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="اختر النوع" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="FULL_TIME">دوام فترة واحدة</SelectItem>
                        <SelectItem value="PART_TIME">دوام فترتين</SelectItem>
                        <SelectItem value="HOURLY">دوام بالساعات</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">يوم الإجازة</label>
                    <Select
                      value={createWeekendDay}
                      onValueChange={onCreateWeekendDayChange}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="اختر يوم الإجازة" />
                      </SelectTrigger>
                      <SelectContent>
                        {WEEKEND_DAY_OPTIONS.map((day) => (
                          <SelectItem key={day.value} value={day.value}>
                            {day.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {createType !== "HOURLY" ? (
                    <>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">الفترة الأولى من</label>
                        <Input
                          type="time"
                          value={createPeriod1Start}
                          onChange={(e) => onCreatePeriod1StartChange(e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">الفترة الأولى إلى</label>
                        <Input
                          type="time"
                          value={createPeriod1End}
                          onChange={(e) => onCreatePeriod1EndChange(e.target.value)}
                        />
                      </div>
                    </>
                  ) : null}

                  {createType === "PART_TIME" ? (
                    <>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">الفترة الثانية من</label>
                        <Input
                          type="time"
                          value={createPeriod2Start}
                          onChange={(e) => onCreatePeriod2StartChange(e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">الفترة الثانية إلى</label>
                        <Input
                          type="time"
                          value={createPeriod2End}
                          onChange={(e) => onCreatePeriod2EndChange(e.target.value)}
                        />
                      </div>
                    </>
                  ) : null}

                  {createType === "HOURLY" ? (
                    <div className="space-y-2 md:col-span-2">
                      <label className="text-sm font-medium">عدد الساعات</label>
                      <Input
                        type="number"
                        min="1"
                        step="0.5"
                        value={createTargetHours}
                        onChange={(e) => onCreateTargetHoursChange(e.target.value)}
                        placeholder="مثال: 8"
                      />
                    </div>
                  ) : null}
                </div>

                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => onOpenChange(false)}
                  >
                    إلغاء
                  </Button>

                  <Button type="button" onClick={onCreate} disabled={creating} className="gap-2">
                    {creating ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        جاري الحفظ...
                      </>
                    ) : (
                      <>
                        <Plus className="h-4 w-4" />
                        حفظ الفترة
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Button
              variant="outline"
              className="h-10 rounded-xl gap-2"
              onClick={onRefresh}
            >
              <RefreshCw className="h-4 w-4" />
              تحديث
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4">
        {loading ? (
          <div className="flex min-h-[260px] items-center justify-center text-muted-foreground">
            <div className="flex items-center gap-2 rounded-2xl border bg-muted/30 px-4 py-3">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>جاري تحميل الفترات...</span>
            </div>
          </div>
        ) : items.length === 0 ? (
          <div className="flex min-h-[220px] flex-col items-center justify-center rounded-3xl border border-dashed bg-muted/10 px-4 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border bg-background">
              <Clock3 className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold">لا توجد فترات عمل حالياً</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              يمكنك إضافة فترة عمل جديدة مباشرة من هذا القسم
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-3xl border border-border/60 bg-background">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/30 hover:bg-muted/30">
                  <TableHead>الاسم</TableHead>
                  <TableHead>النوع</TableHead>
                  <TableHead>الفترة الأولى</TableHead>
                  <TableHead>الفترة الثانية</TableHead>
                  <TableHead>الإجازة</TableHead>
                  <TableHead>الساعات</TableHead>
                  <TableHead>الحالة</TableHead>
                  <TableHead className="text-center">إجراء</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.id} className="hover:bg-muted/20">
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-xl border bg-muted/20">
                          <Clock3 className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <span>{item.name}</span>
                      </div>
                    </TableCell>

                    <TableCell>
                      <Badge variant="outline" className="rounded-full">
                        {getScheduleTypeLabel(item.schedule_type)}
                      </Badge>
                    </TableCell>

                    <TableCell>
                      {item.period1_start || item.period1_end
                        ? `${formatTimeLabel(item.period1_start)} - ${formatTimeLabel(item.period1_end)}`
                        : "--"}
                    </TableCell>

                    <TableCell>
                      {item.period2_start || item.period2_end
                        ? `${formatTimeLabel(item.period2_start)} - ${formatTimeLabel(item.period2_end)}`
                        : "--"}
                    </TableCell>

                    <TableCell>{item.weekend_days_ar || item.weekend_days || "--"}</TableCell>
                    <TableCell>{formatHoursLabel(item.target_daily_hours)}</TableCell>

                    <TableCell>
                      <Badge
                        className={cn(
                          "rounded-full",
                          item.is_active === false
                            ? "border-rose-500/20 bg-rose-500/10 text-rose-700 hover:bg-rose-500/10 dark:text-rose-300"
                            : "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/10 dark:text-emerald-300"
                        )}
                      >
                        {item.is_active === false ? "Inactive" : "Active"}
                      </Badge>
                    </TableCell>

                    <TableCell className="text-center">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="rounded-xl gap-2"
                        onClick={() => {
                          editItem(item)
                          onEditItem(item)
                        }}
                      >
                        <Pencil className="h-4 w-4" />
                        عرض/تعديل
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function StatCard({
  title,
  value,
  icon,
  tone = "default",
}: {
  title: string
  value: number
  icon: React.ReactNode
  tone?: "default" | "emerald" | "rose" | "blue"
}) {
  const toneClasses =
    tone === "emerald"
      ? "bg-emerald-500/10 text-emerald-700 border-emerald-500/20 dark:text-emerald-300"
      : tone === "rose"
        ? "bg-rose-500/10 text-rose-700 border-rose-500/20 dark:text-rose-300"
        : tone === "blue"
          ? "bg-blue-500/10 text-blue-700 border-blue-500/20 dark:text-blue-300"
          : "bg-primary/10 text-primary border-primary/20"

  return (
    <Card className="rounded-[28px] border-border/60 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
      <CardContent className="flex items-center justify-between p-5">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <h3 className="text-2xl font-bold tracking-tight">{value}</h3>
        </div>

        <div
          className={cn(
            "flex h-12 w-12 items-center justify-center rounded-2xl border shadow-sm",
            toneClasses
          )}
        >
          {icon}
        </div>
      </CardContent>
    </Card>
  )
}

export default function CompanyEmployeesPage() {
  const [employees, setEmployees] = useState<EmployeeRow[]>([])
  const [loading, setLoading] = useState(true)

  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("ALL")
  const [departmentFilter, setDepartmentFilter] = useState("ALL")
  const [branchFilter, setBranchFilter] = useState("ALL")

  const [roles] = useState<CompanyRoleOption[]>(COMPANY_ROLE_OPTIONS)

  const [openCreateDialog, setOpenCreateDialog] = useState(false)
  const [fullName, setFullName] = useState("")
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [role, setRole] = useState<CompanyRole>("EMPLOYEE")
  const [status, setStatus] = useState<UserStatus>("ACTIVE")
  const [submitting, setSubmitting] = useState(false)

  const [loadingLookups, setLoadingLookups] = useState(false)
  const [departmentOptions, setDepartmentOptions] = useState<LookupItem[]>([])
  const [jobTitleOptions, setJobTitleOptions] = useState<LookupItem[]>([])
  const [branchOptions, setBranchOptions] = useState<LookupItem[]>([])
  const [workScheduleOptions, setWorkScheduleOptions] = useState<LookupItem[]>([])

  const [selectedDepartmentId, setSelectedDepartmentId] = useState("")
  const [selectedJobTitleId, setSelectedJobTitleId] = useState("")
  const [selectedWorkScheduleId, setSelectedWorkScheduleId] = useState("")
  const [selectedBranchIds, setSelectedBranchIds] = useState<number[]>([])

  const [openBranchDialog, setOpenBranchDialog] = useState(false)
  const [openDepartmentDialog, setOpenDepartmentDialog] = useState(false)
  const [openJobTitleDialog, setOpenJobTitleDialog] = useState(false)
  const [openWorkScheduleDialog, setOpenWorkScheduleDialog] = useState(false)

  const [editingScheduleId, setEditingScheduleId] = useState<number | null>(null)

  const [newBranchName, setNewBranchName] = useState("")
  const [newDepartmentName, setNewDepartmentName] = useState("")
  const [newJobTitleName, setNewJobTitleName] = useState("")

  const [newWorkScheduleName, setNewWorkScheduleName] = useState("")
  const [newWorkScheduleType, setNewWorkScheduleType] =
    useState<ScheduleType>("FULL_TIME")
  const [newWorkScheduleWeekendDay, setNewWorkScheduleWeekendDay] = useState("fri")
  const [newWorkSchedulePeriod1Start, setNewWorkSchedulePeriod1Start] = useState("")
  const [newWorkSchedulePeriod1End, setNewWorkSchedulePeriod1End] = useState("")
  const [newWorkSchedulePeriod2Start, setNewWorkSchedulePeriod2Start] = useState("")
  const [newWorkSchedulePeriod2End, setNewWorkSchedulePeriod2End] = useState("")
  const [newWorkScheduleTargetHours, setNewWorkScheduleTargetHours] = useState("")

  const [creatingBranch, setCreatingBranch] = useState(false)
  const [creatingDepartment, setCreatingDepartment] = useState(false)
  const [creatingJobTitle, setCreatingJobTitle] = useState(false)
  const [creatingWorkSchedule, setCreatingWorkSchedule] = useState(false)

  async function fetchEmployees() {
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/company/employees/`, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        cache: "no-store",
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: EmployeesApiResponse = await response.json()
      const rawResults = data.results || data.employees || data.data || []

      if (!Array.isArray(rawResults) || rawResults.length === 0) {
        setEmployees(FALLBACK_EMPLOYEES)
        toast.warning("تم عرض بيانات تجريبية لأن قائمة الموظفين فارغة")
        return
      }

      const normalized = rawResults.map(normalizeEmployeeRow)
      setEmployees(normalized)
    } catch (error) {
      console.error("Employees fetch error:", error)
      setEmployees(FALLBACK_EMPLOYEES)
      toast.warning("تعذر جلب البيانات الحقيقية، تم عرض بيانات تجريبية")
    } finally {
      setLoading(false)
    }
  }

  async function fetchLookups() {
    setLoadingLookups(true)

    try {
      const [departmentsRes, jobTitlesRes, branchesRes, schedulesRes] =
        await Promise.all([
          fetch(`${API_BASE}/api/company/departments/list/`, {
            method: "GET",
            credentials: "include",
            headers: { Accept: "application/json" },
            cache: "no-store",
          }),
          fetch(`${API_BASE}/api/company/job-titles/list/`, {
            method: "GET",
            credentials: "include",
            headers: { Accept: "application/json" },
            cache: "no-store",
          }),
          fetch(`${API_BASE}/api/company/branches/list/`, {
            method: "GET",
            credentials: "include",
            headers: { Accept: "application/json" },
            cache: "no-store",
          }),
          fetch(`${API_BASE}/api/company/work-schedules/`, {
            method: "GET",
            credentials: "include",
            headers: { Accept: "application/json" },
            cache: "no-store",
          }),
        ])

      const [
        departmentsData,
        jobTitlesData,
        branchesData,
        schedulesData,
      ]: LookupListResponse[] = await Promise.all([
        departmentsRes.json(),
        jobTitlesRes.json(),
        branchesRes.json(),
        schedulesRes.json(),
      ])

      setDepartmentOptions(extractLookupItems(departmentsData, "departments"))
      setJobTitleOptions(extractLookupItems(jobTitlesData, "job_titles"))
      setBranchOptions(extractLookupItems(branchesData, "branches"))

      const schedulesResults = extractLookupItems(schedulesData, "schedules")
      const workSchedulesResults = extractLookupItems(
        schedulesData,
        "work_schedules"
      )

      setWorkScheduleOptions(
        schedulesResults.length ? schedulesResults : workSchedulesResults
      )
    } catch (error) {
      console.error("Lookup loading error:", error)
      toast.error("فشل تحميل القوائم المساعدة")
    } finally {
      setLoadingLookups(false)
    }
  }

  function resetCreateForm() {
    setFullName("")
    setUsername("")
    setEmail("")
    setPhone("")
    setRole("EMPLOYEE")
    setStatus("ACTIVE")
    setSelectedDepartmentId("")
    setSelectedJobTitleId("")
    setSelectedWorkScheduleId("")
    setSelectedBranchIds([])
  }

  function resetWorkScheduleForm() {
    setEditingScheduleId(null)
    setNewWorkScheduleName("")
    setNewWorkScheduleType("FULL_TIME")
    setNewWorkScheduleWeekendDay("fri")
    setNewWorkSchedulePeriod1Start("")
    setNewWorkSchedulePeriod1End("")
    setNewWorkSchedulePeriod2Start("")
    setNewWorkSchedulePeriod2End("")
    setNewWorkScheduleTargetHours("")
  }

  function fillWorkScheduleForm(item: LookupItem) {
    setEditingScheduleId(item.id)
    setNewWorkScheduleName(item.name || "")
    setNewWorkScheduleType((item.schedule_type as ScheduleType) || "FULL_TIME")
    setNewWorkScheduleWeekendDay(item.weekend_days || "fri")
    setNewWorkSchedulePeriod1Start(
      formatTimeLabel(item.period1_start || item.start_time || "")
    )
    setNewWorkSchedulePeriod1End(
      formatTimeLabel(item.period1_end || item.end_time || "")
    )
    setNewWorkSchedulePeriod2Start(formatTimeLabel(item.period2_start || ""))
    setNewWorkSchedulePeriod2End(formatTimeLabel(item.period2_end || ""))
    setNewWorkScheduleTargetHours(
      item.target_daily_hours !== null && item.target_daily_hours !== undefined
        ? String(item.target_daily_hours)
        : ""
    )
  }

  function toggleBranch(branchId: number) {
    setSelectedBranchIds((prev) =>
      prev.includes(branchId)
        ? prev.filter((id) => id !== branchId)
        : [...prev, branchId]
    )
  }

  async function handleCreateUserFromEmployees() {
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
      const temporaryPassword = `Primey@${Math.floor(
        100000 + Math.random() * 900000
      )}`

      const createResponse = await fetch(`${API_BASE}/api/company/employees/create/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          employee: {
            full_name: safeFullName,
            mobile_number: safePhone,
            department_id: selectedDepartmentId
              ? Number(selectedDepartmentId)
              : null,
            job_title_id: selectedJobTitleId ? Number(selectedJobTitleId) : null,
            branch_ids: selectedBranchIds,
          },
          user: {
            username: safeUsername,
            email: safeEmail,
            password: temporaryPassword,
            role,
            status,
          },
        }),
      })

      const createData: GenericApiResponse = await createResponse.json()

      const isCreateSuccess =
        createData.success === true ||
        createData.status === "success" ||
        createResponse.ok

      if (!createResponse.ok || !isCreateSuccess) {
        const firstError =
          createData.errors && Object.keys(createData.errors).length > 0
            ? createData.errors[Object.keys(createData.errors)[0]]
            : null

        throw new Error(
          firstError ||
            createData.error ||
            createData.message ||
            "Failed to create company user"
        )
      }

      const createdEmployeeId =
        createData.employee_id || createData.data?.employee_id

      if (createdEmployeeId && selectedWorkScheduleId) {
        const csrfTokenForSchedule = getCookie("csrftoken")

        const scheduleResponse = await fetch(
          `${API_BASE}/api/company/employees/${createdEmployeeId}/assign-work-schedule/`,
          {
            method: "POST",
            credentials: "include",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfTokenForSchedule,
            },
            body: JSON.stringify({
              schedule_id: Number(selectedWorkScheduleId),
            }),
          }
        )

        const scheduleData: GenericApiResponse = await scheduleResponse.json()

        const isScheduleSuccess =
          scheduleData.success === true ||
          scheduleData.status === "success" ||
          scheduleData.status === "ok" ||
          scheduleResponse.ok

        if (!scheduleResponse.ok || !isScheduleSuccess) {
          toast.warning(
            scheduleData.error ||
              scheduleData.message ||
              "تم إنشاء الموظف لكن فشل ربط جدول الدوام"
          )
        }
      }

      toast.success("Company user created successfully", {
        description:
          createData.temporary_password ||
          createData.data?.temporary_password ||
          `Temporary password: ${temporaryPassword}`,
      })

      resetCreateForm()
      setOpenCreateDialog(false)
      await fetchEmployees()
    } catch (error) {
      console.error("Create company user from employees page error:", error)
      toast.error(
        error instanceof Error ? error.message : "Failed to create company user"
      )
    } finally {
      setSubmitting(false)
    }
  }

  async function handleCreateBranch() {
    const safeName = newBranchName.trim()
    if (!safeName) {
      toast.error("اسم الفرع مطلوب")
      return
    }

    setCreatingBranch(true)

    try {
      const csrfToken = getCookie("csrftoken")
      const response = await fetch(`${API_BASE}/api/company/branches/create/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ name: safeName }),
      })

      const data: GenericApiResponse = await response.json()

      const isSuccess =
        response.ok &&
        (data.success === true ||
          data.status === "success" ||
          data.status === "ok")

      if (!isSuccess) {
        throw new Error(data.error || data.message || "فشل إنشاء الفرع")
      }

      toast.success(data.message || "تم إنشاء الفرع بنجاح")
      setNewBranchName("")
      setOpenBranchDialog(false)
      await fetchLookups()
    } catch (error) {
      console.error("Create branch error:", error)
      toast.error(error instanceof Error ? error.message : "فشل إنشاء الفرع")
    } finally {
      setCreatingBranch(false)
    }
  }

  async function handleCreateDepartment() {
    const safeName = newDepartmentName.trim()
    if (!safeName) {
      toast.error("اسم القسم مطلوب")
      return
    }

    setCreatingDepartment(true)

    try {
      const csrfToken = getCookie("csrftoken")
      const response = await fetch(
        `${API_BASE}/api/company/departments/create/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({ name: safeName }),
        }
      )

      const data: GenericApiResponse = await response.json()

      const isSuccess =
        response.ok &&
        (data.success === true ||
          data.status === "success" ||
          data.status === "ok")

      if (!isSuccess) {
        throw new Error(data.error || data.message || "فشل إنشاء القسم")
      }

      toast.success(data.message || "تم إنشاء القسم بنجاح")
      setNewDepartmentName("")
      setOpenDepartmentDialog(false)
      await fetchLookups()
    } catch (error) {
      console.error("Create department error:", error)
      toast.error(error instanceof Error ? error.message : "فشل إنشاء القسم")
    } finally {
      setCreatingDepartment(false)
    }
  }

  async function handleCreateJobTitle() {
    const safeName = newJobTitleName.trim()
    if (!safeName) {
      toast.error("اسم الوظيفة مطلوب")
      return
    }

    setCreatingJobTitle(true)

    try {
      const csrfToken = getCookie("csrftoken")
      const response = await fetch(`${API_BASE}/api/company/job-titles/create/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ name: safeName }),
      })

      const data: GenericApiResponse = await response.json()

      const isSuccess =
        response.ok &&
        (data.success === true ||
          data.status === "success" ||
          data.status === "ok")

      if (!isSuccess) {
        throw new Error(data.error || data.message || "فشل إنشاء الوظيفة")
      }

      toast.success(data.message || "تم إنشاء الوظيفة بنجاح")
      setNewJobTitleName("")
      setOpenJobTitleDialog(false)
      await fetchLookups()
    } catch (error) {
      console.error("Create job title error:", error)
      toast.error(error instanceof Error ? error.message : "فشل إنشاء الوظيفة")
    } finally {
      setCreatingJobTitle(false)
    }
  }

  async function handleCreateWorkSchedule() {
    const safeName = newWorkScheduleName.trim()

    if (!safeName) {
      toast.error("اسم فترة العمل مطلوب")
      return
    }

    if (!newWorkScheduleWeekendDay) {
      toast.error("يوم الإجازة مطلوب")
      return
    }

    if (newWorkScheduleType !== "HOURLY") {
      if (!newWorkSchedulePeriod1Start || !newWorkSchedulePeriod1End) {
        toast.error("أوقات الفترة الأولى مطلوبة")
        return
      }

      if (newWorkScheduleType === "PART_TIME") {
        if (!newWorkSchedulePeriod2Start || !newWorkSchedulePeriod2End) {
          toast.error("أوقات الفترة الثانية مطلوبة")
          return
        }
      }
    }

    if (newWorkScheduleType === "HOURLY" && !newWorkScheduleTargetHours) {
      toast.error("عدد الساعات مطلوب")
      return
    }

    setCreatingWorkSchedule(true)

    try {
      const csrfToken = getCookie("csrftoken")

      const payload: Record<string, unknown> = {
        name: safeName,
        schedule_type: newWorkScheduleType,
        weekend_days: newWorkScheduleWeekendDay,
        allow_night_overlap: false,
        early_arrival_minutes: 0,
        early_exit_minutes: 0,
        is_active: true,
      }

      if (editingScheduleId) {
        payload.id = editingScheduleId
      }

      if (newWorkScheduleType === "FULL_TIME") {
        payload.period1_start = newWorkSchedulePeriod1Start
        payload.period1_end = newWorkSchedulePeriod1End
      }

      if (newWorkScheduleType === "PART_TIME") {
        payload.period1_start = newWorkSchedulePeriod1Start
        payload.period1_end = newWorkSchedulePeriod1End
        payload.period2_start = newWorkSchedulePeriod2Start
        payload.period2_end = newWorkSchedulePeriod2End
      }

      if (newWorkScheduleType === "HOURLY") {
        payload.target_daily_hours = newWorkScheduleTargetHours
      }

      let response = await fetch(`${API_BASE}/api/company/work-schedules/create/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(payload),
      })

      if (response.status === 404) {
        response = await fetch(`${API_BASE}/api/company/work-schedules/`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify(payload),
        })
      }

      const data: GenericApiResponse = await response.json()

      const isSuccess =
        response.ok &&
        (data.success === true ||
          data.status === "success" ||
          data.status === "ok")

      if (!isSuccess) {
        throw new Error(data.error || data.message || "فشل حفظ فترة العمل")
      }

      toast.success(
        data.message ||
          (editingScheduleId
            ? "تم تعديل فترة العمل بنجاح"
            : "تم إنشاء فترة العمل بنجاح")
      )

      resetWorkScheduleForm()
      setOpenWorkScheduleDialog(false)
      await fetchLookups()
    } catch (error) {
      console.error("Create/update work schedule error:", error)
      toast.error(
        error instanceof Error ? error.message : "فشل حفظ فترة العمل"
      )
    } finally {
      setCreatingWorkSchedule(false)
    }
  }

  useEffect(() => {
    fetchEmployees()
    fetchLookups()
  }, [])

  useEffect(() => {
    if (openCreateDialog) {
      fetchLookups()
    }
  }, [openCreateDialog])

  const departments = useMemo(() => {
    return Array.from(
      new Set(employees.map((item) => item.department).filter(Boolean))
    )
  }, [employees])

  const branches = useMemo(() => {
    const allBranchNames = employees.flatMap((item) =>
      item.branches.map((branch) => branch.name).filter(Boolean)
    )
    return Array.from(new Set(allBranchNames))
  }, [employees])

  const selectedBranchNames = useMemo(() => {
    return branchOptions
      .filter((branch) => selectedBranchIds.includes(branch.id))
      .map((branch) => branch.name)
      .join(", ")
  }, [branchOptions, selectedBranchIds])

  const filteredEmployees = useMemo(() => {
    return employees.filter((employee) => {
      const safeSearch = search.toLowerCase()

      const matchesSearch =
        !search ||
        employee.full_name.toLowerCase().includes(safeSearch) ||
        employee.email.toLowerCase().includes(safeSearch) ||
        employee.phone.toLowerCase().includes(safeSearch) ||
        employee.employee_code.toLowerCase().includes(safeSearch) ||
        employee.department.toLowerCase().includes(safeSearch) ||
        employee.job_title.toLowerCase().includes(safeSearch) ||
        (employee.username || "").toLowerCase().includes(safeSearch) ||
        (employee.role || "").toLowerCase().includes(safeSearch) ||
        employee.branch.toLowerCase().includes(safeSearch)

      const matchesStatus =
        statusFilter === "ALL" || employee.status === statusFilter

      const matchesDepartment =
        departmentFilter === "ALL" || employee.department === departmentFilter

      const matchesBranch =
        branchFilter === "ALL" ||
        employee.branches.some((branch) => branch.name === branchFilter)

      return (
        matchesSearch && matchesStatus && matchesDepartment && matchesBranch
      )
    })
  }, [employees, search, statusFilter, departmentFilter, branchFilter])

  const stats = useMemo(() => {
    const total = employees.length
    const active = employees.filter((e) => e.status === "ACTIVE").length
    const inactive = employees.filter((e) => e.status === "INACTIVE").length
    const departmentsCount = departments.length

    return {
      total,
      active,
      inactive,
      departmentsCount,
    }
  }, [employees, departments])

  function handlePrint() {
    window.print()
    toast.success("تم فتح نافذة الطباعة")
  }

  return (
    <div className="space-y-6 p-4 md:p-6">
      <style jsx global>{`
        @media print {
          body * {
            visibility: hidden !important;
          }

          .employees-print-area,
          .employees-print-area * {
            visibility: visible !important;
          }

          .employees-print-area {
            position: absolute !important;
            inset: 0 !important;
            width: 100% !important;
            background: white !important;
            padding: 24px !important;
          }

          .no-print {
            display: none !important;
          }
        }
      `}</style>

      <Card className="no-print overflow-hidden rounded-[32px] border-border/60 shadow-sm">
        <CardContent className="p-0">
          <div className="border-b border-border/50 bg-gradient-to-br from-muted/30 via-background to-background px-6 py-6">
            <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/5 px-3 py-1 text-xs font-medium text-primary">
                  <Sparkles className="h-3.5 w-3.5" />
                  Premium Employees Workspace
                </div>

                <div>
                  <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
                    Employees
                  </h1>
                  <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
                    إدارة وعرض بيانات الموظفين داخل الشركة بشكل احترافي مع دعم
                    الفلاتر والربط مع الأقسام والفروع وجداول الدوام.
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Dialog open={openCreateDialog} onOpenChange={setOpenCreateDialog}>
                  <DialogTrigger asChild>
                    <Button className="h-10 rounded-xl gap-2">
                      <UserPlus className="h-4 w-4" />
                      Add Employee
                    </Button>
                  </DialogTrigger>

                  <DialogContent className="sm:max-w-4xl">
                    <DialogHeader>
                      <DialogTitle>Add Company User</DialogTitle>
                      <DialogDescription>
                        This will create a real company user and assign the selected company role.
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
                              placeholder="Example: ahmed.hr"
                            />
                          </div>

                          <div className="space-y-2">
                            <label className="text-sm font-medium">Email</label>
                            <Input
                              type="email"
                              value={email}
                              onChange={(e) => setEmail(e.target.value)}
                              placeholder="example@company.com"
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
                              onValueChange={(value) => setRole(value as CompanyRole)}
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

                          <div className="space-y-2">
                            <label className="text-sm font-medium">Department</label>
                            <Select
                              value={selectedDepartmentId}
                              onValueChange={setSelectedDepartmentId}
                            >
                              <SelectTrigger>
                                <SelectValue
                                  placeholder={
                                    loadingLookups
                                      ? "Loading departments..."
                                      : "Select department"
                                  }
                                />
                              </SelectTrigger>
                              <SelectContent>
                                {departmentOptions.map((item) => (
                                  <SelectItem key={item.id} value={String(item.id)}>
                                    {item.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>

                          <div className="space-y-2">
                            <label className="text-sm font-medium">Job Title</label>
                            <Select
                              value={selectedJobTitleId}
                              onValueChange={setSelectedJobTitleId}
                            >
                              <SelectTrigger>
                                <SelectValue
                                  placeholder={
                                    loadingLookups
                                      ? "Loading job titles..."
                                      : "Select job title"
                                  }
                                />
                              </SelectTrigger>
                              <SelectContent>
                                {jobTitleOptions.map((item) => (
                                  <SelectItem key={item.id} value={String(item.id)}>
                                    {item.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>

                          <div className="space-y-2 md:col-span-2">
                            <label className="text-sm font-medium">Work Schedule</label>
                            <Select
                              value={selectedWorkScheduleId}
                              onValueChange={setSelectedWorkScheduleId}
                            >
                              <SelectTrigger>
                                <SelectValue
                                  placeholder={
                                    loadingLookups
                                      ? "Loading schedules..."
                                      : "Select work schedule"
                                  }
                                />
                              </SelectTrigger>
                              <SelectContent>
                                {workScheduleOptions.map((item) => (
                                  <SelectItem key={item.id} value={String(item.id)}>
                                    {item.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>

                          <div className="space-y-2 md:col-span-2">
                            <label className="text-sm font-medium">Branches</label>

                            <div className="rounded-2xl border border-border/60 bg-muted/10 p-3">
                              <div className="mb-3 text-sm text-muted-foreground">
                                {selectedBranchNames || "Select one or more branches"}
                              </div>

                              <div className="max-h-44 space-y-2 overflow-y-auto pr-1">
                                {branchOptions.length === 0 ? (
                                  <div className="text-sm text-muted-foreground">
                                    {loadingLookups
                                      ? "Loading branches..."
                                      : "No branches available"}
                                  </div>
                                ) : (
                                  branchOptions.map((branch) => {
                                    const checked = selectedBranchIds.includes(branch.id)

                                    return (
                                      <label
                                        key={branch.id}
                                        className="flex cursor-pointer items-center justify-between rounded-xl border border-border/60 bg-background px-3 py-2 transition hover:bg-muted/30"
                                      >
                                        <div className="flex items-center gap-2">
                                          <input
                                            type="checkbox"
                                            checked={checked}
                                            onChange={() => toggleBranch(branch.id)}
                                            className="h-4 w-4 rounded border-gray-300"
                                          />
                                          <span className="text-sm font-medium">
                                            {branch.name}
                                          </span>
                                        </div>

                                        {checked ? (
                                          <Check className="h-4 w-4 text-emerald-600" />
                                        ) : null}
                                      </label>
                                    )
                                  })
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <Card className="h-fit rounded-3xl border-border/60 bg-muted/10 shadow-none">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm">Role Summary</CardTitle>
                          <CardDescription>Quick preview</CardDescription>
                        </CardHeader>

                        <CardContent className="space-y-4">
                          <Badge className={cn("gap-1 rounded-full", getRoleBadgeClass(role))}>
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

                            <div className="flex items-center justify-between gap-3">
                              <span className="text-muted-foreground">Department</span>
                              <span className="font-medium text-right">
                                {departmentOptions.find(
                                  (item) => String(item.id) === selectedDepartmentId
                                )?.name || "--"}
                              </span>
                            </div>

                            <div className="flex items-center justify-between gap-3">
                              <span className="text-muted-foreground">Job Title</span>
                              <span className="font-medium text-right">
                                {jobTitleOptions.find(
                                  (item) => String(item.id) === selectedJobTitleId
                                )?.name || "--"}
                              </span>
                            </div>

                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">Branches</span>
                              <span className="font-medium">
                                {selectedBranchIds.length}
                              </span>
                            </div>

                            <div className="flex items-center justify-between gap-3">
                              <span className="text-muted-foreground">Schedule</span>
                              <span className="font-medium text-right">
                                {workScheduleOptions.find(
                                  (item) => String(item.id) === selectedWorkScheduleId
                                )?.name || "--"}
                              </span>
                            </div>

                            <div className="flex items-center justify-between">
                              <span className="text-muted-foreground">Binding</span>
                              <span className="font-medium text-emerald-600">Company</span>
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
                          resetCreateForm()
                          setOpenCreateDialog(false)
                        }}
                      >
                        Cancel
                      </Button>

                      <Button
                        type="button"
                        onClick={handleCreateUserFromEmployees}
                        disabled={submitting}
                        className="gap-2"
                      >
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

                <Button variant="outline" onClick={fetchEmployees} className="h-10 rounded-xl gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </Button>

                <Button variant="outline" onClick={handlePrint} className="h-10 rounded-xl gap-2">
                  <Printer className="h-4 w-4" />
                  Print
                </Button>

                <Button
                  onClick={() => downloadExcelFile(filteredEmployees)}
                  className="h-10 rounded-xl gap-2"
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  Export Excel
                </Button>
              </div>
            </div>
          </div>

          <div className="px-6 py-5">
            <div className="mb-4 flex items-center gap-2 text-sm font-medium">
              <Filter className="h-4 w-4 text-muted-foreground" />
              Filters
            </div>

            <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
              <div className="relative lg:col-span-5">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="ابحث بالاسم، اليوزر، البريد، الجوال، الرقم الوظيفي، القسم، الوظيفة..."
                  className="h-11 rounded-xl pl-9"
                />
              </div>

              <div className="lg:col-span-2">
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="h-11 rounded-xl">
                    <SelectValue placeholder="الحالة" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Statuses</SelectItem>
                    <SelectItem value="ACTIVE">Active</SelectItem>
                    <SelectItem value="INACTIVE">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="lg:col-span-2">
                <Select
                  value={departmentFilter}
                  onValueChange={setDepartmentFilter}
                >
                  <SelectTrigger className="h-11 rounded-xl">
                    <SelectValue placeholder="القسم" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Departments</SelectItem>
                    {departments.map((department) => (
                      <SelectItem key={department} value={department}>
                        {department}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="lg:col-span-2">
                <Select value={branchFilter} onValueChange={setBranchFilter}>
                  <SelectTrigger className="h-11 rounded-xl">
                    <SelectValue placeholder="الفرع" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Branches</SelectItem>
                    {branches.map((branch) => (
                      <SelectItem key={branch} value={branch}>
                        {branch}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="lg:col-span-1">
                <Button
                  variant="secondary"
                  className="h-11 w-full rounded-xl"
                  onClick={() => {
                    setSearch("")
                    setStatusFilter("ALL")
                    setDepartmentFilter("ALL")
                    setBranchFilter("ALL")
                    toast.success("تمت إعادة تعيين الفلاتر")
                  }}
                >
                  Reset
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="no-print grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Employees"
          value={stats.total}
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          title="Active"
          value={stats.active}
          icon={<UserCheck className="h-5 w-5" />}
          tone="emerald"
        />
        <StatCard
          title="Inactive"
          value={stats.inactive}
          icon={<UserX className="h-5 w-5" />}
          tone="rose"
        />
        <StatCard
          title="Departments"
          value={stats.departmentsCount}
          icon={<Building2 className="h-5 w-5" />}
          tone="blue"
        />
      </div>

      <Card className="employees-print-area overflow-hidden rounded-[30px] border-border/60 shadow-sm">
        <CardHeader className="border-b border-border/50 bg-muted/20 pb-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <CardTitle className="text-xl font-semibold">Employees Overview</CardTitle>
              <CardDescription className="mt-1">
                إجمالي النتائج الحالية: {filteredEmployees.length}
              </CardDescription>
            </div>

            <div className="no-print flex items-center gap-2">
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                <BadgeCheck className="mr-1 h-3.5 w-3.5" />
                Ready
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-4">
          {loading ? (
            <div className="flex min-h-[320px] items-center justify-center">
              <div className="flex items-center gap-3 rounded-2xl border bg-muted/20 px-4 py-3 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>جاري تحميل الموظفين...</span>
              </div>
            </div>
          ) : filteredEmployees.length === 0 ? (
            <div className="flex min-h-[240px] flex-col items-center justify-center rounded-3xl border border-dashed bg-muted/10 text-center">
              <Users className="mb-3 h-10 w-10 text-muted-foreground" />
              <h3 className="text-lg font-semibold">لا توجد نتائج</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                جرّب تعديل البحث أو الفلاتر لعرض بيانات أخرى
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-3xl border border-border/60">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/30 hover:bg-muted/30">
                    <TableHead>Employee</TableHead>
                    <TableHead>Employee No.</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Job Title</TableHead>
                    <TableHead>Branches</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Join Date</TableHead>
                    <TableHead className="no-print text-center">View</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {filteredEmployees.map((employee) => (
                    <TableRow key={employee.id} className="align-top hover:bg-muted/20">
                      <TableCell>
                        <div className="flex min-w-[300px] items-start gap-3">
                          <Avatar className="h-12 w-12 rounded-2xl border border-border/60 shadow-sm">
                            <AvatarImage
                              src={employee.avatar || ""}
                              alt={employee.full_name}
                            />
                            <AvatarFallback className="rounded-2xl bg-muted font-semibold">
                              {getInitials(employee.full_name)}
                            </AvatarFallback>
                          </Avatar>

                          <div className="space-y-1.5">
                            <div className="font-semibold">
                              {employee.full_name}
                            </div>

                            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                              <span className="inline-flex items-center gap-1">
                                <Mail className="h-3.5 w-3.5" />
                                {employee.email || "-"}
                              </span>

                              <span className="inline-flex items-center gap-1">
                                <Phone className="h-3.5 w-3.5" />
                                {employee.phone || "-"}
                              </span>

                              {employee.role ? (
                                <Badge
                                  variant="outline"
                                  className="rounded-full text-[11px]"
                                >
                                  {employee.role}
                                </Badge>
                              ) : null}
                            </div>
                          </div>
                        </div>
                      </TableCell>

                      <TableCell className="font-medium">
                        {employee.employee_code || "-"}
                      </TableCell>

                      <TableCell>
                        <Badge variant="outline" className="rounded-full">
                          {employee.department || "-"}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        <div className="inline-flex items-center gap-2">
                          <Briefcase className="h-4 w-4 text-muted-foreground" />
                          <span>{employee.job_title || "-"}</span>
                        </div>
                      </TableCell>

                      <TableCell>
                        <div className="max-w-[220px] leading-6">
                          {employee.branch || "-"}
                        </div>
                      </TableCell>

                      <TableCell>{getStatusBadge(employee.status)}</TableCell>

                      <TableCell>
                        <div className="inline-flex items-center gap-2 text-sm">
                          <CalendarDays className="h-4 w-4 text-muted-foreground" />
                          <span>{formatDateLabel(employee.join_date)}</span>
                        </div>
                      </TableCell>

                      <TableCell className="no-print text-center">
                        <Button
                          asChild
                          variant="outline"
                          size="sm"
                          className="rounded-xl gap-2"
                        >
                          <Link href={`/company/employees/${employee.id}`}>
                            <Eye className="h-4 w-4" />
                            View
                          </Link>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="no-print grid grid-cols-1 gap-4 xl:grid-cols-3">
        <MasterDataCard
          title="الفروع"
          subtitle="عرض وإضافة فروع الشركة"
          count={branchOptions.length}
          icon={<GitBranch className="h-5 w-5" />}
          items={branchOptions}
          loading={loadingLookups}
          emptyText="لا توجد فروع حالياً"
          onRefresh={fetchLookups}
          open={openBranchDialog}
          onOpenChange={setOpenBranchDialog}
          createTitle="إضافة فرع جديد"
          createDescription="سيتم إنشاء فرع جديد داخل الشركة الحالية"
          createPlaceholder="مثال: الفرع الرئيسي"
          createValue={newBranchName}
          onCreateValueChange={setNewBranchName}
          onCreate={handleCreateBranch}
          creating={creatingBranch}
          itemIcon={<GitBranch className="h-4 w-4" />}
        />

        <MasterDataCard
          title="الأقسام"
          subtitle="عرض وإضافة أقسام الشركة"
          count={departmentOptions.length}
          icon={<Building2 className="h-5 w-5" />}
          items={departmentOptions}
          loading={loadingLookups}
          emptyText="لا توجد أقسام حالياً"
          onRefresh={fetchLookups}
          open={openDepartmentDialog}
          onOpenChange={setOpenDepartmentDialog}
          createTitle="إضافة قسم جديد"
          createDescription="سيتم إنشاء قسم جديد داخل الشركة الحالية"
          createPlaceholder="مثال: الموارد البشرية"
          createValue={newDepartmentName}
          onCreateValueChange={setNewDepartmentName}
          onCreate={handleCreateDepartment}
          creating={creatingDepartment}
          itemIcon={<Building2 className="h-4 w-4" />}
        />

        <MasterDataCard
          title="الوظائف"
          subtitle="عرض وإضافة المسميات الوظيفية"
          count={jobTitleOptions.length}
          icon={<Layers3 className="h-5 w-5" />}
          items={jobTitleOptions}
          loading={loadingLookups}
          emptyText="لا توجد وظائف حالياً"
          onRefresh={fetchLookups}
          open={openJobTitleDialog}
          onOpenChange={setOpenJobTitleDialog}
          createTitle="إضافة وظيفة جديدة"
          createDescription="سيتم إنشاء مسمى وظيفي جديد داخل الشركة الحالية"
          createPlaceholder="مثال: محاسب أول"
          createValue={newJobTitleName}
          onCreateValueChange={setNewJobTitleName}
          onCreate={handleCreateJobTitle}
          creating={creatingJobTitle}
          itemIcon={<Briefcase className="h-4 w-4" />}
        />
      </div>

      <div className="no-print">
        <WorkScheduleSection
          items={workScheduleOptions}
          loading={loadingLookups}
          onRefresh={fetchLookups}
          open={openWorkScheduleDialog}
          onOpenChange={(open) => {
            setOpenWorkScheduleDialog(open)
            if (!open) resetWorkScheduleForm()
          }}
          createName={newWorkScheduleName}
          onCreateNameChange={setNewWorkScheduleName}
          createType={newWorkScheduleType}
          onCreateTypeChange={setNewWorkScheduleType}
          createWeekendDay={newWorkScheduleWeekendDay}
          onCreateWeekendDayChange={setNewWorkScheduleWeekendDay}
          createPeriod1Start={newWorkSchedulePeriod1Start}
          onCreatePeriod1StartChange={setNewWorkSchedulePeriod1Start}
          createPeriod1End={newWorkSchedulePeriod1End}
          onCreatePeriod1EndChange={setNewWorkSchedulePeriod1End}
          createPeriod2Start={newWorkSchedulePeriod2Start}
          onCreatePeriod2StartChange={setNewWorkSchedulePeriod2Start}
          createPeriod2End={newWorkSchedulePeriod2End}
          onCreatePeriod2EndChange={setNewWorkSchedulePeriod2End}
          createTargetHours={newWorkScheduleTargetHours}
          onCreateTargetHoursChange={setNewWorkScheduleTargetHours}
          onCreate={handleCreateWorkSchedule}
          creating={creatingWorkSchedule}
          editItem={fillWorkScheduleForm}
          onEditItem={() => setOpenWorkScheduleDialog(true)}
        />
      </div>

      <Card className="no-print rounded-[28px] border-dashed border-border/60 bg-muted/10 shadow-none">
        <CardContent className="flex flex-col gap-3 p-5 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <div className="text-sm font-medium">Quick Summary</div>
            <div className="text-sm text-muted-foreground">
              لديك الآن {filteredEmployees.length} نتيجة معروضة، و {workScheduleOptions.length} فترة عمل،
              و {branchOptions.length} فرع، و {departmentOptions.length} قسم.
            </div>
          </div>

          <Link
            href="/company/profile"
            className="inline-flex items-center gap-2 text-sm font-medium text-primary transition hover:opacity-80"
          >
            الانتقال إلى Company Profile
            <ChevronRight className="h-4 w-4" />
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}