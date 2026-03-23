"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Briefcase,
  CalendarDays,
  CalendarRange,
  CheckCircle2,
  ClipboardList,
  Clock3,
  FileSpreadsheet,
  Loader2,
  Plus,
  Printer,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  TimerReset,
  XCircle,
} from "lucide-react"
import { toast } from "sonner"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
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
import { Label } from "@/components/ui/label"
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
import { Textarea } from "@/components/ui/textarea"

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000"

type Locale = "ar" | "en"

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

type Dictionary = {
  centerLabel: string
  pageTitle: string
  pageDescription: string
  totalRequests: string
  approved: string
  pending: string
  rejected: string
  cancelled: string
  totalBalance: string
  totalBalanceHint: string
  visibleRequests: string
  visibleRequestsHint: string
  hideForm: string
  showForm: string
  refreshData: string
  printRequests: string
  exportExcel: string
  createLeaveRequest: string
  createLeaveRequestDesc: string
  employee: string
  selfAutomatic: string
  selfAutomaticHint: string
  leaveType: string
  selectEmployee: string
  selectLeaveType: string
  fromDate: string
  toDate: string
  startPreview: string
  endPreview: string
  leaveTypePreview: string
  reason: string
  reasonPlaceholder: string
  createRequest: string
  reset: string
  formHiddenTitle: string
  formHiddenDesc: string
  leaveBalances: string
  leaveBalancesDesc: string
  noBalances: string
  availableBalanceHint: string
  days: string
  annualPolicy: string
  annualPolicyDesc: string
  annualDays: string
  maxCarryForward: string
  accrual: string
  carryForward: string
  enabled: string
  disabled: string
  allowed: string
  notAllowed: string
  annualPolicyNotFound: string
  requestsList: string
  requestsListDesc: string
  searchPlaceholder: string
  allStatuses: string
  currentlyVisible: string
  noMatchingRequests: string
  noMatchingRequestsDesc: string
  loadingLeaves: string
  requestNumber: string
  employeeCol: string
  leaveTypeCol: string
  fromCol: string
  toCol: string
  statusCol: string
  actionsCol: string
  email: string
  phone: string
  requestId: string
  noActions: string
  approve: string
  reject: string
  totalRequestsStatHint: string
  pendingRequestsHint: string
  approvedRequestsHint: string
  rejectedRequestsHint: string
  printTitle: string
  printSubtitle: string
  printDate: string
  printTime: string
  totalSummary: string
  approvedSummary: string
  pendingSummary: string
  rejectedSummary: string
  serialCol: string
  emptyPrintable: string
  createSuccess: string
  approveSuccess: string
  rejectSuccess: string
  refreshSuccess: string
  exportSuccess: string
  printPrepared: string
  createError: string
  actionError: string
  loadError: string
  printError: string
  exportError: string
  popupBlocked: string
  fillRequired: string
  invalidDateRange: string
  unknown: string
}

const translations: Record<Locale, Dictionary> = {
  ar: {
    centerLabel: "Leave Center",
    pageTitle: "إدارة الإجازات",
    pageDescription:
      "لوحة احترافية لإدارة طلبات الإجازات والأرصدة والسياسات السنوية مع البحث والاعتماد والطباعة والتصدير من نفس الصفحة.",
    totalRequests: "إجمالي الطلبات",
    approved: "معتمد",
    pending: "قيد الانتظار",
    rejected: "مرفوض",
    cancelled: "ملغي",
    totalBalance: "الرصيد الإجمالي",
    totalBalanceHint: "مجموع أرصدة أنواع الإجازات الحالية",
    visibleRequests: "الطلبات المرئية",
    visibleRequestsHint: "بحسب البحث والفلاتر الحالية",
    hideForm: "إخفاء نموذج الطلب",
    showForm: "إظهار نموذج الطلب",
    refreshData: "تحديث البيانات",
    printRequests: "طباعة الطلبات",
    exportExcel: "تصدير Excel",
    createLeaveRequest: "إنشاء طلب إجازة",
    createLeaveRequestDesc:
      "يمكنك إنشاء طلب لنفسك أو لموظف آخر حسب الصلاحيات المتاحة، مع تحديد النوع والتواريخ وسبب الطلب.",
    employee: "الموظف",
    selfAutomatic: "نفسي / تلقائيًا",
    selfAutomaticHint: "اختر الموظف أو اتركه لنفسك",
    leaveType: "نوع الإجازة",
    selectEmployee: "اختر الموظف",
    selectLeaveType: "اختر نوع الإجازة",
    fromDate: "من تاريخ",
    toDate: "إلى تاريخ",
    startPreview: "بداية الطلب",
    endPreview: "نهاية الطلب",
    leaveTypePreview: "نوع الإجازة",
    reason: "السبب",
    reasonPlaceholder: "اكتب سبب طلب الإجازة بشكل واضح...",
    createRequest: "إنشاء الطلب",
    reset: "إعادة تعيين",
    formHiddenTitle: "نموذج إنشاء الطلب مخفي",
    formHiddenDesc:
      "يمكنك إظهاره مرة أخرى من الشريط العلوي لبدء إنشاء طلب إجازة جديد.",
    leaveBalances: "أرصدة الإجازات",
    leaveBalancesDesc: "ملخص سريع وواضح للأرصدة المتاحة حسب كل نوع إجازة.",
    noBalances: "لا توجد أرصدة متاحة حاليًا.",
    availableBalanceHint: "الرصيد المتاح حاليًا لهذا النوع",
    days: "يوم",
    annualPolicy: "سياسة الإجازة السنوية",
    annualPolicyDesc: "قراءة سريعة لسياسة الإجازة السنوية المطبقة على الشركة.",
    annualDays: "أيام سنوية",
    maxCarryForward: "الحد الأقصى للترحيل",
    accrual: "التراكم",
    carryForward: "ترحيل الرصيد",
    enabled: "مفعل",
    disabled: "غير مفعل",
    allowed: "مسموح",
    notAllowed: "غير مسموح",
    annualPolicyNotFound:
      "لم يتم العثور على بيانات سياسة الإجازة السنوية أو أن المسار غير مفعّل بعد.",
    requestsList: "طلبات الإجازات",
    requestsListDesc:
      "بحث وفلاتر وعمليات الاعتماد والرفض مع تجهيز مباشر للطباعة أو التصدير.",
    searchPlaceholder: "ابحث بالموظف أو النوع أو رقم الطلب...",
    allStatuses: "كل الحالات",
    currentlyVisible: "المعروض حاليًا",
    noMatchingRequests: "لا توجد طلبات مطابقة",
    noMatchingRequestsDesc:
      "جرّب تغيير البحث أو الحالة أو أنشئ طلب إجازة جديد ليظهر هنا.",
    loadingLeaves: "جاري تحميل بيانات الإجازات...",
    requestNumber: "رقم الطلب",
    employeeCol: "الموظف",
    leaveTypeCol: "نوع الإجازة",
    fromCol: "من",
    toCol: "إلى",
    statusCol: "الحالة",
    actionsCol: "الإجراءات",
    email: "البريد",
    phone: "الجوال",
    requestId: "رقم الطلب",
    noActions: "لا توجد إجراءات",
    approve: "اعتماد",
    reject: "رفض",
    totalRequestsStatHint: "كل طلبات الإجازات المسجلة",
    pendingRequestsHint: "طلبات تحتاج إجراء",
    approvedRequestsHint: "تم إنهاؤها بنجاح",
    rejectedRequestsHint: "طلبات لم تعتمد",
    printTitle: "طلبات الإجازات",
    printSubtitle: "تقرير قابل للطباعة من صفحة إدارة الإجازات",
    printDate: "تاريخ الطباعة",
    printTime: "الوقت",
    totalSummary: "إجمالي الطلبات",
    approvedSummary: "معتمدة",
    pendingSummary: "بانتظار الاعتماد",
    rejectedSummary: "مرفوضة",
    serialCol: "م",
    emptyPrintable: "لا توجد بيانات لطباعة قائمة الطلبات الحالية.",
    createSuccess: "تم إنشاء طلب الإجازة بنجاح",
    approveSuccess: "تم اعتماد الطلب",
    rejectSuccess: "تم رفض الطلب",
    refreshSuccess: "تم تحديث بيانات الإجازات بنجاح",
    exportSuccess: "تم تصدير الطلبات إلى Excel بنجاح",
    printPrepared: "تم تجهيز قائمة الطلبات للطباعة",
    createError: "تعذر إنشاء طلب الإجازة",
    actionError: "تعذر تنفيذ العملية",
    loadError: "تعذر تحميل بيانات صفحة الإجازات.",
    printError: "تعذر تجهيز الطباعة",
    exportError: "تعذر تصدير ملف Excel",
    popupBlocked: "تعذر فتح نافذة الطباعة. تأكد من السماح بالنوافذ المنبثقة.",
    fillRequired: "يرجى تعبئة نوع الإجازة وتاريخ البداية والنهاية",
    invalidDateRange: "تاريخ النهاية يجب أن يكون بعد أو يساوي تاريخ البداية",
    unknown: "غير معروف",
  },
  en: {
    centerLabel: "Leave Center",
    pageTitle: "Leave Management",
    pageDescription:
      "A professional workspace to manage leave requests, balances, and annual policies with search, approvals, printing, and export from one page.",
    totalRequests: "Total Requests",
    approved: "Approved",
    pending: "Pending",
    rejected: "Rejected",
    cancelled: "Cancelled",
    totalBalance: "Total Balance",
    totalBalanceHint: "Sum of current leave type balances",
    visibleRequests: "Visible Requests",
    visibleRequestsHint: "Based on current search and filters",
    hideForm: "Hide Request Form",
    showForm: "Show Request Form",
    refreshData: "Refresh Data",
    printRequests: "Print Requests",
    exportExcel: "Export Excel",
    createLeaveRequest: "Create Leave Request",
    createLeaveRequestDesc:
      "Create a leave request for yourself or another employee based on your permissions, then select type, dates, and reason.",
    employee: "Employee",
    selfAutomatic: "Myself / Auto",
    selfAutomaticHint: "Select an employee or leave it for yourself",
    leaveType: "Leave Type",
    selectEmployee: "Select employee",
    selectLeaveType: "Select leave type",
    fromDate: "From Date",
    toDate: "To Date",
    startPreview: "Start Date",
    endPreview: "End Date",
    leaveTypePreview: "Leave Type",
    reason: "Reason",
    reasonPlaceholder: "Write the leave request reason clearly...",
    createRequest: "Create Request",
    reset: "Reset",
    formHiddenTitle: "Request form is hidden",
    formHiddenDesc:
      "You can show it again from the top action bar to create a new leave request.",
    leaveBalances: "Leave Balances",
    leaveBalancesDesc: "A quick and clear summary of available balances by leave type.",
    noBalances: "No balances are currently available.",
    availableBalanceHint: "Currently available balance for this type",
    days: "days",
    annualPolicy: "Annual Leave Policy",
    annualPolicyDesc: "A quick overview of the company annual leave policy.",
    annualDays: "Annual Days",
    maxCarryForward: "Max Carry Forward",
    accrual: "Accrual",
    carryForward: "Carry Forward",
    enabled: "Enabled",
    disabled: "Disabled",
    allowed: "Allowed",
    notAllowed: "Not Allowed",
    annualPolicyNotFound:
      "Annual leave policy data was not found or the endpoint is not enabled yet.",
    requestsList: "Leave Requests",
    requestsListDesc:
      "Search, filters, approval and rejection actions with direct print and export.",
    searchPlaceholder: "Search by employee, type, or request number...",
    allStatuses: "All Statuses",
    currentlyVisible: "Currently Visible",
    noMatchingRequests: "No matching requests",
    noMatchingRequestsDesc:
      "Try changing the search or status filter, or create a new leave request.",
    loadingLeaves: "Loading leave data...",
    requestNumber: "Request Number",
    employeeCol: "Employee",
    leaveTypeCol: "Leave Type",
    fromCol: "From",
    toCol: "To",
    statusCol: "Status",
    actionsCol: "Actions",
    email: "Email",
    phone: "Phone",
    requestId: "Request ID",
    noActions: "No actions",
    approve: "Approve",
    reject: "Reject",
    totalRequestsStatHint: "All recorded leave requests",
    pendingRequestsHint: "Requests that need action",
    approvedRequestsHint: "Successfully completed requests",
    rejectedRequestsHint: "Requests that were not approved",
    printTitle: "Leave Requests",
    printSubtitle: "Printable report from the leave management page",
    printDate: "Printed Date",
    printTime: "Time",
    totalSummary: "Total Requests",
    approvedSummary: "Approved",
    pendingSummary: "Pending",
    rejectedSummary: "Rejected",
    serialCol: "No.",
    emptyPrintable: "There is no data to print for the current requests list.",
    createSuccess: "Leave request created successfully",
    approveSuccess: "Request approved successfully",
    rejectSuccess: "Request rejected successfully",
    refreshSuccess: "Leave data refreshed successfully",
    exportSuccess: "Requests exported to Excel successfully",
    printPrepared: "Requests list prepared for printing",
    createError: "Failed to create leave request",
    actionError: "Failed to complete the action",
    loadError: "Failed to load leave page data.",
    printError: "Failed to prepare printing",
    exportError: "Failed to export Excel file",
    popupBlocked: "Unable to open print window. Please allow pop-ups.",
    fillRequired: "Please fill leave type, start date, and end date",
    invalidDateRange: "End date must be after or equal to start date",
    unknown: "Unknown",
  },
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

function detectLocale(): Locale {
  if (typeof document !== "undefined") {
    const htmlLang = document.documentElement.lang?.toLowerCase().trim() || ""
    if (htmlLang.startsWith("ar")) return "ar"
    if (htmlLang.startsWith("en")) return "en"

    const htmlDir = document.documentElement.dir?.toLowerCase().trim() || ""
    if (htmlDir === "rtl") return "ar"
    if (htmlDir === "ltr") return "en"
  }

  if (typeof navigator !== "undefined") {
    const language = navigator.language?.toLowerCase() || ""
    if (language.startsWith("ar")) return "ar"
  }

  return "en"
}

function formatDate(value?: string | null): string {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }
  return date.toLocaleDateString("en-CA")
}

function formatTime(value?: Date): string {
  const date = value || new Date()
  return date.toLocaleTimeString("en-GB")
}

function formatNumber(value?: number | string | null, digits = 0): string {
  if (value === null || value === undefined || value === "") return digits > 0 ? Number(0).toFixed(digits) : "0"

  const numericValue =
    typeof value === "number" ? value : Number(String(value).replace(/,/g, ""))

  if (Number.isNaN(numericValue)) {
    return String(value)
  }

  return digits > 0
    ? numericValue.toFixed(digits)
    : new Intl.NumberFormat("en-US", {
        useGrouping: false,
        maximumFractionDigits: 0,
      }).format(numericValue)
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

function getStatusLabel(status: string | undefined, t: Dictionary): string {
  const normalized = String(status || "").toLowerCase()

  if (normalized === "approved") return t.approved
  if (normalized === "rejected") return t.rejected
  if (normalized === "pending") return t.pending
  if (normalized === "cancelled") return t.cancelled

  return status || t.unknown
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

function buildPrintableHtml(rows: LeaveRequestRow[], locale: Locale) {
  const t = translations[locale]
  const isArabic = locale === "ar"
  const dir = isArabic ? "rtl" : "ltr"
  const align = isArabic ? "right" : "left"
  const oppositeAlign = isArabic ? "left" : "right"

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
          <td>${getStatusLabel(item.status, t)}</td>
        </tr>
      `
    )
    .join("")

  return `
    <html dir="${dir}" lang="${locale}">
      <head>
        <title>${t.printTitle}</title>
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
            gap: 16px;
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
            text-align: ${oppositeAlign};
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
            border-inline-start: 1px solid #e2e8f0;
            text-align: ${align};
          }
          tbody td {
            font-size: 12px;
            padding: 12px 10px;
            border-bottom: 1px solid #e2e8f0;
            border-inline-start: 1px solid #e2e8f0;
            text-align: ${align};
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
            <h1 class="title">${t.printTitle}</h1>
            <p class="subtitle">${t.printSubtitle}</p>
          </div>
          <div class="meta">
            <div>${t.printDate}: ${new Date().toLocaleDateString("en-CA")}</div>
            <div>${t.printTime}: ${formatTime(new Date())}</div>
          </div>
        </div>

        <div class="summary">
          <div class="summary-card">
            <div class="summary-label">${t.totalSummary}</div>
            <div class="summary-value">${rows.length}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">${t.approvedSummary}</div>
            <div class="summary-value">${getStatusCount(rows, "approved")}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">${t.pendingSummary}</div>
            <div class="summary-value">${getStatusCount(rows, "pending")}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">${t.rejectedSummary}</div>
            <div class="summary-value">${getStatusCount(rows, "rejected")}</div>
          </div>
        </div>

        ${
          rows.length === 0
            ? `<div class="empty">${t.emptyPrintable}</div>`
            : `
              <table>
                <thead>
                  <tr>
                    <th>${t.serialCol}</th>
                    <th>${t.requestNumber}</th>
                    <th>${t.employeeCol}</th>
                    <th>${t.leaveTypeCol}</th>
                    <th>${t.fromCol}</th>
                    <th>${t.toCol}</th>
                    <th>${t.statusCol}</th>
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
    cache: "no-store",
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
      "Request failed."
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

  throw lastError || new Error("Failed to reach the requested endpoint.")
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
  const [locale, setLocale] = useState<Locale>("en")
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

  const t = translations[locale]
  const isArabic = locale === "ar"
  const dir = isArabic ? "rtl" : "ltr"

  useEffect(() => {
    const applyLocale = () => {
      setLocale(detectLocale())
    }

    applyLocale()

    const htmlElement = document.documentElement
    const observer = new MutationObserver(() => {
      applyLocale()
    })

    observer.observe(htmlElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    window.addEventListener("languagechange", applyLocale)
    window.addEventListener("focus", applyLocale)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", applyLocale)
      window.removeEventListener("focus", applyLocale)
    }
  }, [])

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
          error instanceof Error ? error.message : t.loadError
        )
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [loadAnnualPolicy, loadBalances, loadEmployees, loadLeaveTypes, loadRequests, t.loadError]
  )

  useEffect(() => {
    void loadAll()
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
    toast.success(t.refreshSuccess)
  }

  const handleCreate = async () => {
    if (!form.leave_type_id || !form.start_date || !form.end_date) {
      toast.error(t.fillRequired)
      return
    }

    if (form.end_date < form.start_date) {
      toast.error(t.invalidDateRange)
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

      toast.success(t.createSuccess)
      setForm(INITIAL_FORM)
      await loadAll(true)
    } catch (error) {
      console.error("Create leave request error:", error)
      toast.error(
        error instanceof Error ? error.message : t.createError
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

      toast.success(type === "approve" ? t.approveSuccess : t.rejectSuccess)
      await loadAll(true)
    } catch (error) {
      console.error("Leave action error:", error)
      toast.error(
        error instanceof Error ? error.message : t.actionError
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
        toast.error(t.popupBlocked)
        return
      }

      printableWindow.document.open()
      printableWindow.document.write(buildPrintableHtml(filteredRequests, locale))
      printableWindow.document.close()
      printableWindow.focus()

      setTimeout(() => {
        printableWindow.print()
        printableWindow.close()
      }, 250)

      toast.success(t.printPrepared)
    } catch (error) {
      console.error("Print requests error:", error)
      toast.error(t.printError)
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
          [t.serialCol]: index + 1,
          [t.requestNumber]: item.id,
          [t.employeeCol]: item.employee_name,
          [t.email]: employeeInfo?.email || "",
          [t.phone]: employeeInfo?.phone || "",
          [t.leaveTypeCol]: item.type,
          [t.fromCol]: formatDate(item.from_date),
          [t.toCol]: formatDate(item.to_date),
          [t.statusCol]: getStatusLabel(item.status, t),
        }
      })

      const worksheet = XLSX.utils.json_to_sheet(rows)
      const workbook = XLSX.utils.book_new()

      XLSX.utils.book_append_sheet(
        workbook,
        worksheet,
        locale === "ar" ? "طلبات الإجازات" : "Leave Requests"
      )

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

      toast.success(t.exportSuccess)
    } catch (error) {
      console.error("Export excel error:", error)
      toast.error(t.exportError)
    } finally {
      setExportingExcel(false)
    }
  }

  const isActionLoading = (requestId: number, type: "approve" | "reject") =>
    actionId === requestId && actionType === type

  return (
    <div dir={dir} className="space-y-6 p-4 md:p-6">
      <div className="relative overflow-hidden rounded-[30px] border border-slate-200/80 bg-gradient-to-br from-white via-slate-50 to-slate-100 p-6 shadow-sm">
        <div className="absolute inset-y-0 start-0 w-48 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent" />
        <div className="absolute -end-16 -top-16 h-40 w-40 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute -bottom-16 start-16 h-36 w-36 rounded-full bg-sky-100 blur-3xl" />

        <div className="relative flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm">
              <Sparkles className="h-4 w-4 text-primary" />
              {t.centerLabel}
            </div>

            <div className="space-y-2">
              <h1 className="text-3xl font-black tracking-tight text-slate-900 md:text-4xl">
                {t.pageTitle}
              </h1>
              <p className="max-w-3xl text-sm leading-6 text-slate-600 md:text-[15px]">
                {t.pageDescription}
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <Badge className="rounded-full border-0 bg-slate-900 text-white hover:bg-slate-900">
                <ClipboardList className="h-3.5 w-3.5" />
                <span className={isArabic ? "mr-1" : "ml-1"}>
                  {formatNumber(stats.total)} {t.totalRequests}
                </span>
              </Badge>
              <Badge className="rounded-full border-0 bg-emerald-600 text-white hover:bg-emerald-600">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span className={isArabic ? "mr-1" : "ml-1"}>
                  {formatNumber(stats.approved)} {t.approved}
                </span>
              </Badge>
              <Badge className="rounded-full border-0 bg-amber-500 text-white hover:bg-amber-500">
                <Clock3 className="h-3.5 w-3.5" />
                <span className={isArabic ? "mr-1" : "ml-1"}>
                  {formatNumber(stats.pending)} {t.pending}
                </span>
              </Badge>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:min-w-[360px]">
            <div className="rounded-3xl border border-white/70 bg-white/80 p-4 shadow-sm backdrop-blur">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-500">
                    {t.totalBalance}
                  </p>
                  <p className="mt-2 text-3xl font-black text-slate-900 tabular-nums">
                    {formatNumber(stats.totalBalance, 1)}
                  </p>
                </div>
                <div className="rounded-2xl bg-sky-100 p-3 text-sky-700">
                  <TimerReset className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                {t.totalBalanceHint}
              </p>
            </div>

            <div className="rounded-3xl border border-white/70 bg-slate-950 p-4 text-white shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-300">
                    {t.visibleRequests}
                  </p>
                  <p className="mt-2 text-3xl font-black tabular-nums">
                    {formatNumber(filteredRequests.length)}
                  </p>
                </div>
                <div className="rounded-2xl bg-white/10 p-3 text-white">
                  <CalendarRange className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-2 text-xs text-slate-300">
                {t.visibleRequestsHint}
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
            <Plus className="h-4 w-4" />
            <span className={isArabic ? "mr-2" : "ml-2"}>
              {showCreateForm ? t.hideForm : t.showForm}
            </span>
          </Button>

          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            className="rounded-2xl"
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            <span className={isArabic ? "mr-2" : "ml-2"}>
              {t.refreshData}
            </span>
          </Button>

          <Button
            variant="outline"
            className="rounded-2xl border-slate-200 bg-white/90"
            onClick={handlePrintRequests}
            disabled={printing}
          >
            {printing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Printer className="h-4 w-4" />
            )}
            <span className={isArabic ? "mr-2" : "ml-2"}>
              {t.printRequests}
            </span>
          </Button>

          <Button
            variant="outline"
            className="rounded-2xl border-slate-200 bg-white/90"
            onClick={handleExportExcel}
            disabled={exportingExcel}
          >
            {exportingExcel ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileSpreadsheet className="h-4 w-4" />
            )}
            <span className={isArabic ? "mr-2" : "ml-2"}>
              {t.exportExcel}
            </span>
          </Button>
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="rounded-[28px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">{t.totalRequests}</p>
              <p className="text-3xl font-black text-slate-900 tabular-nums">
                {formatNumber(stats.total)}
              </p>
              <p className="text-xs text-slate-400">{t.totalRequestsStatHint}</p>
            </div>
            <div className="rounded-2xl bg-primary/10 p-3 text-primary">
              <CalendarDays className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-[28px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">{t.pending}</p>
              <p className="text-3xl font-black text-amber-600 tabular-nums">
                {formatNumber(stats.pending)}
              </p>
              <p className="text-xs text-slate-400">{t.pendingRequestsHint}</p>
            </div>
            <div className="rounded-2xl bg-amber-100 p-3 text-amber-700">
              <Clock3 className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-[28px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">{t.approved}</p>
              <p className="text-3xl font-black text-emerald-600 tabular-nums">
                {formatNumber(stats.approved)}
              </p>
              <p className="text-xs text-slate-400">{t.approvedRequestsHint}</p>
            </div>
            <div className="rounded-2xl bg-emerald-100 p-3 text-emerald-700">
              <CheckCircle2 className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-[28px] border-0 bg-white shadow-sm ring-1 ring-slate-200/70">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">{t.rejected}</p>
              <p className="text-3xl font-black text-rose-600 tabular-nums">
                {formatNumber(stats.rejected)}
              </p>
              <p className="text-xs text-slate-400">{t.rejectedRequestsHint}</p>
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
                    {t.createLeaveRequest}
                  </CardTitle>
                  <CardDescription className="mt-2 text-sm leading-6 text-slate-600">
                    {t.createLeaveRequestDesc}
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
                  <Label className="text-sm font-semibold text-slate-700">
                    {t.employee}
                  </Label>
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
                      <SelectValue placeholder={t.selfAutomaticHint} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="self">{t.selfAutomatic}</SelectItem>
                      {employees.map((employee) => (
                        <SelectItem key={employee.id} value={String(employee.id)}>
                          {employee.full_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-semibold text-slate-700">
                    {t.leaveType}
                  </Label>
                  <Select
                    value={form.leave_type_id}
                    onValueChange={(value) =>
                      setForm((prev) => ({ ...prev, leave_type_id: value }))
                    }
                  >
                    <SelectTrigger className="h-12 rounded-2xl border-slate-200 bg-white">
                      <SelectValue placeholder={t.selectLeaveType} />
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
                  <Label className="text-sm font-semibold text-slate-700">
                    {t.fromDate}
                  </Label>
                  <Input
                    type="date"
                    className="h-12 rounded-2xl border-slate-200 tabular-nums"
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
                  <Label className="text-sm font-semibold text-slate-700">
                    {t.toDate}
                  </Label>
                  <Input
                    type="date"
                    className="h-12 rounded-2xl border-slate-200 tabular-nums"
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
                    <p className="text-xs font-medium text-slate-500">{t.startPreview}</p>
                    <p className="mt-1 text-sm font-bold text-slate-900 tabular-nums">
                      {form.start_date || "—"}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-slate-200/70">
                    <p className="text-xs font-medium text-slate-500">{t.endPreview}</p>
                    <p className="mt-1 text-sm font-bold text-slate-900 tabular-nums">
                      {form.end_date || "—"}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-slate-200/70">
                    <p className="text-xs font-medium text-slate-500">{t.leaveTypePreview}</p>
                    <p className="mt-1 truncate text-sm font-bold text-slate-900">
                      {leaveTypes.find(
                        (type) => String(type.id) === String(form.leave_type_id)
                      )?.name || "—"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-semibold text-slate-700">
                  {t.reason}
                </Label>
                <Textarea
                  value={form.reason}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      reason: e.target.value,
                    }))
                  }
                  placeholder={t.reasonPlaceholder}
                  className="min-h-[140px] rounded-2xl border-slate-200 bg-white text-sm"
                />
              </div>

              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={handleCreate}
                  disabled={submitting}
                  className="rounded-2xl px-5"
                >
                  {submitting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                  <span className={isArabic ? "mr-2" : "ml-2"}>
                    {t.createRequest}
                  </span>
                </Button>

                <Button
                  variant="outline"
                  className="rounded-2xl border-slate-200 px-5"
                  onClick={() => setForm(INITIAL_FORM)}
                  disabled={submitting}
                >
                  {t.reset}
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
                    {t.formHiddenTitle}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    {t.formHiddenDesc}
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
                {t.leaveBalances}
              </CardTitle>
              <CardDescription className="mt-1 text-sm text-slate-600">
                {t.leaveBalancesDesc}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              {balances.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
                  {t.noBalances}
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
                          {t.availableBalanceHint}
                        </p>
                      </div>
                      <Badge
                        variant="outline"
                        className="rounded-full border-primary/20 bg-primary/5 px-3 py-1 text-primary"
                      >
                        {formatNumber(item.balance, 1)} {t.days}
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
                {t.annualPolicy}
              </CardTitle>
              <CardDescription className="mt-1 text-sm text-slate-600">
                {t.annualPolicyDesc}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              {annualPolicy ? (
                <>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
                      <p className="text-xs font-medium text-slate-500">{t.annualDays}</p>
                      <p className="mt-2 text-2xl font-black text-slate-900 tabular-nums">
                        {typeof annualPolicy.annual_days === "number"
                          ? formatNumber(annualPolicy.annual_days)
                          : "—"}
                      </p>
                    </div>

                    <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
                      <p className="text-xs font-medium text-slate-500">
                        {t.maxCarryForward}
                      </p>
                      <p className="mt-2 text-2xl font-black text-slate-900 tabular-nums">
                        {typeof annualPolicy.max_carry_forward_days === "number"
                          ? formatNumber(annualPolicy.max_carry_forward_days)
                          : "—"}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-3xl border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-slate-600">
                        {t.accrual}
                      </span>
                      <Badge
                        variant="outline"
                        className={
                          annualPolicy.accrual_enabled
                            ? "rounded-full border-emerald-200 bg-emerald-50 text-emerald-700"
                            : "rounded-full border-slate-200 bg-slate-50 text-slate-700"
                        }
                      >
                        {annualPolicy.accrual_enabled ? t.enabled : t.disabled}
                      </Badge>
                    </div>
                  </div>

                  <div className="rounded-3xl border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-slate-600">
                        {t.carryForward}
                      </span>
                      <Badge
                        variant="outline"
                        className={
                          annualPolicy.carry_forward_enabled
                            ? "rounded-full border-emerald-200 bg-emerald-50 text-emerald-700"
                            : "rounded-full border-slate-200 bg-slate-50 text-slate-700"
                        }
                      >
                        {annualPolicy.carry_forward_enabled ? t.allowed : t.notAllowed}
                      </Badge>
                    </div>
                  </div>
                </>
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
                  {t.annualPolicyNotFound}
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
                {t.requestsList}
              </CardTitle>
              <CardDescription className="mt-2 text-sm leading-6 text-slate-600">
                {t.requestsListDesc}
              </CardDescription>
            </div>

            <div className="flex w-full flex-col gap-3 xl:flex-row 2xl:w-auto">
              <div className="relative min-w-[260px]">
                <Search
                  className={[
                    "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400",
                    isArabic ? "right-3" : "left-3",
                  ].join(" ")}
                />
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={t.searchPlaceholder}
                  className={[
                    "h-11 rounded-2xl border-slate-200",
                    isArabic ? "pr-10" : "pl-10",
                  ].join(" ")}
                />
              </div>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="h-11 min-w-[180px] rounded-2xl border-slate-200">
                  <SelectValue placeholder={t.allStatuses} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.allStatuses}</SelectItem>
                  <SelectItem value="pending">{t.pending}</SelectItem>
                  <SelectItem value="approved">{t.approved}</SelectItem>
                  <SelectItem value="rejected">{t.rejected}</SelectItem>
                  <SelectItem value="cancelled">{t.cancelled}</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                className="h-11 rounded-2xl border-slate-200"
                onClick={handlePrintRequests}
                disabled={printing}
              >
                {printing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Printer className="h-4 w-4" />
                )}
                <span className={isArabic ? "mr-2" : "ml-2"}>
                  {t.printRequests}
                </span>
              </Button>

              <Button
                variant="outline"
                className="h-11 rounded-2xl border-slate-200"
                onClick={handleExportExcel}
                disabled={exportingExcel}
              >
                {exportingExcel ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileSpreadsheet className="h-4 w-4" />
                )}
                <span className={isArabic ? "mr-2" : "ml-2"}>
                  {t.exportExcel}
                </span>
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="mb-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50/70 px-4 py-3">
              <p className="text-xs font-medium text-slate-500">{t.currentlyVisible}</p>
              <p className="mt-1 text-2xl font-black text-slate-900 tabular-nums">
                {formatNumber(filteredRequests.length)}
              </p>
            </div>
            <div className="rounded-2xl border border-amber-200 bg-amber-50/80 px-4 py-3">
              <p className="text-xs font-medium text-amber-700">{t.pending}</p>
              <p className="mt-1 text-2xl font-black text-amber-700 tabular-nums">
                {formatNumber(pendingVisibleCount)}
              </p>
            </div>
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/80 px-4 py-3">
              <p className="text-xs font-medium text-emerald-700">{t.approved}</p>
              <p className="mt-1 text-2xl font-black text-emerald-700 tabular-nums">
                {formatNumber(approvedVisibleCount)}
              </p>
            </div>
            <div className="rounded-2xl border border-rose-200 bg-rose-50/80 px-4 py-3">
              <p className="text-xs font-medium text-rose-700">{t.rejected}</p>
              <p className="mt-1 text-2xl font-black text-rose-700 tabular-nums">
                {formatNumber(rejectedVisibleCount)}
              </p>
            </div>
          </div>

          <Separator className="mb-5" />

          {loading ? (
            <div className="flex min-h-[320px] items-center justify-center">
              <div className="flex items-center gap-3 rounded-2xl border bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
                <Loader2 className="h-4 w-4 animate-spin" />
                {t.loadingLeaves}
              </div>
            </div>
          ) : filteredRequests.length === 0 ? (
            <div className="flex min-h-[320px] items-center justify-center rounded-[28px] border border-dashed border-slate-200 bg-slate-50/50 text-center">
              <div className="space-y-3 px-6">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-slate-500">
                  <CalendarDays className="h-7 w-7" />
                </div>
                <h3 className="text-xl font-black text-slate-900">
                  {t.noMatchingRequests}
                </h3>
                <p className="text-sm leading-6 text-slate-500">
                  {t.noMatchingRequestsDesc}
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className="hidden overflow-hidden rounded-[28px] border border-slate-200 lg:block">
                <Table>
                  <TableHeader className="bg-slate-50/90">
                    <TableRow className="hover:bg-slate-50/90">
                      <TableHead className="whitespace-nowrap font-bold">
                        #
                      </TableHead>
                      <TableHead className="whitespace-nowrap font-bold">
                        {t.employeeCol}
                      </TableHead>
                      <TableHead className="whitespace-nowrap font-bold">
                        {t.leaveTypeCol}
                      </TableHead>
                      <TableHead className="whitespace-nowrap font-bold">
                        {t.fromCol}
                      </TableHead>
                      <TableHead className="whitespace-nowrap font-bold">
                        {t.toCol}
                      </TableHead>
                      <TableHead className="whitespace-nowrap font-bold">
                        {t.statusCol}
                      </TableHead>
                      <TableHead
                        className={[
                          "whitespace-nowrap font-bold",
                          isArabic ? "text-left" : "text-right",
                        ].join(" ")}
                      >
                        {t.actionsCol}
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
                          <TableCell className="font-bold text-slate-700 tabular-nums">
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

                                  <span>
                                    {t.requestId}: #{item.id}
                                  </span>
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

                          <TableCell className="font-medium text-slate-700 tabular-nums">
                            {formatDate(item.from_date)}
                          </TableCell>

                          <TableCell className="font-medium text-slate-700 tabular-nums">
                            {formatDate(item.to_date)}
                          </TableCell>

                          <TableCell>
                            <Badge
                              variant="outline"
                              className={`rounded-full ${getStatusBadgeClass(item.status)}`}
                            >
                              {getStatusLabel(item.status, t)}
                            </Badge>
                          </TableCell>

                          <TableCell className={isArabic ? "text-left" : "text-right"}>
                            {String(item.status).toLowerCase() === "pending" ? (
                              <div
                                className={[
                                  "flex flex-wrap gap-2",
                                  isArabic ? "justify-start" : "justify-end",
                                ].join(" ")}
                              >
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
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <CheckCircle2 className="h-4 w-4" />
                                  )}
                                  <span className={isArabic ? "mr-2" : "ml-2"}>
                                    {t.approve}
                                  </span>
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
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                  ) : (
                                    <XCircle className="h-4 w-4" />
                                  )}
                                  <span className={isArabic ? "mr-2" : "ml-2"}>
                                    {t.reject}
                                  </span>
                                </Button>
                              </div>
                            ) : (
                              <div className={isArabic ? "flex justify-start" : "flex justify-end"}>
                                <Badge
                                  variant="outline"
                                  className="rounded-full border-slate-200 bg-slate-50 text-slate-600"
                                >
                                  {t.noActions}
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

              <div className="grid gap-4 lg:hidden">
                {filteredRequests.map((item) => {
                  const employeeInfo = item.employee_id
                    ? employeeMap.get(item.employee_id)
                    : null

                  return (
                    <div
                      key={item.id}
                      className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex min-w-0 flex-1 items-start gap-3">
                          <Avatar className="h-12 w-12 rounded-2xl border border-slate-200 shadow-sm">
                            <AvatarImage
                              src={employeeInfo?.avatar || ""}
                              alt={item.employee_name}
                            />
                            <AvatarFallback className="rounded-2xl bg-slate-100 font-semibold text-slate-700">
                              {getInitials(item.employee_name)}
                            </AvatarFallback>
                          </Avatar>

                          <div className="min-w-0">
                            <h3 className="truncate font-bold text-slate-900">
                              {item.employee_name}
                            </h3>
                            <p className="mt-1 text-xs text-slate-500">
                              {t.requestId}: #{item.id}
                            </p>
                          </div>
                        </div>

                        <Badge
                          variant="outline"
                          className={`rounded-full ${getStatusBadgeClass(item.status)}`}
                        >
                          {getStatusLabel(item.status, t)}
                        </Badge>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                        <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-3">
                          <p className="text-xs text-slate-500">{t.leaveTypeCol}</p>
                          <p className="mt-1 font-medium text-slate-900">{item.type}</p>
                        </div>

                        <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-3">
                          <p className="text-xs text-slate-500">{t.statusCol}</p>
                          <p className="mt-1 font-medium text-slate-900">
                            {getStatusLabel(item.status, t)}
                          </p>
                        </div>

                        <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-3">
                          <p className="text-xs text-slate-500">{t.fromCol}</p>
                          <p className="mt-1 font-medium text-slate-900 tabular-nums">
                            {formatDate(item.from_date)}
                          </p>
                        </div>

                        <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-3">
                          <p className="text-xs text-slate-500">{t.toCol}</p>
                          <p className="mt-1 font-medium text-slate-900 tabular-nums">
                            {formatDate(item.to_date)}
                          </p>
                        </div>
                      </div>

                      {(employeeInfo?.email || employeeInfo?.phone) && (
                        <div className="mt-4 flex flex-col gap-2 rounded-2xl border border-slate-200 bg-slate-50/40 p-3 text-xs text-slate-600">
                          {employeeInfo?.email ? <span>{employeeInfo.email}</span> : null}
                          {employeeInfo?.phone ? <span>{employeeInfo.phone}</span> : null}
                        </div>
                      )}

                      <div className="mt-4 flex flex-wrap gap-2">
                        {String(item.status).toLowerCase() === "pending" ? (
                          <>
                            <Button
                              className="flex-1 rounded-2xl"
                              onClick={() => handleAction(item.id, "approve")}
                              disabled={
                                isActionLoading(item.id, "approve") ||
                                isActionLoading(item.id, "reject")
                              }
                            >
                              {isActionLoading(item.id, "approve") ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <CheckCircle2 className="h-4 w-4" />
                              )}
                              <span className={isArabic ? "mr-2" : "ml-2"}>
                                {t.approve}
                              </span>
                            </Button>

                            <Button
                              variant="outline"
                              className="flex-1 rounded-2xl border-rose-200 text-rose-700 hover:bg-rose-50 hover:text-rose-800"
                              onClick={() => handleAction(item.id, "reject")}
                              disabled={
                                isActionLoading(item.id, "approve") ||
                                isActionLoading(item.id, "reject")
                              }
                            >
                              {isActionLoading(item.id, "reject") ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <XCircle className="h-4 w-4" />
                              )}
                              <span className={isArabic ? "mr-2" : "ml-2"}>
                                {t.reject}
                              </span>
                            </Button>
                          </>
                        ) : (
                          <div className="w-full">
                            <Badge
                              variant="outline"
                              className="rounded-full border-slate-200 bg-slate-50 text-slate-600"
                            >
                              {t.noActions}
                            </Badge>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}