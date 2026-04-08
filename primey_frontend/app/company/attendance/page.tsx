"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  BadgeCheck,
  Briefcase,
  Building2,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Cpu,
  FileSpreadsheet,
  Fingerprint,
  GitBranch,
  Loader2,
  LogIn,
  LogOut,
  PencilLine,
  RefreshCw,
  Search,
  ShieldCheck,
  TriangleAlert,
  UserCheck,
  Users,
  Workflow,
  Zap,
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
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

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim()?.replace(/\/+$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.trim()?.replace(/\/+$/, "") ||
  "http://localhost:8000"

const ATTENDANCE_MANUAL_ENTRY_API = "/api/company/attendance/manual-entry/"
const EMPLOYEE_SCHEDULE_PREVIEW_API = "/api/company/attendance/employee-schedule-preview/"

type Locale = "ar" | "en"
type ManualActionType = "check_in" | "check_out" | "both"

type EmployeeItem = {
  id: number
  full_name?: string
  name?: string
  department?: string | null
  job_title?: string | null
  status?: string | null
  biotime_code?: string | null
}

type DeviceItem = {
  id: number
  name?: string | null
  sn?: string | null
  ip?: string | null
  location?: string | null
  geo_location?: string | null
  status?: string | null
  users?: number | null
  last_activity?: string | null
}

type WorkScheduleItem = {
  id: number
  name?: string | null
  schedule_type?: string | null
  period1_start?: string | null
  period1_end?: string | null
  period2_start?: string | null
  period2_end?: string | null
  weekend_days?: string | null
  weekend_days_ar?: string | null
  target_daily_hours?: string | number | null
  allow_night_overlap?: boolean
  is_active?: boolean
}

type DashboardData = {
  today: {
    present: number
    absent: number
    late: number
    leave: number
  }
  total_records: number
}

type AttendanceRow = {
  employee: string
  employee_id: number
  photo_url?: string | null
  date: string
  status: string
  status_ar: string
  schedule_type?: string | null
  schedule_label?: string | null
  period_display?: string | null
  check_in?: string | null
  check_out?: string | null
  actual_hours?: number | null
  late_minutes?: number | null
  overtime_minutes?: number | null
  location?: string | null
}

type AttendancePolicy = {
  grace_minutes: number
  late_after_minutes: number
  absence_after_minutes: number
  auto_absent_if_no_checkin: boolean
  overtime_enabled?: boolean
}

type UnmappedLog = {
  id: number
  employee_code: string
  punch_time: string
  device_sn?: string | null
  terminal_alias?: string | null
  device_ip?: string | null
  raw_id?: string | number | null
}

type SchedulePreviewPeriod = {
  start: string
  end: string
}

type EmployeeSchedulePreview = {
  schedule_type: string | null
  periods: SchedulePreviewPeriod[]
  is_weekend: boolean
  target_daily_hours: string | null
}

type ManualEntryFormState = {
  employeeId: string
  date: string
  actionType: ManualActionType
  checkIn: string
  checkOut: string
}

type Dictionary = {
  headerBadge: string
  pageTitle: string
  pageDescription: string
  refresh: string
  syncDevices: string
  syncAttendance: string
  loadingPage: string

  todayPresent: string
  todayLate: string
  todayAbsent: string
  totalAttendanceRecords: string

  reportTitle: string
  reportDescription: string
  reportSearchPlaceholder: string
  refreshReport: string
  fromDate: string
  toDate: string
  status: string
  applyFilters: string
  allStatuses: string
  present: string
  late: string
  absent: string
  leave: string
  weekend: string
  employee: string
  date: string
  schedule: string
  checkIn: string
  checkOut: string
  workHours: string
  delay: string
  overtime: string
  location: string
  loadingReport: string
  noMatchingRows: string

  setupSummaryTitle: string
  setupSummaryDescription: string
  employees: string
  linkedToBiotime: string
  onlineDevices: string
  unmappedLogs: string
  attendancePolicyTitle: string
  attendancePolicyDescription: string
  graceMinutes: string
  lateAfterMinutes: string
  absenceAfterMinutes: string
  autoAbsentIfNoCheckin: string
  overtimeEnabled: string
  enabled: string
  disabled: string
  savePolicy: string

  unmappedLogsTitle: string
  unmappedLogsDescription: string
  hide: string
  employeeCode: string
  punchTime: string
  device: string
  deviceSn: string
  ipAddress: string
  rawId: string
  noUnmappedLogs: string

  readyEmployeesTitle: string
  readyEmployeesDescription: string
  employeesSearchPlaceholder: string
  department: string
  jobTitle: string
  biotime: string
  noMatchingEmployees: string

  biotimeDevicesTitle: string
  biotimeDevicesDescription: string
  usersCount: string
  noDevices: string
  supportiveMessage: string

  schedulesTitle: string
  schedulesDescription: string
  noSchedules: string
  periods: string
  weeklyWeekend: string
  active: string
  inactive: string

  operationalTitle: string
  operationalDescription: string
  pageStructure: string
  pageStructureDescription: string
  workSchedules: string
  linkedEmployees: string

  unknown: string
  notLinked: string
  activeStatus: string
  inactiveStatus: string
  online: string
  offline: string
  minutesSuffix: string
  hoursRequired: string

  syncDevicesSuccess: string
  syncAttendanceSuccess: string
  savePolicySuccess: string
  loadPageError: string
  loadReportError: string
  savePolicyError: string
  syncDevicesError: string
  syncAttendanceError: string

  manualEntryButton: string
  manualEntryTitle: string
  manualEntryDescription: string
  manualEntryEmployee: string
  manualEntrySelectEmployee: string
  manualEntryEmployeeSearch: string
  manualEntryActionType: string
  manualEntryCheckInOnly: string
  manualEntryCheckOutOnly: string
  manualEntryBoth: string
  manualEntryTime: string
  manualEntryDate: string
  manualEntrySchedulePreview: string
  manualEntryNoSchedule: string
  manualEntryWeekend: string
  manualEntryWorkingDay: string
  manualEntrySave: string
  manualEntrySaving: string
  manualEntryCancel: string
  manualEntrySuccess: string
  manualEntryError: string
  manualEntrySelectEmployeeFirst: string
  manualEntrySelectDateFirst: string
  manualEntryCheckInRequired: string
  manualEntryCheckOutRequired: string
  manualEntryLoadScheduleError: string
  manualEntryTypeLabel: string
  manualEntryPeriodsLabel: string
  manualEntryTargetHoursLabel: string
  manualEntryNoPeriods: string
}

const translations: Record<Locale, Dictionary> = {
  ar: {
    headerBadge: "مركز حضور الشركة",
    pageTitle: "إدارة الحضور والانصراف",
    pageDescription:
      "صفحة حضور وانصراف احترافية مرتبطة بالبيانات الفعلية، مع الحفاظ على الهوية الداخلية الموحدة للبطاقات والجداول والأزرار.",
    refresh: "تحديث",
    syncDevices: "مزامنة الأجهزة",
    syncAttendance: "مزامنة الحضور",
    loadingPage: "جاري تحميل صفحة الحضور...",

    todayPresent: "الحضور اليوم",
    todayLate: "المتأخرون اليوم",
    todayAbsent: "الغياب اليوم",
    totalAttendanceRecords: "إجمالي السجلات",

    reportTitle: "تقرير سجلات الحضور",
    reportDescription: "معاينة مباشرة لسجلات الحضور والانصراف الفعلية مع البحث والفلاتر.",
    reportSearchPlaceholder: "بحث باسم الموظف أو الحالة أو الموقع",
    refreshReport: "تحديث التقرير",
    fromDate: "من تاريخ",
    toDate: "إلى تاريخ",
    status: "الحالة",
    applyFilters: "تطبيق الفلاتر",
    allStatuses: "كل الحالات",
    present: "حاضر",
    late: "متأخر",
    absent: "غائب",
    leave: "إجازة",
    weekend: "عطلة",
    employee: "الموظف",
    date: "التاريخ",
    schedule: "الجدول",
    checkIn: "الدخول",
    checkOut: "الخروج",
    workHours: "ساعات العمل",
    delay: "التأخير",
    overtime: "الإضافي",
    location: "الموقع",
    loadingReport: "جاري تحميل التقرير...",
    noMatchingRows: "لا توجد بيانات مطابقة للفلاتر الحالية.",

    setupSummaryTitle: "ملخص الربط والتجهيز",
    setupSummaryDescription: "نظرة سريعة على جاهزية بيئة الحضور داخل الشركة.",
    employees: "الموظفون",
    linkedToBiotime: "مربوطون بـ BioTime",
    onlineDevices: "أجهزة أونلاين",
    unmappedLogs: "سجلات غير مربوطة",
    attendancePolicyTitle: "سياسة الحضور",
    attendancePolicyDescription: "تعديل إعدادات التأخير والغياب وسياسة الحضور للشركة.",
    graceMinutes: "Grace Minutes",
    lateAfterMinutes: "Late After Minutes",
    absenceAfterMinutes: "Absence After Minutes",
    autoAbsentIfNoCheckin: "Auto Absent If No Check-in",
    overtimeEnabled: "Overtime Enabled",
    enabled: "ON",
    disabled: "OFF",
    savePolicy: "حفظ السياسة",

    unmappedLogsTitle: "السجلات غير المربوطة",
    unmappedLogsDescription: "هذه السجلات وصلت من BioTime لكنها غير مرتبطة بموظف داخل النظام.",
    hide: "إخفاء",
    employeeCode: "Employee Code",
    punchTime: "وقت الحركة",
    device: "الجهاز",
    deviceSn: "SN",
    ipAddress: "IP",
    rawId: "Raw ID",
    noUnmappedLogs: "لا توجد سجلات غير مربوطة حاليًا.",

    readyEmployeesTitle: "الموظفون الجاهزون للحضور",
    readyEmployeesDescription: "عرض سريع للموظفين وربطهم الحالي مع BioTime.",
    employeesSearchPlaceholder: "بحث في الموظفين",
    department: "القسم",
    jobTitle: "الوظيفة",
    biotime: "BioTime",
    noMatchingEmployees: "لا توجد بيانات مطابقة.",

    biotimeDevicesTitle: "أجهزة BioTime",
    biotimeDevicesDescription: "ملخص سريع لأجهزة الشركة وحالتها الحالية.",
    usersCount: "المستخدمون",
    noDevices: "لا توجد أجهزة مرتبطة حاليًا.",
    supportiveMessage:
      "هذه الصفحة مربوطة بتقرير الحضور الفعلي وسجلات الشركة الحقيقية، مع الإبقاء على بيانات BioTime والأجهزة كعناصر مساندة داخل نفس الصفحة.",

    schedulesTitle: "جداول الدوام المعتمدة",
    schedulesDescription: "عرض سريع لسياسات وجداول الدوام الموجودة فعليًا في النظام.",
    noSchedules: "لا توجد جداول دوام حاليًا.",
    periods: "الفترات",
    weeklyWeekend: "الإجازة الأسبوعية",
    active: "نشط",
    inactive: "معطل",

    operationalTitle: "ملخص البنية التشغيلية",
    operationalDescription: "المكونات المتاحة الآن التي تعتمد عليها صفحة الحضور.",
    pageStructure: "بنية الصفحة الحالية",
    pageStructureDescription:
      "الصفحة تعتمد على Dashboard الحضور الحقيقي، تقرير السجلات الفعلي، سياسة الحضور، الأجهزة، الموظفين، وجداول الدوام.",
    workSchedules: "جداول الدوام",
    linkedEmployees: "موظفون مربوطون",

    unknown: "—",
    notLinked: "غير مربوط",
    activeStatus: "نشط",
    inactiveStatus: "معطل",
    online: "Online",
    offline: "Offline",
    minutesSuffix: "د",
    hoursRequired: "ساعات مطلوبة",

    syncDevicesSuccess: "تمت مزامنة أجهزة BioTime بنجاح",
    syncAttendanceSuccess: "تمت مزامنة الحضور بنجاح",
    savePolicySuccess: "تم حفظ سياسة الحضور بنجاح",
    loadPageError: "فشل تحميل صفحة الحضور",
    loadReportError: "فشل تحميل تقرير الحضور",
    savePolicyError: "فشل حفظ سياسة الحضور",
    syncDevicesError: "فشلت مزامنة الأجهزة",
    syncAttendanceError: "فشلت مزامنة الحضور",

    manualEntryButton: "إدخال حركة",
    manualEntryTitle: "إدخال حركة حضور يدويًا",
    manualEntryDescription:
      "استخدم هذه النافذة لتسجيل حركة دخول أو خروج رسمية للموظف عند فقدان البصمة أو الحاجة إلى تصحيح الحركة.",
    manualEntryEmployee: "الموظف",
    manualEntrySelectEmployee: "اختر الموظف",
    manualEntryEmployeeSearch: "ابحث باسم الموظف",
    manualEntryActionType: "نوع الحركة",
    manualEntryCheckInOnly: "دخول فقط",
    manualEntryCheckOutOnly: "خروج فقط",
    manualEntryBoth: "دخول وخروج",
    manualEntryTime: "الوقت",
    manualEntryDate: "تاريخ الحركة",
    manualEntrySchedulePreview: "معاينة الجدول",
    manualEntryNoSchedule: "لا يوجد جدول دوام مربوط لهذا الموظف في هذا التاريخ.",
    manualEntryWeekend: "اليوم عطلة أسبوعية",
    manualEntryWorkingDay: "يوم عمل",
    manualEntrySave: "حفظ الحركة",
    manualEntrySaving: "جارٍ الحفظ...",
    manualEntryCancel: "إلغاء",
    manualEntrySuccess: "تم حفظ الحركة اليدوية بنجاح",
    manualEntryError: "فشل حفظ الحركة اليدوية",
    manualEntrySelectEmployeeFirst: "اختر الموظف أولًا",
    manualEntrySelectDateFirst: "اختر التاريخ أولًا",
    manualEntryCheckInRequired: "وقت الدخول مطلوب",
    manualEntryCheckOutRequired: "وقت الخروج مطلوب",
    manualEntryLoadScheduleError: "تعذر تحميل جدول دوام الموظف",
    manualEntryTypeLabel: "نوع الدوام",
    manualEntryPeriodsLabel: "الفترات",
    manualEntryTargetHoursLabel: "الساعات المطلوبة",
    manualEntryNoPeriods: "لا توجد فترات ثابتة لهذا الجدول",
  },
  en: {
    headerBadge: "Company Attendance Center",
    pageTitle: "Attendance Management",
    pageDescription:
      "A professional attendance page connected to real attendance data while preserving the unified internal UI for cards, tables, and buttons.",
    refresh: "Refresh",
    syncDevices: "Sync Devices",
    syncAttendance: "Sync Attendance",
    loadingPage: "Loading attendance page...",

    todayPresent: "Present Today",
    todayLate: "Late Today",
    todayAbsent: "Absent Today",
    totalAttendanceRecords: "Total Records",

    reportTitle: "Attendance Report",
    reportDescription: "Live preview of actual attendance records with search and filters.",
    reportSearchPlaceholder: "Search by employee, status, or location",
    refreshReport: "Refresh Report",
    fromDate: "From Date",
    toDate: "To Date",
    status: "Status",
    applyFilters: "Apply Filters",
    allStatuses: "All Statuses",
    present: "Present",
    late: "Late",
    absent: "Absent",
    leave: "Leave",
    weekend: "Weekend",
    employee: "Employee",
    date: "Date",
    schedule: "Schedule",
    checkIn: "Check-in",
    checkOut: "Check-out",
    workHours: "Work Hours",
    delay: "Delay",
    overtime: "Overtime",
    location: "Location",
    loadingReport: "Loading report...",
    noMatchingRows: "No data matches the current filters.",

    setupSummaryTitle: "Readiness Summary",
    setupSummaryDescription: "Quick overview of the attendance environment inside the company.",
    employees: "Employees",
    linkedToBiotime: "Linked to BioTime",
    onlineDevices: "Online Devices",
    unmappedLogs: "Unmapped Logs",
    attendancePolicyTitle: "Attendance Policy",
    attendancePolicyDescription: "Adjust lateness, absence, and attendance policy settings.",
    graceMinutes: "Grace Minutes",
    lateAfterMinutes: "Late After Minutes",
    absenceAfterMinutes: "Absence After Minutes",
    autoAbsentIfNoCheckin: "Auto Absent If No Check-in",
    overtimeEnabled: "Overtime Enabled",
    enabled: "ON",
    disabled: "OFF",
    savePolicy: "Save Policy",

    unmappedLogsTitle: "Unmapped Logs",
    unmappedLogsDescription: "These records came from BioTime but are not linked to any employee.",
    hide: "Hide",
    employeeCode: "Employee Code",
    punchTime: "Punch Time",
    device: "Device",
    deviceSn: "SN",
    ipAddress: "IP",
    rawId: "Raw ID",
    noUnmappedLogs: "There are no unmapped logs right now.",

    readyEmployeesTitle: "Attendance-Ready Employees",
    readyEmployeesDescription: "Quick overview of employees and their current BioTime linkage.",
    employeesSearchPlaceholder: "Search employees",
    department: "Department",
    jobTitle: "Job Title",
    biotime: "BioTime",
    noMatchingEmployees: "No matching data found.",

    biotimeDevicesTitle: "BioTime Devices",
    biotimeDevicesDescription: "Quick summary of company devices and their current status.",
    usersCount: "Users",
    noDevices: "No linked devices available right now.",
    supportiveMessage:
      "This page is connected to the real attendance report and company records while keeping BioTime and device data as supporting sections within the same page.",

    schedulesTitle: "Approved Work Schedules",
    schedulesDescription: "Quick overview of the actual work schedules configured in the system.",
    noSchedules: "No work schedules available right now.",
    periods: "Periods",
    weeklyWeekend: "Weekly Weekend",
    active: "Active",
    inactive: "Inactive",

    operationalTitle: "Operational Structure Summary",
    operationalDescription: "The available components currently powering this attendance page.",
    pageStructure: "Current Page Structure",
    pageStructureDescription:
      "This page currently depends on the real attendance dashboard, actual records report, attendance policy, devices, employees, and work schedules.",
    workSchedules: "Work Schedules",
    linkedEmployees: "Linked Employees",

    unknown: "—",
    notLinked: "Not Linked",
    activeStatus: "Active",
    inactiveStatus: "Inactive",
    online: "Online",
    offline: "Offline",
    minutesSuffix: "m",
    hoursRequired: "required hours",

    syncDevicesSuccess: "BioTime devices synchronized successfully",
    syncAttendanceSuccess: "Attendance synchronized successfully",
    savePolicySuccess: "Attendance policy saved successfully",
    loadPageError: "Failed to load attendance page",
    loadReportError: "Failed to load attendance report",
    savePolicyError: "Failed to save attendance policy",
    syncDevicesError: "Failed to synchronize devices",
    syncAttendanceError: "Failed to synchronize attendance",

    manualEntryButton: "Manual Entry",
    manualEntryTitle: "Manual Attendance Entry",
    manualEntryDescription:
      "Use this dialog to register an official employee check-in or check-out when a punch was missed or needs correction.",
    manualEntryEmployee: "Employee",
    manualEntrySelectEmployee: "Select employee",
    manualEntryEmployeeSearch: "Search employee by name",
    manualEntryActionType: "Action Type",
    manualEntryCheckInOnly: "Check-in only",
    manualEntryCheckOutOnly: "Check-out only",
    manualEntryBoth: "Check-in and Check-out",
    manualEntryTime: "Time",
    manualEntryDate: "Attendance Date",
    manualEntrySchedulePreview: "Schedule Preview",
    manualEntryNoSchedule: "No work schedule is linked for this employee on this date.",
    manualEntryWeekend: "Weekend",
    manualEntryWorkingDay: "Working day",
    manualEntrySave: "Save Entry",
    manualEntrySaving: "Saving...",
    manualEntryCancel: "Cancel",
    manualEntrySuccess: "Manual attendance entry saved successfully",
    manualEntryError: "Failed to save manual attendance entry",
    manualEntrySelectEmployeeFirst: "Please select an employee first",
    manualEntrySelectDateFirst: "Please select a date first",
    manualEntryCheckInRequired: "Check-in time is required",
    manualEntryCheckOutRequired: "Check-out time is required",
    manualEntryLoadScheduleError: "Unable to load employee schedule preview",
    manualEntryTypeLabel: "Schedule Type",
    manualEntryPeriodsLabel: "Periods",
    manualEntryTargetHoursLabel: "Target Hours",
    manualEntryNoPeriods: "No fixed periods for this schedule",
  },
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

function formatNumber(value?: number | string | null) {
  if (value === null || value === undefined || value === "") return "0"

  const numericValue =
    typeof value === "number" ? value : Number(String(value).replace(/,/g, ""))

  if (Number.isNaN(numericValue)) {
    return String(value)
  }

  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
  }).format(numericValue)
}

function formatDecimal(value?: number | string | null, fractionDigits = 2) {
  if (value === null || value === undefined || value === "") return "0"

  const numericValue =
    typeof value === "number" ? value : Number(String(value).replace(/,/g, ""))

  if (Number.isNaN(numericValue)) {
    return String(value)
  }

  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
    minimumFractionDigits: 0,
    maximumFractionDigits: fractionDigits,
  }).format(numericValue)
}

function formatTime(value?: string | null) {
  if (!value) return "—"
  return String(value).slice(0, 5)
}

function formatDate(value?: string | null) {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  return date.toLocaleDateString("en-CA")
}

function formatDateTime(value?: string | null) {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  return `${date.toLocaleDateString("en-CA")} ${date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  })}`
}

function getStatusBadgeClass(status?: string | null) {
  const key = String(status || "").toLowerCase()

  if (["active", "present", "online", "success", "linked"].includes(key)) {
    return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300"
  }

  if (["late", "warning", "pending", "unlinked"].includes(key)) {
    return "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-300"
  }

  if (["leave", "weekend", "before_start"].includes(key)) {
    return "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900/50 dark:bg-sky-950/40 dark:text-sky-300"
  }

  if (["inactive", "offline", "failed", "error", "absent", "terminated"].includes(key)) {
    return "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300"
  }

  return "border-border bg-muted text-foreground"
}

function getLocalizedStatusLabel(
  status?: string | null,
  statusAr?: string | null,
  locale: Locale = "ar"
) {
  const key = String(status || "").toLowerCase()
  const arValue = String(statusAr || "").trim()

  const labels: Record<
    string,
    {
      ar: string
      en: string
    }
  > = {
    present: { ar: "حاضر", en: "Present" },
    late: { ar: "متأخر", en: "Late" },
    absent: { ar: "غائب", en: "Absent" },
    leave: { ar: "إجازة", en: "Leave" },
    weekend: { ar: "عطلة", en: "Weekend" },
    before_start: { ar: "قبل المباشرة", en: "Before Start" },
    terminated: { ar: "منتهي خدمة", en: "Terminated" },
    active: { ar: "نشط", en: "Active" },
    inactive: { ar: "معطل", en: "Inactive" },
    online: { ar: "متصل", en: "Online" },
    offline: { ar: "غير متصل", en: "Offline" },
    success: { ar: "ناجح", en: "Success" },
    failed: { ar: "فشل", en: "Failed" },
    error: { ar: "خطأ", en: "Error" },
    warning: { ar: "تحذير", en: "Warning" },
    linked: { ar: "مربوط", en: "Linked" },
    unlinked: { ar: "غير مربوط", en: "Unlinked" },
  }

  if (locale === "ar") {
    if (arValue && !labels[arValue.toLowerCase()]) {
      return arValue
    }
    return labels[key]?.ar || arValue || status || "—"
  }

  return labels[key]?.en || status || "—"
}

function getScheduleTypeLabel(type?: string | null, locale: Locale = "ar") {
  const value = String(type || "").toUpperCase()

  if (locale === "ar") {
    if (value === "FULL_TIME") return "دوام كامل"
    if (value === "PART_TIME") return "فترتين"
    if (value === "HOURLY") return "بالساعات"
  } else {
    if (value === "FULL_TIME") return "Full Time"
    if (value === "PART_TIME") return "Two Shifts"
    if (value === "HOURLY") return "Hourly"
  }

  return type || "—"
}

function buildSchedulePeriods(schedule: WorkScheduleItem, locale: Locale, t: Dictionary) {
  const periods: string[] = []

  if (schedule.period1_start && schedule.period1_end) {
    periods.push(`${formatTime(schedule.period1_start)} → ${formatTime(schedule.period1_end)}`)
  }

  if (schedule.period2_start && schedule.period2_end) {
    periods.push(`${formatTime(schedule.period2_start)} → ${formatTime(schedule.period2_end)}`)
  }

  if (periods.length > 0) return periods.join(" | ")

  if (schedule.schedule_type === "HOURLY" && schedule.target_daily_hours) {
    return `${formatDecimal(schedule.target_daily_hours)} ${t.hoursRequired}`
  }

  return "—"
}

function SummaryCard({
  title,
  value,
  icon,
  tone = "default",
}: {
  title: string
  value: string | number
  icon: React.ReactNode
  tone?: "default" | "emerald" | "amber" | "rose" | "sky"
}) {
  const toneClasses: Record<string, string> = {
    default: "bg-muted/40 text-foreground",
    emerald: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300",
    amber: "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300",
    rose: "bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300",
    sky: "bg-sky-50 text-sky-700 dark:bg-sky-950/30 dark:text-sky-300",
  }

  return (
    <Card className="border-border/60 rounded-2xl">
      <CardContent className="flex items-center justify-between p-5">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-3xl font-semibold tabular-nums">{formatNumber(value)}</p>
        </div>

        <div className={`rounded-2xl border p-3 ${toneClasses[tone]}`}>{icon}</div>
      </CardContent>
    </Card>
  )
}

function TogglePolicyRow({
  active,
  onClick,
  icon,
  label,
  enabledLabel,
  disabledLabel,
  tone,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
  enabledLabel: string
  disabledLabel: string
  tone: "emerald" | "sky"
}) {
  const activeClasses =
    tone === "emerald"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300"
      : "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900/50 dark:bg-sky-950/30 dark:text-sky-300"

  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      className={`h-auto w-full justify-between rounded-2xl px-4 py-3 text-sm font-medium ${
        active ? activeClasses : "border-border bg-background text-foreground"
      }`}
    >
      <span className="flex items-center gap-2">
        {icon}
        {label}
      </span>
      <span>{active ? enabledLabel : disabledLabel}</span>
    </Button>
  )
}

export default function CompanyAttendancePage() {
  const [locale, setLocale] = useState<Locale>("en")
  const [employees, setEmployees] = useState<EmployeeItem[]>([])
  const [devices, setDevices] = useState<DeviceItem[]>([])
  const [workSchedules, setWorkSchedules] = useState<WorkScheduleItem[]>([])
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [rows, setRows] = useState<AttendanceRow[]>([])
  const [policy, setPolicy] = useState<AttendancePolicy>({
    grace_minutes: 15,
    late_after_minutes: 30,
    absence_after_minutes: 180,
    auto_absent_if_no_checkin: true,
    overtime_enabled: true,
  })
  const [unmappedLogs, setUnmappedLogs] = useState<UnmappedLog[]>([])

  const [loadingPage, setLoadingPage] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [syncingDevices, setSyncingDevices] = useState(false)
  const [syncingAttendance, setSyncingAttendance] = useState(false)
  const [loadingRows, setLoadingRows] = useState(false)
  const [savingPolicy, setSavingPolicy] = useState(false)

  const [reportSearch, setReportSearch] = useState("")
  const [employeeSearch, setEmployeeSearch] = useState("")
  const [fromDate, setFromDate] = useState("")
  const [toDate, setToDate] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [showUnmapped, setShowUnmapped] = useState(false)

  const [manualEntryOpen, setManualEntryOpen] = useState(false)
  const [manualEntryEmployeeSearch, setManualEntryEmployeeSearch] = useState("")
  const [manualEntryLoading, setManualEntryLoading] = useState(false)
  const [loadingSchedulePreview, setLoadingSchedulePreview] = useState(false)
  const [schedulePreview, setSchedulePreview] = useState<EmployeeSchedulePreview | null>(null)
  const [manualEntryForm, setManualEntryForm] = useState<ManualEntryFormState>({
    employeeId: "",
    date: "",
    actionType: "both",
    checkIn: "",
    checkOut: "",
  })

  const today = useMemo(() => new Date().toLocaleDateString("en-CA"), [])
  const isArabic = locale === "ar"
  const dir = isArabic ? "rtl" : "ltr"
  const t = translations[locale]

  useEffect(() => {
    setFromDate(today)
    setToDate(today)
    setManualEntryForm((prev) => ({
      ...prev,
      date: today,
    }))
  }, [today])

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

  const fetchJson = useCallback(async (path: string, init?: RequestInit) => {
    const response = await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers || {}),
      },
      cache: "no-store",
      ...init,
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data?.message || data?.error || "Request failed")
    }

    return data
  }, [])

  const loadEmployees = useCallback(async () => {
    const data = await fetchJson("/api/company/employees/")
    setEmployees(Array.isArray(data?.employees) ? data.employees : [])
  }, [fetchJson])

  const loadDevices = useCallback(async () => {
    const data = await fetchJson("/api/company/biotime/devices/")
    setDevices(Array.isArray(data?.devices) ? data.devices : [])
  }, [fetchJson])

  const loadWorkSchedules = useCallback(async () => {
    const data = await fetchJson("/api/company/work-schedules/")
    setWorkSchedules(Array.isArray(data?.schedules) ? data.schedules : [])
  }, [fetchJson])

  const loadDashboard = useCallback(async () => {
    const data = await fetchJson("/api/company/attendance/dashboard/")
    setDashboard(data?.data || null)
  }, [fetchJson])

  const loadPolicy = useCallback(async () => {
    const data = await fetchJson("/api/company/attendance/policy/")
    if (data?.policy) {
      setPolicy({
        grace_minutes: Number(data.policy.grace_minutes ?? 15),
        late_after_minutes: Number(data.policy.late_after_minutes ?? 30),
        absence_after_minutes: Number(data.policy.absence_after_minutes ?? 180),
        auto_absent_if_no_checkin: Boolean(data.policy.auto_absent_if_no_checkin),
        overtime_enabled: Boolean(data.policy.overtime_enabled ?? true),
      })
    }
  }, [fetchJson])

  const loadUnmappedLogs = useCallback(async () => {
    const data = await fetchJson("/api/company/attendance/unmapped-logs/")
    setUnmappedLogs(Array.isArray(data?.records) ? data.records : [])
  }, [fetchJson])

  const loadRows = useCallback(async () => {
    setLoadingRows(true)
    try {
      const params = new URLSearchParams()

      if (fromDate) params.set("from_date", fromDate)
      if (toDate) params.set("to_date", toDate)
      if (statusFilter && statusFilter !== "all") params.set("status", statusFilter)

      const data = await fetchJson(`/api/company/attendance/reports/preview/?${params.toString()}`)
      setRows(Array.isArray(data?.rows) ? data.rows : [])
    } catch (error) {
      console.error("Attendance report load error:", error)
      toast.error(error instanceof Error ? error.message : t.loadReportError)
    } finally {
      setLoadingRows(false)
    }
  }, [fetchJson, fromDate, toDate, statusFilter, t.loadReportError])

  const loadAll = useCallback(
    async (silent = false) => {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoadingPage(true)
      }

      try {
        await Promise.all([
          loadEmployees(),
          loadDevices(),
          loadWorkSchedules(),
          loadDashboard(),
          loadPolicy(),
          loadUnmappedLogs(),
          loadRows(),
        ])
      } catch (error) {
        console.error("Attendance page load error:", error)
        toast.error(error instanceof Error ? error.message : t.loadPageError)
      } finally {
        setLoadingPage(false)
        setRefreshing(false)
      }
    },
    [
      loadDashboard,
      loadDevices,
      loadEmployees,
      loadPolicy,
      loadRows,
      loadUnmappedLogs,
      loadWorkSchedules,
      t.loadPageError,
    ]
  )

  useEffect(() => {
    if (!fromDate || !toDate) return
    void loadAll()
  }, [fromDate, toDate, loadAll])

  const handleSyncDevices = async () => {
    setSyncingDevices(true)
    try {
      const data = await fetchJson("/api/company/biotime/devices/sync/", {
        method: "POST",
      })

      toast.success(data?.message || t.syncDevicesSuccess)
      await loadAll(true)
    } catch (error) {
      console.error("BioTime device sync error:", error)
      toast.error(error instanceof Error ? error.message : t.syncDevicesError)
    } finally {
      setSyncingDevices(false)
    }
  }

  const handleAttendanceSync = async () => {
    setSyncingAttendance(true)
    try {
      const data = await fetchJson("/api/company/attendance/sync/", {
        method: "POST",
      })

      toast.success(data?.message || t.syncAttendanceSuccess)
      await Promise.all([loadDashboard(), loadRows(), loadUnmappedLogs()])
    } catch (error) {
      console.error("Attendance sync error:", error)
      toast.error(error instanceof Error ? error.message : t.syncAttendanceError)
    } finally {
      setSyncingAttendance(false)
    }
  }

  const handleSavePolicy = async () => {
    setSavingPolicy(true)
    try {
      const data = await fetchJson("/api/company/attendance/policy/", {
        method: "PATCH",
        body: JSON.stringify(policy),
      })

      if (data?.policy) {
        setPolicy({
          grace_minutes: Number(data.policy.grace_minutes ?? 15),
          late_after_minutes: Number(data.policy.late_after_minutes ?? 30),
          absence_after_minutes: Number(data.policy.absence_after_minutes ?? 180),
          auto_absent_if_no_checkin: Boolean(data.policy.auto_absent_if_no_checkin),
          overtime_enabled: Boolean(data.policy.overtime_enabled ?? true),
        })
      }

      toast.success(t.savePolicySuccess)
    } catch (error) {
      console.error("Attendance policy save error:", error)
      toast.error(error instanceof Error ? error.message : t.savePolicyError)
    } finally {
      setSavingPolicy(false)
    }
  }

  const resetManualEntryForm = useCallback(() => {
    setManualEntryEmployeeSearch("")
    setSchedulePreview(null)
    setManualEntryForm({
      employeeId: "",
      date: today,
      actionType: "both",
      checkIn: "",
      checkOut: "",
    })
  }, [today])

  const loadEmployeeSchedulePreview = useCallback(
    async (employeeId: string, workDate: string) => {
      if (!employeeId) {
        setSchedulePreview(null)
        return
      }

      if (!workDate) {
        setSchedulePreview(null)
        return
      }

      setLoadingSchedulePreview(true)
      try {
        const params = new URLSearchParams({
          employee_id: employeeId,
          date: workDate,
        })

        const data = await fetchJson(
          `${EMPLOYEE_SCHEDULE_PREVIEW_API}?${params.toString()}`
        )

        setSchedulePreview({
          schedule_type: data?.schedule_type ?? null,
          periods: Array.isArray(data?.periods) ? data.periods : [],
          is_weekend: Boolean(data?.is_weekend),
          target_daily_hours: data?.target_daily_hours
            ? String(data.target_daily_hours)
            : null,
        })
      } catch (error) {
        console.error("Employee schedule preview load error:", error)
        setSchedulePreview(null)
        toast.error(error instanceof Error ? error.message : t.manualEntryLoadScheduleError)
      } finally {
        setLoadingSchedulePreview(false)
      }
    },
    [fetchJson, t.manualEntryLoadScheduleError]
  )

  useEffect(() => {
    if (!manualEntryOpen) return
    if (!manualEntryForm.employeeId || !manualEntryForm.date) {
      setSchedulePreview(null)
      return
    }

    void loadEmployeeSchedulePreview(manualEntryForm.employeeId, manualEntryForm.date)
  }, [
    manualEntryForm.employeeId,
    manualEntryForm.date,
    manualEntryOpen,
    loadEmployeeSchedulePreview,
  ])

  const handleOpenManualEntry = () => {
    resetManualEntryForm()
    setManualEntryOpen(true)
  }

  const handleCloseManualEntry = () => {
    setManualEntryOpen(false)
    resetManualEntryForm()
  }

  const handleSubmitManualEntry = async () => {
    if (!manualEntryForm.employeeId) {
      toast.error(t.manualEntrySelectEmployeeFirst)
      return
    }

    if (!manualEntryForm.date) {
      toast.error(t.manualEntrySelectDateFirst)
      return
    }

    if (
      (manualEntryForm.actionType === "check_in" || manualEntryForm.actionType === "both") &&
      !manualEntryForm.checkIn
    ) {
      toast.error(t.manualEntryCheckInRequired)
      return
    }

    if (
      (manualEntryForm.actionType === "check_out" || manualEntryForm.actionType === "both") &&
      !manualEntryForm.checkOut
    ) {
      toast.error(t.manualEntryCheckOutRequired)
      return
    }

    const payload: Record<string, unknown> = {
      employee_id: Number(manualEntryForm.employeeId),
      date: manualEntryForm.date,
    }

    if (manualEntryForm.actionType === "check_in" || manualEntryForm.actionType === "both") {
      payload.check_in = manualEntryForm.checkIn
    }

    if (manualEntryForm.actionType === "check_out" || manualEntryForm.actionType === "both") {
      payload.check_out = manualEntryForm.checkOut
    }

    setManualEntryLoading(true)
    try {
      const data = await fetchJson(ATTENDANCE_MANUAL_ENTRY_API, {
        method: "POST",
        body: JSON.stringify(payload),
      })

      toast.success(data?.message || t.manualEntrySuccess)

      handleCloseManualEntry()
      await Promise.all([loadDashboard(), loadRows()])
    } catch (error) {
      console.error("Manual attendance entry error:", error)
      toast.error(error instanceof Error ? error.message : t.manualEntryError)
    } finally {
      setManualEntryLoading(false)
    }
  }

  const filteredEmployees = useMemo(() => {
    const query = employeeSearch.trim().toLowerCase()
    if (!query) return employees

    return employees.filter((emp) => {
      return (
        String(emp.full_name || emp.name || "").toLowerCase().includes(query) ||
        String(emp.department || "").toLowerCase().includes(query) ||
        String(emp.job_title || "").toLowerCase().includes(query) ||
        String(emp.biotime_code || "").toLowerCase().includes(query)
      )
    })
  }, [employeeSearch, employees])

  const manualEntryFilteredEmployees = useMemo(() => {
    const query = manualEntryEmployeeSearch.trim().toLowerCase()
    if (!query) return employees

    return employees.filter((emp) => {
      return (
        String(emp.full_name || emp.name || "").toLowerCase().includes(query) ||
        String(emp.department || "").toLowerCase().includes(query) ||
        String(emp.job_title || "").toLowerCase().includes(query) ||
        String(emp.biotime_code || "").toLowerCase().includes(query)
      )
    })
  }, [employees, manualEntryEmployeeSearch])

  const filteredRows = useMemo(() => {
    const query = reportSearch.trim().toLowerCase()
    if (!query) return rows

    return rows.filter((row) => {
      return (
        String(row.employee || "").toLowerCase().includes(query) ||
        String(getLocalizedStatusLabel(row.status, row.status_ar, locale)).toLowerCase().includes(query) ||
        String(row.status || "").toLowerCase().includes(query) ||
        String(row.schedule_label || "").toLowerCase().includes(query) ||
        String(row.location || "").toLowerCase().includes(query)
      )
    })
  }, [reportSearch, rows, locale])

  const selectedManualEmployee = useMemo(() => {
    return employees.find((emp) => String(emp.id) === manualEntryForm.employeeId) || null
  }, [employees, manualEntryForm.employeeId])

  const manualEntryPeriodsText = useMemo(() => {
    if (!schedulePreview) return t.unknown
    if (!schedulePreview.periods.length) return t.manualEntryNoPeriods

    return schedulePreview.periods
      .map((period) => `${formatTime(period.start)} → ${formatTime(period.end)}`)
      .join(" | ")
  }, [schedulePreview, t.manualEntryNoPeriods, t.unknown])

  const summary = useMemo(() => {
    const linkedEmployees = employees.filter((emp) => !!emp.biotime_code).length
    const activeEmployees = employees.filter(
      (emp) => String(emp.status || "").toUpperCase() === "ACTIVE"
    ).length
    const activeDevices = devices.filter(
      (device) => String(device.status || "").toLowerCase() === "online"
    ).length
    const activeSchedules = workSchedules.filter((schedule) => !!schedule.is_active).length

    return {
      employeesCount: employees.length,
      linkedEmployees,
      activeEmployees,
      devicesCount: devices.length,
      activeDevices,
      workSchedulesCount: workSchedules.length,
      activeSchedules,
      unmappedCount: unmappedLogs.length,
      totalAttendanceRecords: dashboard?.total_records ?? 0,
      todayPresent: dashboard?.today.present ?? 0,
      todayLate: dashboard?.today.late ?? 0,
      todayAbsent: dashboard?.today.absent ?? 0,
      todayLeave: dashboard?.today.leave ?? 0,
    }
  }, [dashboard, devices, employees, unmappedLogs, workSchedules])

  if (loadingPage) {
    return (
      <div dir={dir} className="flex min-h-[60vh] items-center justify-center">
        <div className="flex items-center gap-3 rounded-2xl border border-border/60 bg-background px-5 py-4 shadow-sm">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm font-medium">{t.loadingPage}</span>
        </div>
      </div>
    )
  }

  return (
    <div dir={dir} className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm">
            <Fingerprint className="h-3.5 w-3.5" />
            {t.headerBadge}
          </div>

          <div className="space-y-1">
            <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">{t.pageTitle}</h1>
            <p className="text-sm text-muted-foreground md:text-base">{t.pageDescription}</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            onClick={handleOpenManualEntry}
            disabled={refreshing || syncingDevices || syncingAttendance}
            className="gap-2"
          >
            <PencilLine className="h-4 w-4" />
            {t.manualEntryButton}
          </Button>

          <Button
            variant="outline"
            onClick={() => void loadAll(true)}
            disabled={refreshing || syncingDevices || syncingAttendance}
            className="gap-2"
          >
            {refreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {t.refresh}
          </Button>

          <Button
            variant="outline"
            onClick={handleSyncDevices}
            disabled={syncingDevices || refreshing || syncingAttendance}
            className="gap-2"
          >
            {syncingDevices ? <Loader2 className="h-4 w-4 animate-spin" /> : <Cpu className="h-4 w-4" />}
            {t.syncDevices}
          </Button>

          <Button
            onClick={handleAttendanceSync}
            disabled={syncingAttendance || refreshing || syncingDevices}
            className="gap-2"
          >
            {syncingAttendance ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            {t.syncAttendance}
          </Button>
        </div>
      </div>

      <Dialog open={manualEntryOpen} onOpenChange={(open) => (!open ? handleCloseManualEntry() : setManualEntryOpen(true))}>
        <DialogContent className="max-w-3xl rounded-2xl">
          <DialogHeader className="space-y-2">
            <DialogTitle className="flex items-center gap-2 text-lg">
              <PencilLine className="h-5 w-5" />
              {t.manualEntryTitle}
            </DialogTitle>
            <DialogDescription>{t.manualEntryDescription}</DialogDescription>
          </DialogHeader>

          <div className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2 md:col-span-2">
                <Label>{t.manualEntryEmployee}</Label>

                <div className="relative">
                  <Search
                    className={[
                      "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                      isArabic ? "right-3" : "left-3",
                    ].join(" ")}
                  />
                  <Input
                    value={manualEntryEmployeeSearch}
                    onChange={(e) => setManualEntryEmployeeSearch(e.target.value)}
                    placeholder={t.manualEntryEmployeeSearch}
                    className={isArabic ? "pr-10" : "pl-10"}
                  />
                </div>

                <Select
                  value={manualEntryForm.employeeId}
                  onValueChange={(value) =>
                    setManualEntryForm((prev) => ({
                      ...prev,
                      employeeId: value,
                    }))
                  }
                >
                  <SelectTrigger dir={dir}>
                    <SelectValue placeholder={t.manualEntrySelectEmployee} />
                  </SelectTrigger>
                  <SelectContent>
                    {manualEntryFilteredEmployees.length === 0 ? (
                      <div className="px-3 py-2 text-sm text-muted-foreground">
                        {t.noMatchingEmployees}
                      </div>
                    ) : (
                      manualEntryFilteredEmployees.slice(0, 30).map((emp) => (
                        <SelectItem key={emp.id} value={String(emp.id)}>
                          {emp.full_name || emp.name || `#${emp.id}`}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>

                {selectedManualEmployee ? (
                  <div className="rounded-2xl border border-border/60 bg-muted/30 px-4 py-3 text-sm">
                    <div className="font-medium">{selectedManualEmployee.full_name || selectedManualEmployee.name}</div>
                    <div className="mt-1 text-muted-foreground">
                      {selectedManualEmployee.department || t.unknown} •{" "}
                      {selectedManualEmployee.job_title || t.unknown}
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="space-y-2">
                <Label>{t.manualEntryDate}</Label>
                <Input
                  type="date"
                  dir="ltr"
                  value={manualEntryForm.date}
                  onChange={(e) =>
                    setManualEntryForm((prev) => ({
                      ...prev,
                      date: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>{t.manualEntryActionType}</Label>
                <Select
                  value={manualEntryForm.actionType}
                  onValueChange={(value: ManualActionType) =>
                    setManualEntryForm((prev) => ({
                      ...prev,
                      actionType: value,
                    }))
                  }
                >
                  <SelectTrigger dir={dir}>
                    <SelectValue placeholder={t.manualEntryActionType} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="check_in">{t.manualEntryCheckInOnly}</SelectItem>
                    <SelectItem value="check_out">{t.manualEntryCheckOutOnly}</SelectItem>
                    <SelectItem value="both">{t.manualEntryBoth}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {(manualEntryForm.actionType === "check_in" || manualEntryForm.actionType === "both") && (
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <LogIn className="h-4 w-4" />
                    {t.checkIn}
                  </Label>
                  <Input
                    type="time"
                    dir="ltr"
                    value={manualEntryForm.checkIn}
                    onChange={(e) =>
                      setManualEntryForm((prev) => ({
                        ...prev,
                        checkIn: e.target.value,
                      }))
                    }
                  />
                </div>
              )}

              {(manualEntryForm.actionType === "check_out" || manualEntryForm.actionType === "both") && (
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <LogOut className="h-4 w-4" />
                    {t.checkOut}
                  </Label>
                  <Input
                    type="time"
                    dir="ltr"
                    value={manualEntryForm.checkOut}
                    onChange={(e) =>
                      setManualEntryForm((prev) => ({
                        ...prev,
                        checkOut: e.target.value,
                      }))
                    }
                  />
                </div>
              )}
            </div>

            <Separator />

            <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{t.manualEntrySchedulePreview}</h3>
                  <p className="text-sm text-muted-foreground">{t.schedule}</p>
                </div>

                {loadingSchedulePreview ? (
                  <div className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {t.loadingPage}
                  </div>
                ) : schedulePreview ? (
                  <Badge className={getStatusBadgeClass(schedulePreview.is_weekend ? "weekend" : "active")}>
                    {schedulePreview.is_weekend ? t.manualEntryWeekend : t.manualEntryWorkingDay}
                  </Badge>
                ) : null}
              </div>

              {!manualEntryForm.employeeId || !manualEntryForm.date ? (
                <div className="text-sm text-muted-foreground">{t.manualEntryNoSchedule}</div>
              ) : loadingSchedulePreview ? (
                <div className="text-sm text-muted-foreground">{t.loadingPage}</div>
              ) : !schedulePreview ? (
                <div className="text-sm text-muted-foreground">{t.manualEntryNoSchedule}</div>
              ) : (
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-xl border border-border/60 bg-background p-3">
                    <div className="text-xs text-muted-foreground">{t.manualEntryTypeLabel}</div>
                    <div className="mt-1 font-medium">
                      {getScheduleTypeLabel(schedulePreview.schedule_type, locale)}
                    </div>
                  </div>

                  <div className="rounded-xl border border-border/60 bg-background p-3">
                    <div className="text-xs text-muted-foreground">{t.manualEntryPeriodsLabel}</div>
                    <div className="mt-1 font-medium">{manualEntryPeriodsText}</div>
                  </div>

                  <div className="rounded-xl border border-border/60 bg-background p-3">
                    <div className="text-xs text-muted-foreground">{t.manualEntryTargetHoursLabel}</div>
                    <div className="mt-1 font-medium">
                      {schedulePreview.target_daily_hours
                        ? formatDecimal(schedulePreview.target_daily_hours)
                        : t.unknown}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <DialogFooter className="flex-col gap-2 sm:flex-row">
            <Button
              type="button"
              variant="outline"
              onClick={handleCloseManualEntry}
              disabled={manualEntryLoading}
            >
              {t.manualEntryCancel}
            </Button>

            <Button
              type="button"
              onClick={handleSubmitManualEntry}
              disabled={manualEntryLoading}
              className="gap-2"
            >
              {manualEntryLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {t.manualEntrySaving}
                </>
              ) : (
                <>
                  <PencilLine className="h-4 w-4" />
                  {t.manualEntrySave}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          title={t.todayPresent}
          value={summary.todayPresent}
          tone="emerald"
          icon={<UserCheck className="h-5 w-5" />}
        />
        <SummaryCard
          title={t.todayLate}
          value={summary.todayLate}
          tone="amber"
          icon={<Clock3 className="h-5 w-5" />}
        />
        <SummaryCard
          title={t.todayAbsent}
          value={summary.todayAbsent}
          tone="rose"
          icon={<TriangleAlert className="h-5 w-5" />}
        />
        <SummaryCard
          title={t.totalAttendanceRecords}
          value={summary.totalAttendanceRecords}
          tone="sky"
          icon={<CheckCircle2 className="h-5 w-5" />}
        />
      </div>

      <Card className="border-border/60 rounded-2xl">
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="space-y-1">
              <CardTitle className="text-base md:text-lg">{t.reportTitle}</CardTitle>
              <CardDescription>{t.reportDescription}</CardDescription>
            </div>

            <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
              <div className="relative min-w-[220px] flex-1 sm:flex-none">
                <Search
                  className={[
                    "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                    isArabic ? "right-3" : "left-3",
                  ].join(" ")}
                />
                <Input
                  value={reportSearch}
                  onChange={(e) => setReportSearch(e.target.value)}
                  placeholder={t.reportSearchPlaceholder}
                  className={isArabic ? "pr-10" : "pl-10"}
                />
              </div>

              <Button
                variant="outline"
                onClick={() => void loadRows()}
                disabled={loadingRows}
                className="gap-2"
              >
                {loadingRows ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                {t.refreshReport}
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="space-y-2">
              <Label>{t.fromDate}</Label>
              <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} dir="ltr" />
            </div>

            <div className="space-y-2">
              <Label>{t.toDate}</Label>
              <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} dir="ltr" />
            </div>

            <div className="space-y-2">
              <Label>{t.status}</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger dir={dir}>
                  <SelectValue placeholder={t.status} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.allStatuses}</SelectItem>
                  <SelectItem value="present">{t.present}</SelectItem>
                  <SelectItem value="late">{t.late}</SelectItem>
                  <SelectItem value="absent">{t.absent}</SelectItem>
                  <SelectItem value="leave">{t.leave}</SelectItem>
                  <SelectItem value="weekend">{t.weekend}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button className="w-full gap-2" onClick={() => void loadRows()} disabled={loadingRows}>
                {loadingRows ? <Loader2 className="h-4 w-4 animate-spin" /> : <CalendarDays className="h-4 w-4" />}
                {t.applyFilters}
              </Button>
            </div>
          </div>

          <Separator />

          <Card className="hidden rounded-2xl border-border/60 lg:block">
            <CardContent className="p-0">
              <div className="overflow-x-auto rounded-2xl">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.employee}</TableHead>
                      <TableHead>{t.date}</TableHead>
                      <TableHead>{t.status}</TableHead>
                      <TableHead>{t.schedule}</TableHead>
                      <TableHead>{t.checkIn}</TableHead>
                      <TableHead>{t.checkOut}</TableHead>
                      <TableHead>{t.workHours}</TableHead>
                      <TableHead>{t.delay}</TableHead>
                      <TableHead>{t.overtime}</TableHead>
                      <TableHead>{t.location}</TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {loadingRows ? (
                      <TableRow>
                        <TableCell colSpan={10} className="h-24 text-center">
                          <div className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            {t.loadingReport}
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : filteredRows.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={10} className="h-24 text-center text-muted-foreground">
                          {t.noMatchingRows}
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredRows.map((row, index) => (
                        <TableRow key={`${row.employee_id}-${row.date}-${index}`}>
                          <TableCell>
                            <div className="min-w-[180px]">
                              <p className="font-medium">{row.employee}</p>
                              <p className="text-xs text-muted-foreground">{row.schedule_label || "—"}</p>
                            </div>
                          </TableCell>
                          <TableCell className="tabular-nums">{formatDate(row.date)}</TableCell>
                          <TableCell>
                            <Badge className={getStatusBadgeClass(row.status)}>
                              {getLocalizedStatusLabel(row.status, row.status_ar, locale)}
                            </Badge>
                          </TableCell>
                          <TableCell className="whitespace-pre-line text-sm text-muted-foreground">
                            {row.period_display || "—"}
                          </TableCell>
                          <TableCell className="tabular-nums">{formatTime(row.check_in)}</TableCell>
                          <TableCell className="tabular-nums">{formatTime(row.check_out)}</TableCell>
                          <TableCell className="tabular-nums">{formatDecimal(row.actual_hours ?? 0)}</TableCell>
                          <TableCell className="tabular-nums">
                            {formatNumber(row.late_minutes ?? 0)} {t.minutesSuffix}
                          </TableCell>
                          <TableCell className="tabular-nums">
                            {formatNumber(row.overtime_minutes ?? 0)} {t.minutesSuffix}
                          </TableCell>
                          <TableCell>{row.location || "—"}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:hidden">
            {loadingRows ? (
              <Card className="border-border/60 rounded-2xl">
                <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                  {t.loadingReport}
                </CardContent>
              </Card>
            ) : filteredRows.length === 0 ? (
              <Card className="border-border/60 rounded-2xl">
                <CardContent className="py-10 text-center text-sm text-muted-foreground">
                  {t.noMatchingRows}
                </CardContent>
              </Card>
            ) : (
              filteredRows.map((row, index) => (
                <Card key={`${row.employee_id}-${row.date}-${index}`} className="border-border/60 rounded-2xl">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1 space-y-1">
                        <p className="truncate font-semibold">{row.employee}</p>
                        <p className="text-sm text-muted-foreground">{row.schedule_label || "—"}</p>
                      </div>

                      <Badge className={getStatusBadgeClass(row.status)}>
                        {getLocalizedStatusLabel(row.status, row.status_ar, locale)}
                      </Badge>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">{t.date}</p>
                        <p className="mt-1 font-medium tabular-nums">{formatDate(row.date)}</p>
                      </div>

                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">{t.location}</p>
                        <p className="mt-1 font-medium">{row.location || "—"}</p>
                      </div>

                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">{t.checkIn}</p>
                        <p className="mt-1 font-medium tabular-nums">{formatTime(row.check_in)}</p>
                      </div>

                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">{t.checkOut}</p>
                        <p className="mt-1 font-medium tabular-nums">{formatTime(row.check_out)}</p>
                      </div>

                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">{t.workHours}</p>
                        <p className="mt-1 font-medium tabular-nums">{formatDecimal(row.actual_hours ?? 0)}</p>
                      </div>

                      <div className="rounded-xl border bg-muted/30 p-3">
                        <p className="text-xs text-muted-foreground">{t.delay}</p>
                        <p className="mt-1 font-medium tabular-nums">
                          {formatNumber(row.late_minutes ?? 0)} {t.minutesSuffix}
                        </p>
                      </div>
                    </div>

                    <div className="mt-3 rounded-xl border bg-muted/30 p-3 text-sm text-muted-foreground">
                      <span className="font-medium text-foreground">{t.schedule}: </span>
                      {row.period_display || "—"}
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="border-border/60 rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base md:text-lg">{t.setupSummaryTitle}</CardTitle>
            <CardDescription>{t.setupSummaryDescription}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Users className="h-4 w-4" />
                  {t.employees}
                </div>
                <p className="mt-2 text-2xl font-semibold tabular-nums">{formatNumber(summary.employeesCount)}</p>
              </div>

              <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <BadgeCheck className="h-4 w-4" />
                  {t.linkedToBiotime}
                </div>
                <p className="mt-2 text-2xl font-semibold tabular-nums">{formatNumber(summary.linkedEmployees)}</p>
              </div>

              <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Cpu className="h-4 w-4" />
                  {t.onlineDevices}
                </div>
                <p className="mt-2 text-2xl font-semibold tabular-nums">{formatNumber(summary.activeDevices)}</p>
              </div>

              <Button
                type="button"
                variant="outline"
                onClick={() => setShowUnmapped((prev) => !prev)}
                className="h-auto justify-start rounded-2xl border-border/60 bg-muted/30 p-4 text-start"
              >
                <div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <TriangleAlert className="h-4 w-4" />
                    {t.unmappedLogs}
                  </div>
                  <p className="mt-2 text-2xl font-semibold tabular-nums text-foreground">
                    {formatNumber(summary.unmappedCount)}
                  </p>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60 rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base md:text-lg">{t.attendancePolicyTitle}</CardTitle>
            <CardDescription>{t.attendancePolicyDescription}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-2">
                <Label>{t.graceMinutes}</Label>
                <Input
                  type="number"
                  min={0}
                  dir="ltr"
                  value={policy.grace_minutes}
                  onChange={(e) =>
                    setPolicy((prev) => ({
                      ...prev,
                      grace_minutes: Number(e.target.value || 0),
                    }))
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>{t.lateAfterMinutes}</Label>
                <Input
                  type="number"
                  min={0}
                  dir="ltr"
                  value={policy.late_after_minutes}
                  onChange={(e) =>
                    setPolicy((prev) => ({
                      ...prev,
                      late_after_minutes: Number(e.target.value || 0),
                    }))
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>{t.absenceAfterMinutes}</Label>
                <Input
                  type="number"
                  min={0}
                  dir="ltr"
                  value={policy.absence_after_minutes}
                  onChange={(e) =>
                    setPolicy((prev) => ({
                      ...prev,
                      absence_after_minutes: Number(e.target.value || 0),
                    }))
                  }
                />
              </div>
            </div>

            <div className="grid gap-2">
              <TogglePolicyRow
                active={policy.auto_absent_if_no_checkin}
                onClick={() =>
                  setPolicy((prev) => ({
                    ...prev,
                    auto_absent_if_no_checkin: !prev.auto_absent_if_no_checkin,
                  }))
                }
                icon={<ShieldCheck className="h-4 w-4" />}
                label={t.autoAbsentIfNoCheckin}
                enabledLabel={t.enabled}
                disabledLabel={t.disabled}
                tone="emerald"
              />

              <TogglePolicyRow
                active={Boolean(policy.overtime_enabled)}
                onClick={() =>
                  setPolicy((prev) => ({
                    ...prev,
                    overtime_enabled: !prev.overtime_enabled,
                  }))
                }
                icon={<Zap className="h-4 w-4" />}
                label={t.overtimeEnabled}
                enabledLabel={t.enabled}
                disabledLabel={t.disabled}
                tone="sky"
              />
            </div>

            <Button className="w-full gap-2" onClick={handleSavePolicy} disabled={savingPolicy}>
              {savingPolicy ? <Loader2 className="h-4 w-4 animate-spin" /> : <BadgeCheck className="h-4 w-4" />}
              {t.savePolicy}
            </Button>
          </CardContent>
        </Card>
      </div>

      {showUnmapped && (
        <Card className="border-border/60 rounded-2xl">
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-base md:text-lg">{t.unmappedLogsTitle}</CardTitle>
                <CardDescription>{t.unmappedLogsDescription}</CardDescription>
              </div>

              <Button variant="outline" onClick={() => setShowUnmapped(false)}>
                {t.hide}
              </Button>
            </div>
          </CardHeader>

          <CardContent>
            <Card className="hidden rounded-2xl border-border/60 lg:block">
              <CardContent className="p-0">
                <div className="overflow-x-auto rounded-2xl">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t.employeeCode}</TableHead>
                        <TableHead>{t.punchTime}</TableHead>
                        <TableHead>{t.device}</TableHead>
                        <TableHead>{t.deviceSn}</TableHead>
                        <TableHead>{t.ipAddress}</TableHead>
                        <TableHead>{t.rawId}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {unmappedLogs.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} className="h-20 text-center text-muted-foreground">
                            {t.noUnmappedLogs}
                          </TableCell>
                        </TableRow>
                      ) : (
                        unmappedLogs.map((log) => (
                          <TableRow key={log.id}>
                            <TableCell className="font-medium">{log.employee_code}</TableCell>
                            <TableCell className="tabular-nums">{formatDateTime(log.punch_time)}</TableCell>
                            <TableCell>{log.terminal_alias || "—"}</TableCell>
                            <TableCell>{log.device_sn || "—"}</TableCell>
                            <TableCell>{log.device_ip || "—"}</TableCell>
                            <TableCell>{log.raw_id || "—"}</TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-4 lg:hidden">
              {unmappedLogs.length === 0 ? (
                <Card className="border-border/60 rounded-2xl">
                  <CardContent className="py-10 text-center text-sm text-muted-foreground">
                    {t.noUnmappedLogs}
                  </CardContent>
                </Card>
              ) : (
                unmappedLogs.map((log) => (
                  <Card key={log.id} className="border-border/60 rounded-2xl">
                    <CardContent className="p-4">
                      <div className="space-y-1">
                        <p className="font-semibold">{log.employee_code}</p>
                        <p className="text-sm text-muted-foreground tabular-nums">
                          {formatDateTime(log.punch_time)}
                        </p>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.device}</p>
                          <p className="mt-1 font-medium">{log.terminal_alias || "—"}</p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.deviceSn}</p>
                          <p className="mt-1 font-medium">{log.device_sn || "—"}</p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.ipAddress}</p>
                          <p className="mt-1 font-medium">{log.device_ip || "—"}</p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.rawId}</p>
                          <p className="mt-1 font-medium">{log.raw_id || "—"}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="border-border/60 rounded-2xl">
          <CardHeader>
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-base md:text-lg">{t.readyEmployeesTitle}</CardTitle>
                <CardDescription>{t.readyEmployeesDescription}</CardDescription>
              </div>

              <div className="relative min-w-[220px] max-w-full">
                <Search
                  className={[
                    "pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                    isArabic ? "right-3" : "left-3",
                  ].join(" ")}
                />
                <Input
                  value={employeeSearch}
                  onChange={(e) => setEmployeeSearch(e.target.value)}
                  placeholder={t.employeesSearchPlaceholder}
                  className={isArabic ? "pr-10" : "pl-10"}
                />
              </div>
            </div>
          </CardHeader>

          <CardContent>
            <Card className="hidden rounded-2xl border-border/60 lg:block">
              <CardContent className="p-0">
                <div className="overflow-x-auto rounded-2xl">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t.employee}</TableHead>
                        <TableHead>{t.department}</TableHead>
                        <TableHead>{t.jobTitle}</TableHead>
                        <TableHead>{t.status}</TableHead>
                        <TableHead>{t.biotime}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredEmployees.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} className="h-20 text-center text-muted-foreground">
                            {t.noMatchingEmployees}
                          </TableCell>
                        </TableRow>
                      ) : (
                        filteredEmployees.slice(0, 10).map((emp) => (
                          <TableRow key={emp.id}>
                            <TableCell className="font-medium">{emp.full_name || emp.name || "—"}</TableCell>
                            <TableCell>{emp.department || "—"}</TableCell>
                            <TableCell>{emp.job_title || "—"}</TableCell>
                            <TableCell>
                              <Badge
                                className={
                                  String(emp.status || "").toUpperCase() === "ACTIVE"
                                    ? getStatusBadgeClass("active")
                                    : getStatusBadgeClass("inactive")
                                }
                              >
                                {String(emp.status || "").toUpperCase() === "ACTIVE"
                                  ? locale === "ar"
                                    ? t.activeStatus
                                    : t.active
                                  : locale === "ar"
                                    ? t.inactiveStatus
                                    : t.inactive}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {emp.biotime_code ? (
                                <Badge className={getStatusBadgeClass("linked")}>{emp.biotime_code}</Badge>
                              ) : (
                                <Badge className={getStatusBadgeClass("unlinked")}>{t.notLinked}</Badge>
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-4 lg:hidden">
              {filteredEmployees.length === 0 ? (
                <Card className="border-border/60 rounded-2xl">
                  <CardContent className="py-10 text-center text-sm text-muted-foreground">
                    {t.noMatchingEmployees}
                  </CardContent>
                </Card>
              ) : (
                filteredEmployees.slice(0, 10).map((emp) => (
                  <Card key={emp.id} className="border-border/60 rounded-2xl">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1 space-y-1">
                          <p className="truncate font-semibold">{emp.full_name || emp.name || "—"}</p>
                          <p className="text-sm text-muted-foreground">
                            {emp.department || "—"} • {emp.job_title || "—"}
                          </p>
                        </div>

                        <Badge
                          className={
                            String(emp.status || "").toUpperCase() === "ACTIVE"
                              ? getStatusBadgeClass("active")
                              : getStatusBadgeClass("inactive")
                          }
                        >
                          {String(emp.status || "").toUpperCase() === "ACTIVE"
                            ? locale === "ar"
                              ? t.activeStatus
                              : t.active
                            : locale === "ar"
                              ? t.inactiveStatus
                              : t.inactive}
                        </Badge>
                      </div>

                      <div className="mt-4 rounded-xl border bg-muted/30 p-3 text-sm">
                        <span className="text-muted-foreground">{t.biotime}: </span>
                        <span className="font-medium">{emp.biotime_code || t.notLinked}</span>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60 rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base md:text-lg">{t.biotimeDevicesTitle}</CardTitle>
            <CardDescription>{t.biotimeDevicesDescription}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <Card className="hidden rounded-2xl border-border/60 lg:block">
              <CardContent className="p-0">
                <div className="overflow-x-auto rounded-2xl">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t.device}</TableHead>
                        <TableHead>{t.ipAddress}</TableHead>
                        <TableHead>{t.location}</TableHead>
                        <TableHead>{t.status}</TableHead>
                        <TableHead>{t.usersCount}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {devices.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} className="h-20 text-center text-muted-foreground">
                            {t.noDevices}
                          </TableCell>
                        </TableRow>
                      ) : (
                        devices.slice(0, 10).map((device) => (
                          <TableRow key={device.id}>
                            <TableCell>
                              <div>
                                <p className="font-medium">{device.name || "—"}</p>
                                <p className="text-xs text-muted-foreground">{device.sn || "—"}</p>
                              </div>
                            </TableCell>
                            <TableCell>{device.ip || "—"}</TableCell>
                            <TableCell>{device.geo_location || device.location || "—"}</TableCell>
                            <TableCell>
                              <Badge
                                className={
                                  String(device.status || "").toLowerCase() === "online"
                                    ? getStatusBadgeClass("online")
                                    : getStatusBadgeClass("offline")
                                }
                              >
                                {String(device.status || "").toLowerCase() === "online" ? t.online : t.offline}
                              </Badge>
                            </TableCell>
                            <TableCell className="tabular-nums">{formatNumber(device.users ?? 0)}</TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-4 lg:hidden">
              {devices.length === 0 ? (
                <Card className="border-border/60 rounded-2xl">
                  <CardContent className="py-10 text-center text-sm text-muted-foreground">
                    {t.noDevices}
                  </CardContent>
                </Card>
              ) : (
                devices.slice(0, 10).map((device) => (
                  <Card key={device.id} className="border-border/60 rounded-2xl">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <p className="font-semibold">{device.name || "—"}</p>
                          <p className="text-sm text-muted-foreground">{device.sn || "—"}</p>
                        </div>

                        <Badge
                          className={
                            String(device.status || "").toLowerCase() === "online"
                              ? getStatusBadgeClass("online")
                              : getStatusBadgeClass("offline")
                          }
                        >
                          {String(device.status || "").toLowerCase() === "online" ? t.online : t.offline}
                        </Badge>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.ipAddress}</p>
                          <p className="mt-1 font-medium">{device.ip || "—"}</p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.location}</p>
                          <p className="mt-1 font-medium">{device.geo_location || device.location || "—"}</p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3 col-span-2">
                          <p className="text-xs text-muted-foreground">{t.usersCount}</p>
                          <p className="mt-1 font-medium tabular-nums">{formatNumber(device.users ?? 0)}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>

            <div className="flex items-center gap-2 rounded-2xl border border-border/60 bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
              <FileSpreadsheet className="h-4 w-4 shrink-0" />
              {t.supportiveMessage}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="border-border/60 rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base md:text-lg">{t.schedulesTitle}</CardTitle>
            <CardDescription>{t.schedulesDescription}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            {workSchedules.length === 0 ? (
              <div className="rounded-2xl border border-border/60 bg-muted/30 px-4 py-5 text-sm text-muted-foreground">
                {t.noSchedules}
              </div>
            ) : (
              workSchedules.slice(0, 6).map((schedule) => (
                <div key={schedule.id} className="rounded-2xl border border-border/60 bg-muted/30 p-4">
                  <div className="mb-2 flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold">{schedule.name || "—"}</p>
                      <p className="text-xs text-muted-foreground">
                        {getScheduleTypeLabel(schedule.schedule_type, locale)}
                      </p>
                    </div>

                    <Badge className={schedule.is_active ? getStatusBadgeClass("active") : getStatusBadgeClass("inactive")}>
                      {schedule.is_active ? t.active : t.inactive}
                    </Badge>
                  </div>

                  <div className="space-y-1 text-sm text-muted-foreground">
                    <p>
                      {t.periods}: {buildSchedulePeriods(schedule, locale, t)}
                    </p>
                    <p>
                      {t.weeklyWeekend}: {locale === "ar"
                        ? schedule.weekend_days_ar || schedule.weekend_days || "—"
                        : schedule.weekend_days || schedule.weekend_days_ar || "—"}
                    </p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="border-border/60 rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base md:text-lg">{t.operationalTitle}</CardTitle>
            <CardDescription>{t.operationalDescription}</CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Building2 className="h-4 w-4" />
                {t.pageStructure}
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{t.pageStructureDescription}</p>
            </div>

            <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <GitBranch className="h-4 w-4" />
                {t.workSchedules}
              </div>
              <p className="mt-2 text-2xl font-semibold tabular-nums">{formatNumber(summary.workSchedulesCount)}</p>
            </div>

            <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <CheckCircle2 className="h-4 w-4" />
                {t.biotimeDevicesTitle}
              </div>
              <p className="mt-2 text-2xl font-semibold tabular-nums">{formatNumber(summary.devicesCount)}</p>
            </div>

            <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Briefcase className="h-4 w-4" />
                {t.linkedEmployees}
              </div>
              <p className="mt-2 text-2xl font-semibold tabular-nums">{formatNumber(summary.linkedEmployees)}</p>
            </div>

            <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Workflow className="h-4 w-4" />
                {t.todayPresent}
              </div>
              <p className="mt-2 text-2xl font-semibold tabular-nums">{formatNumber(summary.todayPresent)}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}