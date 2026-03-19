"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileSpreadsheet,
  Loader2,
  Plus,
  Printer,
  RefreshCw,
  Search,
  TimerReset,
  XCircle,
  Briefcase,
  Sparkles,
  ClipboardList,
  ShieldAlert,
  CalendarRange,
} from "lucide-react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type LeaveRequestRow = {
  id: number
  employee_name: string
  employee_id?: number
  type: string
  from_date: string
  to_date: string
  status: string
}

type LeaveBalanceRow = {
  leave_type: string
  balance: number
}

type LeaveTypeOption = {
  id: number
  name: string
}

type EmployeeOption = {
  id: number
  full_name: string
  avatar?: string | null
  email?: string
  phone?: string
}

type AnnualPolicy = {
  annual_days?: number
  accrual_enabled?: boolean
  carry_forward_enabled?: boolean
  max_carry_forward_days?: number
  [key: string]: unknown
}

type CreateFormState = {
  employee_id: string
  leave_type_id: string
  start_date: string
  end_date: string
  reason: string
}

const INITIAL_FORM: CreateFormState = {
  employee_id: "",
  leave_type_id: "",
  start_date: "",
  end_date: "",
  reason: "",
}

function getCookie(name: string): string {
  if (typeof document === "undefined") return ""
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || ""
  }
  return ""
}

function formatDate(value?: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }
  return date.toLocaleDateString("en-CA")
}

function getInitials(name?: string | null): string {
  const safeName = String(name || "").trim()
  if (!safeName) return "EM"

  const parts = safeName.split(" ").filter(Boolean)
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase()
  }

  return `${parts[0][0] || ""}${parts[1][0] || ""}`.toUpperCase()
}

function getStatusLabel(status?: string): string {
  const normalized = String(status || "").toLowerCase()

  if (normalized === "approved") return "معتمد"
  if (normalized === "rejected") return "مرفوض"
  if (normalized === "pending") return "قيد الانتظار"
  if (normalized === "cancelled") return "ملغي"

  return status || "غير معروف"
}

function getStatusBadgeClass(status?: string): string {
  const normalized = String(status || "").toLowerCase()

  if (normalized === "approved") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700"
  }
  if (normalized === "rejected") {
    return "border-rose-200 bg-rose-50 text-rose-700"
  }
  if (normalized === "pending") {
    return "border-amber-200 bg-amber-50 text-amber-700"
  }
  if (normalized === "cancelled") {
    return "border-slate-300 bg-slate-100 text-slate-700"
  }

  return "border-slate-200 bg-slate-50 text-slate-700"
}

function getStatusCount(
  rows: LeaveRequestRow[],
  status: "approved" | "rejected" | "pending" | "cancelled"
) {
  return rows.filter(
    (item) => String(item.status || "").toLowerCase() === status
  ).length
}

function buildPrintableHtml(rows: LeaveRequestRow[]) {
  const tableRows = rows
    .map(
      (item, index) => `
        <tr>
          <td>${index + 1}</td>
          <td>#${item.id}</td>
          <td>${item.employee_name}</td>
          <td>${item.type}</td>
          <td>${formatDate(item.from_date)}</td>
          <td>${formatDate(item.to_date)}</td>
          <td>${getStatusLabel(item.status)}</td>
        </tr>
      `
    )
    .join("")

  return `
    <html dir="rtl" lang="ar">
      <head>
        <title>طلبات الإجازات</title>
        <meta charset="utf-8" />
        <style>
          * { box-sizing: border-box; }
          body {
            font-family: Arial, Tahoma, sans-serif;
            margin: 24px;
            color: #0f172a;
            background: #ffffff;
          }
          .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid #e2e8f0;
          }
          .title {
            margin: 0;
            font-size: 28px;
            font-weight: 800;
          }
          .subtitle {
            margin: 6px 0 0 0;
            color: #475569;
            font-size: 13px;
          }
          .meta {
            text-align: left;
            color: #475569;
            font-size: 12px;
          }
          .summary {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 20px;
          }
          .summary-card {
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 14px;
            background: #f8fafc;
          }
          .summary-label {
            font-size: 12px;
            color: #64748b;
            margin-bottom: 8px;
          }
          .summary-value {
            font-size: 24px;
            font-weight: 800;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #e2e8f0;
          }
          thead th {
            background: #f8fafc;
            font-size: 12px;
            padding: 12px 10px;
            border-bottom: 1px solid #e2e8f0;
            border-left: 1px solid #e2e8f0;
            text-align: right;
          }
          tbody td {
            font-size: 12px;
            padding: 12px 10px;
            border-bottom: 1px solid #e2e8f0;
            border-left: 1px solid #e2e8f0;
          }
          tbody tr:nth-child(even) {
            background: #fcfcfd;
          }
          .empty {
            margin-top: 20px;
            padding: 20px;
            text-align: center;
            border: 1px dashed #cbd5e1;
            border-radius: 14px;
            color: #64748b;
            background: #f8fafc;
          }
          @page {
            size: A4 portrait;
            margin: 14mm;
          }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <h1 class="title">طلبات الإجازات</h1>
            <p class="subtitle">تقرير قابل للطباعة من صفحة إدارة الإجازات</p>
          </div>
          <div class="meta">
            <div>تاريخ الطباعة: ${new Date().toLocaleDateString("en-CA")}</div>
            <div>الوقت: ${new Date().toLocaleTimeString("en-GB")}</div>
          </div>
        </div>

        <div class="summary">
          <div class="summary-card">
            <div class="summary-label">إجمالي الطلبات</div>
            <div class="summary-value">${rows.length}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">معتمدة</div>
            <div class="summary-value">${getStatusCount(rows, "approved")}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">بانتظار الاعتماد</div>
            <div class="summary-value">${getStatusCount(rows, "pending")}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">مرفوضة</div>
            <div class="summary-value">${getStatusCount(rows, "rejected")}</div>
          </div>
        </div>

        ${
          rows.length === 0
            ? `<div class="empty">لا توجد بيانات لطباعة قائمة الطلبات الحالية.</div>`
            : `
              <table>
                <thead>
                  <tr>
                    <th>م</th>
                    <th>رقم الطلب</th>
                    <th>الموظف</th>
                    <th>نوع الإجازة</th>
                    <th>من</th>
                    <th>إلى</th>
                    <th>الحالة</th>
                  </tr>
                </thead>
                <tbody>
                  ${tableRows}
                </tbody>
              </table>
            `
        }
      </body>
    </html>
  `
}

async function safeJson(response: Response) {
  const text = await response.text()
  try {
    return text ? JSON.parse(text) : {}
  } catch {
    return {}
  }
}

async function apiRequest(
  endpoint: string,
  options?: RequestInit
): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    credentials: "include",
    ...options,
    headers: {
      Accept: "application/json",
      ...(options?.headers || {}),
    },
  })

  const data = await safeJson(response)

  if (!response.ok) {
    const message =
      (typeof data?.error === "string" && data.error) ||
      (typeof data?.message === "string" && data.message) ||
      "تعذر تنفيذ الطلب."
    throw new Error(message)
  }

  return data
}

async function apiRequestWithFallback(
  endpoints: string[],
  options?: RequestInit
): Promise<Record<string, unknown>> {
  let lastError: unknown = null

  for (const endpoint of endpoints) {
    try {
      return await apiRequest(endpoint, options)
    } catch (error) {
      lastError = error
    }
  }

  throw lastError || new Error("تعذر الوصول إلى المسار المطلوب.")
}

function normalizeRequests(payload: Record<string, unknown>): LeaveRequestRow[] {
  const list = Array.isArray(payload.requests) ? payload.requests : []

  return list.map((item) => {
    const row = item as Record<string, unknown>
    return {
      id: Number(row.id || 0),
      employee_name: String(row.employee_name || "—"),
      employee_id: row.employee_id ? Number(row.employee_id) : undefined,
      type: String(row.type || "—"),
      from_date: String(row.from_date || ""),
      to_date: String(row.to_date || ""),
      status: String(row.status || "pending"),
    }
  })
}

function normalizeBalances(payload: Record<string, unknown>): LeaveBalanceRow[] {
  const list = Array.isArray(payload.balances) ? payload.balances : []

  return list.map((item) => {
    const row = item as Record<string, unknown>
    return {
      leave_type: String(row.leave_type || "—"),
      balance: Number(row.balance || 0),
    }
  })
}

function normalizeLeaveTypes(
  payload: Record<string, unknown>
): LeaveTypeOption[] {
  const list = Array.isArray(payload.types) ? payload.types : []

  return list.map((item) => {
    const row = item as Record<string, unknown>
    return {
      id: Number(row.id || 0),
      name: String(row.name || "—"),
    }
  })
}

function normalizeEmployees(
  payload: Record<string, unknown>
): EmployeeOption[] {
  const list = Array.isArray(payload.employees) ? payload.employees : []

  return list
    .map((item) => {
      const row = item as Record<string, unknown>
      const user =
        row.user && typeof row.user === "object"
          ? (row.user as Record<string, unknown>)
          : null

      return {
        id: Number(row.id || 0),
        full_name: String(
          row.full_name || row.name || row.username || `Employee #${row.id || ""}`
        ),
        avatar: String(row.avatar || row.photo_url || "") || "",
        email: String(row.email || user?.email || "") || "",
        phone: String(row.phone || row.mobile_number || "") || "",
      }
    })
    .filter((item) => item.id > 0)
}

export default function CompanyLeavesPage() {
  const [requests, setRequests] = useState<LeaveRequestRow[]>([])
  const [balances, setBalances] = useState<LeaveBalanceRow[]>([])
  const [leaveTypes, setLeaveTypes] = useState<LeaveTypeOption[]>([])
  const [employees, setEmployees] = useState<EmployeeOption[]>([])
  const [annualPolicy, setAnnualPolicy] = useState<AnnualPolicy | null>(null)

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [exportingExcel, setExportingExcel] = useState(false)
  const [printing, setPrinting] = useState(false)
  const [actionId, setActionId] = useState<number | null>(null)
  const [actionType, setActionType] = useState<"approve" | "reject" | null>(null)

  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [showCreateForm, setShowCreateForm] = useState(true)
  const [form, setForm] = useState<CreateFormState>(INITIAL_FORM)

  const employeeMap = useMemo(() => {
    return new Map(employees.map((employee) => [employee.id, employee]))
  }, [employees])

  const loadRequests = useCallback(async () => {
    const data = await apiRequest("/api/company/leaves/requests/")
    setRequests(normalizeRequests(data))
  }, [])

  const loadBalances = useCallback(async () => {
    const data = await apiRequest("/api/company/leaves/balance/")
    setBalances(normalizeBalances(data))
  }, [])

  const loadLeaveTypes = useCallback(async () => {
    const data = await apiRequestWithFallback([
      "/api/company/leaves/types/",
      "/api/company/leaves/leave-types/",
    ])
    setLeaveTypes(normalizeLeaveTypes(data))
  }, [])

  const loadEmployees = useCallback(async () => {
    const data = await apiRequest("/api/company/employees/")
    setEmployees(normalizeEmployees(data))
  }, [])

  const loadAnnualPolicy = useCallback(async () => {
    try {
      const data = await apiRequest("/api/company/leaves/annual-policy/")
      setAnnualPolicy((data || {}) as AnnualPolicy)
    } catch {
      setAnnualPolicy(null)
    }
  }, [])

  const loadAll = useCallback(
    async (silent = false) => {
      try {
        if (silent) {
          setRefreshing(true)
        } else {
          setLoading(true)
        }

        await Promise.all([
          loadRequests(),
          loadBalances(),
          loadLeaveTypes(),
          loadEmployees(),
          loadAnnualPolicy(),
        ])
      } catch (error) {
        console.error("Leaves page load error:", error)
        toast.error(
          error instanceof Error
            ? error.message
            : "تعذر تحميل بيانات صفحة الإجازات."
        )
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [loadAnnualPolicy, loadBalances, loadEmployees, loadLeaveTypes, loadRequests]
  )

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const filteredRequests = useMemo(() => {
    const query = search.trim().toLowerCase()

    return requests.filter((item) => {
      const matchesStatus =
        statusFilter === "all"
          ? true
          : String(item.status).toLowerCase() === statusFilter

      const employeeInfo = item.employee_id ? employeeMap.get(item.employee_id) : null

      const matchesSearch =
        !query ||
        item.employee_name.toLowerCase().includes(query) ||
        item.type.toLowerCase().includes(query) ||
        String(item.id).includes(query) ||
        String(employeeInfo?.email || "")
          .toLowerCase()
          .includes(query) ||
        String(employeeInfo?.phone || "")
          .toLowerCase()
          .includes(query)

      return matchesStatus && matchesSearch
    })
  }, [requests, search, statusFilter, employeeMap])

  const stats = useMemo(() => {
    const pending = requests.filter(
      (item) => item.status?.toLowerCase() === "pending"
    ).length
    const approved = requests.filter(
      (item) => item.status?.toLowerCase() === "approved"
    ).length
    const rejected = requests.filter(
      (item) => item.status?.toLowerCase() === "rejected"
    ).length
    const totalBalance = balances.reduce(
      (sum, item) => sum + Number(item.balance || 0),
      0
    )

    return {
      total: requests.length,
      pending,
      approved,
      rejected,
      totalBalance,
    }
  }, [balances, requests])

  const pendingVisibleCount = useMemo(
    () =>
      filteredRequests.filter(
        (item) => String(item.status || "").toLowerCase() === "pending"
      ).length,
    [filteredRequests]
  )

  const approvedVisibleCount = useMemo(
    () =>
      filteredRequests.filter(
        (item) => String(item.status || "").toLowerCase() === "approved"
      ).length,
    [filteredRequests]
  )

  const rejectedVisibleCount = useMemo(
    () =>
      filteredRequests.filter(
        (item) => String(item.status || "").toLowerCase() === "rejected"
      ).length,
    [filteredRequests]
  )

  const handleRefresh = async () => {
    await loadAll(true)
    toast.success("تم تحديث بيانات الإجازات بنجاح")
  }

  const handleCreate = async () => {
    if (!form.leave_type_id || !form.start_date || !form.end_date) {
      toast.error("يرجى تعبئة نوع الإجازة وتاريخ البداية والنهاية")
      return
    }

    if (form.end_date < form.start_date) {
      toast.error("تاريخ النهاية يجب أن يكون بعد أو يساوي تاريخ البداية")
      return
    }

    try {
      setSubmitting(true)

      const csrfToken = getCookie("csrftoken")
      const body = new FormData()

      if (form.employee_id) body.append("employee_id", form.employee_id)
      body.append("leave_type_id", form.leave_type_id)
      body.append("start_date", form.start_date)
      body.append("end_date", form.end_date)
      body.append("reason", form.reason)

      await apiRequest("/api/company/leaves/request/", {
        method: "POST",
        body,
        headers: {
          "X-CSRFToken": csrfToken,
        },
      })

      toast.success("تم إنشاء طلب الإجازة بنجاح")
      setForm(INITIAL_FORM)
      await loadAll(true)
    } catch (error) {
      console.error("Create leave request error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر إنشاء طلب الإجازة"
      )
    } finally {
      setSubmitting(false)
    }
  }

  const handleAction = async (
    requestId: number,
    type: "approve" | "reject"
  ) => {
    try {
      setActionId(requestId)
      setActionType(type)

      const csrfToken = getCookie("csrftoken")
      const endpoint =
        type === "approve"
          ? `/api/company/leaves/${requestId}/approve/`
          : `/api/company/leaves/${requestId}/reject/`

      await apiRequest(endpoint, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
      })

      toast.success(type === "approve" ? "تم اعتماد الطلب" : "تم رفض الطلب")
      await loadAll(true)
    } catch (error) {
      console.error("Leave action error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر تنفيذ العملية"
      )
    } finally {
      setActionId(null)
      setActionType(null)
    }
  }

  const handlePrintRequests = () => {
    try {
      setPrinting(true)

      const printableWindow = window.open("", "_blank", "width=1200,height=900")
      if (!printableWindow) {
        toast.error("تعذر فتح نافذة الطباعة. تأكد من السماح بالنوافذ المنبثقة.")
        return
      }

      printableWindow.document.open()
      printableWindow.document.write(buildPrintableHtml(filteredRequests))
      printableWindow.document.close()
      printableWindow.focus()

      setTimeout(() => {
        printableWindow.print()
        printableWindow.close()
      }, 250)

      toast.success("تم تجهيز قائمة الطلبات للطباعة")
    } catch (error) {
      console.error("Print requests error:", error)
      toast.error("تعذر تجهيز الطباعة")
    } finally {
      setTimeout(() => setPrinting(false), 600)
    }
  }

  const handleExportExcel = async () => {
    try {
      setExportingExcel(true)

      const XLSX = await import("xlsx")

      const rows = filteredRequests.map((item, index) => {
        const employeeInfo = item.employee_id ? employeeMap.get(item.employee_id) : null

        return {
          "م": index + 1,
          "رقم الطلب": item.id,
          "الموظف": item.employee_name,
          "البريد": employeeInfo?.email || "",
          "الجوال": employeeInfo?.phone || "",
          "نوع الإجازة": item.type,
          "من تاريخ": formatDate(item.from_date),
          "إلى تاريخ": formatDate(item.to_date),
          "الحالة": getStatusLabel(item.status),
        }
      })

      const worksheet = XLSX.utils.json_to_sheet(rows)
      const workbook = XLSX.utils.book_new()

      XLSX.utils.book_append_sheet(workbook, worksheet, "Leave Requests")

      const range = XLSX.utils.decode_range(worksheet["!ref"] || "A1:I1")
      const colWidths: Array<{ wch: number }> = []

      for (let col = range.s.c; col <= range.e.c; col += 1) {
        let maxLength = 14
        for (let row = range.s.r; row <= range.e.r; row += 1) {
          const cellAddress = XLSX.utils.encode_cell({ r: row, c: col })
          const cell = worksheet[cellAddress]
          const cellValue = cell ? String(cell.v ?? "") : ""
          maxLength = Math.max(maxLength, cellValue.length + 4)
        }
        colWidths.push({ wch: maxLength })
      }

      worksheet["!cols"] = colWidths

      XLSX.writeFile(
        workbook,
        `company-leave-requests-${new Date().toLocaleDateString("en-CA")}.xlsx`
      )

      toast.success("تم تصدير الطلبات إلى Excel بنجاح")
    } catch (error) {
      console.error("Export excel error:", error)
      toast.error("تعذر تصدير ملف Excel")
    } finally {
      setExportingExcel(false)
    }
  }

  const isActionLoading = (requestId: number, type: "approve" | "reject") =>
    actionId === requestId && actionType === type

  return (
    <div className="space-y-6 p-4 md:p-6">
      <div className="relative overflow-hidden rounded-[30px] border border-slate-200/80 bg-gradient-to-br from-white via-slate-50 to-slate-100 p-6 shadow-sm">
        <div className="absolute inset-y-0 left-0 w-48 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent" />
        <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute -bottom-16 left-16 h-36 w-36 rounded-full bg-sky-100 blur-3xl" />

        <div className="relative flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm">
              <Sparkles className="h-4 w-4 text-primary" />
              Leave Center
            </div>

            <div className="space-y-2">
              <h1 className="text-3xl font-black tracking-tight text-slate-900 md:text-4xl">
                إدارة الإجازات
              </h1>
              <p className="max-w-3xl text-sm leading-6 text-slate-600 md:text-[15px]">
                لوحة احترافية لإدارة طلبات الإجازات، الأرصدة، والسياسات السنوية مع
                إمكانيات الاعتماد والطباعة والتصدير من نفس الصفحة.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <Badge className="rounded-full border-0 bg-slate-900 text-white hover:bg-slate-900">
                <ClipboardList className="mr-1 h-3.5 w-3.5" />
                {stats.total} طلب
              </Badge>
              <Badge className="rounded-full border-0 bg-emerald-600 text-white hover:bg-emerald-600">
                <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                {stats.approved} معتمد
              </Badge>
              <Badge className="rounded-full border-0 bg-amber-500 text-white hover:bg-amber-500">
                <Clock3 className="mr-1 h-3.5 w-3.5" />
                {stats.pending} بانتظار الاعتماد
              </Badge>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:min-w-[360px]">
            <div className="rounded-3xl border border-white/70 bg-white/80 p-4 shadow-sm backdrop-blur">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-500">
                    الرصيد الإجمالي
                  </p>
                  <p className="mt-2 text-3xl font-black text-slate-900">
                    {stats.totalBalance.toFixed(1)}
                  </p>
                </div>
                <div className="rounded-2xl bg-sky-100 p-3 text-sky-700">
                  <TimerReset className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                مجموع أرصدة الأنواع الحالية
              </p>
            </div>

            <div className="rounded-3xl border border-white/70 bg-slate-950 p-4 text-white shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-300">الطلبات المرئية</p>
                  <p className="mt-2 text-3xl font-black">{filteredRequests.length}</p>
                </div>
                <div className="rounded-2xl bg-white/10 p-3 text-white">
                  <CalendarRange className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-2 text-xs text-slate-300">
                حسب الفلاتر والبحث الحالي
              </p>
            </div>
          </div>
        </div>

        <div className="relative mt-6 flex flex-wrap items-center gap-3">
          <Button
            variant="outline"
            className="rounded-2xl border-slate-200 bg-white/90"
            onClick={() => setShowCreateForm((prev) => !prev)}
          >
            <Plus className="mr-2 h-4 w-4" />
            {showCreateForm ? "إخفاء نموذج الطلب" : "إظهار نموذج الطلب"}
          </Button>

          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            className="rounded-2xl"
          >
            {refreshing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            تحديث البيانات
          </Button>

          <Button
            variant="outline"
            className="rounded-2xl border-slate-200 bg-white/90"
            onClick={handlePrintRequests}
            disabled={printing}
          >
            {printing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Printer className="mr-2 h-4 w-4" />
            )}
            طباعة الطلبات
          </Button>

          <Button
            variant="outline"
            className="rounded-2xl border-slate-200 bg-white/90"
            onClick={handleExportExcel}
            disabled={exportingExcel}
          >
            {exportingExcel ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <FileSpreadsheet className="mr-2 h-4 w-4" />
            )}
            تصدير Excel
          </Button>
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="rounded-[28px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">إجمالي الطلبات</p>
              <p className="text-3xl font-black text-slate-900">{stats.total}</p>
              <p className="text-xs text-slate-400">كل طلبات الإجازات المسجلة</p>
            </div>
            <div className="rounded-2xl bg-primary/10 p-3 text-primary">
              <CalendarDays className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-[28px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">بانتظار الاعتماد</p>
              <p className="text-3xl font-black text-amber-600">{stats.pending}</p>
              <p className="text-xs text-slate-400">طلبات تحتاج إجراء</p>
            </div>
            <div className="rounded-2xl bg-amber-100 p-3 text-amber-700">
              <Clock3 className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-[28px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">طلبات معتمدة</p>
              <p className="text-3xl font-black text-emerald-600">
                {stats.approved}
              </p>
              <p className="text-xs text-slate-400">تم إنهاؤها بنجاح</p>
            </div>
            <div className="rounded-2xl bg-emerald-100 p-3 text-emerald-700">
              <CheckCircle2 className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-[28px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">طلبات مرفوضة</p>
              <p className="text-3xl font-black text-rose-600">{stats.rejected}</p>
              <p className="text-xs text-slate-400">طلبات لم تعتمد</p>
            </div>
            <div className="rounded-2xl bg-rose-100 p-3 text-rose-700">
              <ShieldAlert className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        {showCreateForm ? (
          <Card className="rounded-[30px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <CardTitle className="text-2xl font-black text-slate-900">
                    إنشاء طلب إجازة
                  </CardTitle>
                  <CardDescription className="mt-2 text-sm leading-6 text-slate-600">
                    يمكنك إنشاء طلب لنفسك أو لموظف آخر حسب الصلاحيات المتاحة لك،
                    مع اختيار النوع والتاريخ وإضافة السبب.
                  </CardDescription>
                </div>

                <div className="hidden rounded-2xl bg-primary/10 p-3 text-primary md:flex">
                  <Briefcase className="h-5 w-5" />
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">
                    الموظف
                  </label>
                  <Select
                    value={form.employee_id || "self"}
                    onValueChange={(value) =>
                      setForm((prev) => ({
                        ...prev,
                        employee_id: value === "self" ? "" : value,
                      }))
                    }
                  >
                    <SelectTrigger className="h-12 rounded-2xl border-slate-200 bg-white">
                      <SelectValue placeholder="اختر الموظف أو اتركه لنفسك" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="self">نفسي / تلقائيًا</SelectItem>
                      {employees.map((employee) => (
                        <SelectItem key={employee.id} value={String(employee.id)}>
                          {employee.full_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">
                    نوع الإجازة
                  </label>
                  <Select
                    value={form.leave_type_id}
                    onValueChange={(value) =>
                      setForm((prev) => ({ ...prev, leave_type_id: value }))
                    }
                  >
                    <SelectTrigger className="h-12 rounded-2xl border-slate-200 bg-white">
                      <SelectValue placeholder="اختر نوع الإجازة" />
                    </SelectTrigger>
                    <SelectContent>
                      {leaveTypes.map((type) => (
                        <SelectItem key={type.id} value={String(type.id)}>
                          {type.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">
                    من تاريخ
                  </label>
                  <Input
                    type="date"
                    className="h-12 rounded-2xl border-slate-200"
                    value={form.start_date}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        start_date: e.target.value,
                      }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-slate-700">
                    إلى تاريخ
                  </label>
                  <Input
                    type="date"
                    className="h-12 rounded-2xl border-slate-200"
                    value={form.end_date}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        end_date: e.target.value,
                      }))
                    }
                  />
                </div>
              </div>

              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/70 p-4">
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-slate-200/70">
                    <p className="text-xs font-medium text-slate-500">بداية الطلب</p>
                    <p className="mt-1 text-sm font-bold text-slate-900">
                      {form.start_date || "—"}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-slate-200/70">
                    <p className="text-xs font-medium text-slate-500">نهاية الطلب</p>
                    <p className="mt-1 text-sm font-bold text-slate-900">
                      {form.end_date || "—"}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-slate-200/70">
                    <p className="text-xs font-medium text-slate-500">نوع الإجازة</p>
                    <p className="mt-1 truncate text-sm font-bold text-slate-900">
                      {leaveTypes.find(
                        (type) => String(type.id) === String(form.leave_type_id)
                      )?.name || "—"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700">السبب</label>
                <textarea
                  value={form.reason}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      reason: e.target.value,
                    }))
                  }
                  placeholder="اكتب سبب طلب الإجازة بشكل واضح..."
                  className="min-h-[140px] w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-primary"
                />
              </div>

              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={handleCreate}
                  disabled={submitting}
                  className="rounded-2xl px-5"
                >
                  {submitting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="mr-2 h-4 w-4" />
                  )}
                  إنشاء الطلب
                </Button>

                <Button
                  variant="outline"
                  className="rounded-2xl border-slate-200 px-5"
                  onClick={() => setForm(INITIAL_FORM)}
                  disabled={submitting}
                >
                  إعادة تعيين
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="rounded-[30px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
            <CardContent className="flex min-h-[320px] items-center justify-center p-6 text-center">
              <div className="space-y-3">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-slate-600">
                  <Plus className="h-7 w-7" />
                </div>
                <div>
                  <h3 className="text-lg font-black text-slate-900">
                    نموذج إنشاء الطلب مخفي
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    يمكنك إظهاره مرة أخرى من الشريط العلوي لبدء إنشاء طلب إجازة جديد.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="space-y-6">
          <Card className="rounded-[30px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
            <CardHeader>
              <CardTitle className="text-2xl font-black text-slate-900">
                أرصدة الإجازات
              </CardTitle>
              <CardDescription className="mt-1 text-sm text-slate-600">
                ملخص سريع وواضح للأرصدة المتاحة حسب كل نوع إجازة.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              {balances.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
                  لا توجد أرصدة متاحة حاليًا.
                </div>
              ) : (
                balances.map((item, index) => (
                  <div
                    key={`${item.leave_type}-${index}`}
                    className="group rounded-3xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-4 transition hover:shadow-sm"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-bold text-slate-900">
                          {item.leave_type}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          الرصيد المتاح حاليًا لهذا النوع
                        </p>
                      </div>
                      <Badge
                        variant="outline"
                        className="rounded-full border-primary/20 bg-primary/5 px-3 py-1 text-primary"
                      >
                        {item.balance.toFixed(1)} يوم
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card className="rounded-[30px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
            <CardHeader>
              <CardTitle className="text-2xl font-black text-slate-900">
                سياسة الإجازة السنوية
              </CardTitle>
              <CardDescription className="mt-1 text-sm text-slate-600">
                قراءة سريعة لسياسة الإجازة السنوية المطبقة على الشركة.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              {annualPolicy ? (
                <>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
                      <p className="text-xs font-medium text-slate-500">أيام سنوية</p>
                      <p className="mt-2 text-2xl font-black text-slate-900">
                        {typeof annualPolicy.annual_days === "number"
                          ? annualPolicy.annual_days
                          : "—"}
                      </p>
                    </div>

                    <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
                      <p className="text-xs font-medium text-slate-500">
                        الحد الأقصى للترحيل
                      </p>
                      <p className="mt-2 text-2xl font-black text-slate-900">
                        {typeof annualPolicy.max_carry_forward_days === "number"
                          ? annualPolicy.max_carry_forward_days
                          : "—"}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-3xl border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-slate-600">التراكم</span>
                      <Badge
                        variant="outline"
                        className={
                          annualPolicy.accrual_enabled
                            ? "rounded-full border-emerald-200 bg-emerald-50 text-emerald-700"
                            : "rounded-full border-slate-200 bg-slate-50 text-slate-700"
                        }
                      >
                        {annualPolicy.accrual_enabled ? "مفعل" : "غير مفعل"}
                      </Badge>
                    </div>
                  </div>

                  <div className="rounded-3xl border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-slate-600">
                        ترحيل الرصيد
                      </span>
                      <Badge
                        variant="outline"
                        className={
                          annualPolicy.carry_forward_enabled
                            ? "rounded-full border-emerald-200 bg-emerald-50 text-emerald-700"
                            : "rounded-full border-slate-200 bg-slate-50 text-slate-700"
                        }
                      >
                        {annualPolicy.carry_forward_enabled
                          ? "مسموح"
                          : "غير مسموح"}
                      </Badge>
                    </div>
                  </div>
                </>
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
                  لم يتم العثور على بيانات سياسة الإجازة السنوية أو أن المسار غير
                  مفعّل بعد.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>

      <Card className="rounded-[30px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-4 2xl:flex-row 2xl:items-center 2xl:justify-between">
            <div>
              <CardTitle className="text-2xl font-black text-slate-900">
                طلبات الإجازات
              </CardTitle>
              <CardDescription className="mt-2 text-sm leading-6 text-slate-600">
                بحث وفلاتر وعمليات الاعتماد والرفض مع تجهيز مباشر للطباعة أو التصدير.
              </CardDescription>
            </div>

            <div className="flex w-full flex-col gap-3 xl:flex-row 2xl:w-auto">
              <div className="relative min-w-[260px]">
                <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="ابحث بالموظف أو النوع أو رقم الطلب..."
                  className="h-11 rounded-2xl border-slate-200 pr-10"
                />
              </div>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="h-11 min-w-[180px] rounded-2xl border-slate-200">
                  <SelectValue placeholder="كل الحالات" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">كل الحالات</SelectItem>
                  <SelectItem value="pending">قيد الانتظار</SelectItem>
                  <SelectItem value="approved">معتمد</SelectItem>
                  <SelectItem value="rejected">مرفوض</SelectItem>
                  <SelectItem value="cancelled">ملغي</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                className="h-11 rounded-2xl border-slate-200"
                onClick={handlePrintRequests}
                disabled={printing}
              >
                {printing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Printer className="mr-2 h-4 w-4" />
                )}
                طباعة PDF
              </Button>

              <Button
                variant="outline"
                className="h-11 rounded-2xl border-slate-200"
                onClick={handleExportExcel}
                disabled={exportingExcel}
              >
                {exportingExcel ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <FileSpreadsheet className="mr-2 h-4 w-4" />
                )}
                تصدير Excel
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="mb-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50/70 px-4 py-3">
              <p className="text-xs font-medium text-slate-500">المعروض حاليًا</p>
              <p className="mt-1 text-2xl font-black text-slate-900">
                {filteredRequests.length}
              </p>
            </div>
            <div className="rounded-2xl border border-amber-200 bg-amber-50/80 px-4 py-3">
              <p className="text-xs font-medium text-amber-700">بانتظار الاعتماد</p>
              <p className="mt-1 text-2xl font-black text-amber-700">
                {pendingVisibleCount}
              </p>
            </div>
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/80 px-4 py-3">
              <p className="text-xs font-medium text-emerald-700">معتمدة</p>
              <p className="mt-1 text-2xl font-black text-emerald-700">
                {approvedVisibleCount}
              </p>
            </div>
            <div className="rounded-2xl border border-rose-200 bg-rose-50/80 px-4 py-3">
              <p className="text-xs font-medium text-rose-700">مرفوضة</p>
              <p className="mt-1 text-2xl font-black text-rose-700">
                {rejectedVisibleCount}
              </p>
            </div>
          </div>

          <Separator className="mb-5" />

          {loading ? (
            <div className="flex min-h-[320px] items-center justify-center">
              <div className="flex items-center gap-3 rounded-2xl border bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
                <Loader2 className="h-4 w-4 animate-spin" />
                جاري تحميل بيانات الإجازات...
              </div>
            </div>
          ) : filteredRequests.length === 0 ? (
            <div className="flex min-h-[320px] items-center justify-center rounded-[28px] border border-dashed border-slate-200 bg-slate-50/50 text-center">
              <div className="space-y-3 px-6">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-slate-500">
                  <CalendarDays className="h-7 w-7" />
                </div>
                <h3 className="text-xl font-black text-slate-900">
                  لا توجد طلبات مطابقة
                </h3>
                <p className="text-sm leading-6 text-slate-500">
                  جرّب تغيير البحث أو الحالة أو أنشئ طلب إجازة جديد ليظهر هنا.
                </p>
              </div>
            </div>
          ) : (
            <div className="overflow-hidden rounded-[28px] border border-slate-200">
              <Table>
                <TableHeader className="bg-slate-50/90">
                  <TableRow className="hover:bg-slate-50/90">
                    <TableHead className="whitespace-nowrap font-bold">#</TableHead>
                    <TableHead className="whitespace-nowrap font-bold">
                      الموظف
                    </TableHead>
                    <TableHead className="whitespace-nowrap font-bold">
                      نوع الإجازة
                    </TableHead>
                    <TableHead className="whitespace-nowrap font-bold">
                      من
                    </TableHead>
                    <TableHead className="whitespace-nowrap font-bold">
                      إلى
                    </TableHead>
                    <TableHead className="whitespace-nowrap font-bold">
                      الحالة
                    </TableHead>
                    <TableHead className="whitespace-nowrap text-left font-bold">
                      الإجراءات
                    </TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {filteredRequests.map((item) => {
                    const employeeInfo = item.employee_id
                      ? employeeMap.get(item.employee_id)
                      : null

                    return (
                      <TableRow key={item.id} className="hover:bg-slate-50/70">
                        <TableCell className="font-bold text-slate-700">
                          #{item.id}
                        </TableCell>

                        <TableCell>
                          <div className="flex min-w-[280px] items-start gap-3">
                            <Avatar className="h-12 w-12 rounded-2xl border border-slate-200 shadow-sm">
                              <AvatarImage
                                src={employeeInfo?.avatar || ""}
                                alt={item.employee_name}
                              />
                              <AvatarFallback className="rounded-2xl bg-slate-100 font-semibold text-slate-700">
                                {getInitials(item.employee_name)}
                              </AvatarFallback>
                            </Avatar>

                            <div className="min-w-0 space-y-1">
                              <div className="truncate font-bold text-slate-900">
                                {item.employee_name}
                              </div>

                              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                                {employeeInfo?.email ? (
                                  <span>{employeeInfo.email}</span>
                                ) : null}

                                {employeeInfo?.phone ? (
                                  <span>{employeeInfo.phone}</span>
                                ) : null}

                                <span>Request ID: #{item.id}</span>
                              </div>
                            </div>
                          </div>
                        </TableCell>

                        <TableCell>
                          <Badge
                            variant="outline"
                            className="rounded-full border-slate-200 bg-slate-50 text-slate-700"
                          >
                            {item.type}
                          </Badge>
                        </TableCell>

                        <TableCell className="font-medium text-slate-700">
                          {formatDate(item.from_date)}
                        </TableCell>

                        <TableCell className="font-medium text-slate-700">
                          {formatDate(item.to_date)}
                        </TableCell>

                        <TableCell>
                          <Badge
                            variant="outline"
                            className={`rounded-full ${getStatusBadgeClass(item.status)}`}
                          >
                            {getStatusLabel(item.status)}
                          </Badge>
                        </TableCell>

                        <TableCell className="text-left">
                          {String(item.status).toLowerCase() === "pending" ? (
                            <div className="flex flex-wrap justify-end gap-2">
                              <Button
                                size="sm"
                                className="rounded-xl"
                                onClick={() => handleAction(item.id, "approve")}
                                disabled={
                                  isActionLoading(item.id, "approve") ||
                                  isActionLoading(item.id, "reject")
                                }
                              >
                                {isActionLoading(item.id, "approve") ? (
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                  <CheckCircle2 className="mr-2 h-4 w-4" />
                                )}
                                اعتماد
                              </Button>

                              <Button
                                size="sm"
                                variant="outline"
                                className="rounded-xl border-rose-200 text-rose-700 hover:bg-rose-50 hover:text-rose-800"
                                onClick={() => handleAction(item.id, "reject")}
                                disabled={
                                  isActionLoading(item.id, "approve") ||
                                  isActionLoading(item.id, "reject")
                                }
                              >
                                {isActionLoading(item.id, "reject") ? (
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                  <XCircle className="mr-2 h-4 w-4" />
                                )}
                                رفض
                              </Button>
                            </div>
                          ) : (
                            <div className="flex justify-end">
                              <Badge
                                variant="outline"
                                className="rounded-full border-slate-200 bg-slate-50 text-slate-600"
                              >
                                لا توجد إجراءات
                              </Badge>
                            </div>
                          )}
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
    </div>
  )
}