"use client"

import { use, useCallback, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import {
  ArrowLeft,
  Banknote,
  CircleDollarSign,
  Download,
  Eye,
  FileSpreadsheet,
  FileText,
  Loader2,
  Printer,
  Receipt,
  RefreshCw,
  Search,
  Wallet,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

type Locale = "ar" | "en"
type RunStatus = "DRAFT" | "CALCULATED" | "APPROVED" | "PAID" | string
type RecordStatus = "UNPAID" | "PARTIAL" | "PAID" | "PENDING" | string
type PaymentMethod = "BANK" | "CASH"

type PayrollRunSummary = {
  id?: number
  run_id?: number
  month?: string
  status?: RunStatus
  progress_percent?: number | string
  accounting_consistency?: boolean
  amounts?: {
    total_net?: number | string
    total_paid?: number | string
    total_remaining?: number | string
  }
  counts?: {
    total_records?: number
    paid_records?: number
    unpaid_records?: number
    partial_records?: number
  }
}

type PayrollRecordItem = {
  record_id: number
  employee_id: number
  employee_name: string
  net_salary: number | string
  paid_amount: number | string
  remaining_amount: number | string
  status: RecordStatus
  run_status: RunStatus
  is_snapshot: boolean
}

type SalarySlipLineItem = {
  code?: string
  label?: string
  amount?: number | string
  days?: number | string | null
  quantity?: number | string | null
  unit?: string | null
  notes?: string | null
  category?: string | null
}

type SalarySlipFact = {
  key?: string
  label?: string
  value?: string | number | null
}

type SalarySlipPrintPayload = {
  earnings_items?: SalarySlipLineItem[]
  deduction_items?: SalarySlipLineItem[]
  facts?: SalarySlipFact[]
  summary?: {
    gross_salary?: number | string
    total_earnings?: number | string
    total_deductions?: number | string
    net_salary?: number | string
    paid_amount?: number | string
    remaining_amount?: number | string
  }
  meta?: {
    employment_start_date?: string | null
    payroll_period_start?: string | null
    payroll_period_end?: string | null
    effective_start_date?: string | null
    effective_end_date?: string | null
    eligible_days?: number | string | null
    payable_days_after_deduction?: number | string | null
    unpaid_absence_days?: number | string | null
  }
}

type SalarySlipResponse = {
  id?: number
  record_id?: number
  company?: {
    id?: number
    name?: string
    email?: string | null
    phone?: string | null
    commercial_number?: string | null
    vat_number?: string | null
    building_number?: string | null
    street?: string | null
    district?: string | null
    city?: string | null
    postal_code?: string | null
    short_address?: string | null
    logo_url?: string | null
  }
  employee?: {
    id?: number
    full_name?: string
    employee_number?: string | null
    department?: string | null
    job_title?: string | null
    branches?: string[]
  }
  month?: string
  payment_status?: string
  payment?: {
    status?: string
    paid_amount?: number | string
    remaining_amount?: number | string
    payment_method?: string | null
    paid_at?: string | null
  }
  contract?: {
    id?: number | null
    contract_type?: string | null
    start_date?: string | null
  }
  financial_info?: {
    basic_salary?: number
    housing_allowance?: number
    transport_allowance?: number
    food_allowance?: number
    other_allowances?: number
    bank_name?: string | null
    iban?: string | null
  }
  run?: {
    id?: number
    status?: string
  }
  salary?: {
    base_salary?: number
    allowance?: number
    bonus?: number
    overtime?: number
    deductions?: number
    net_salary?: number
    reference_base_salary?: number
    reference_allowance?: number
    prorated_base_salary?: number
    prorated_allowance?: number
  }
  period?: {
    employment_start_date?: string | null
    payroll_period_start?: string | null
    payroll_period_end?: string | null
    effective_start_date?: string | null
    effective_end_date?: string | null
    eligible_days?: number
    payable_days_before_deduction?: number
    payable_days_after_deduction?: number
    unpaid_absence_days?: number
    inferred_absence_days?: number
    leave_paid_days?: number
    leave_partial_unpaid_days?: number
  }
  breakdown?: Record<string, unknown>
  print_payload?: SalarySlipPrintPayload
  generated_at?: string
}

type PaymentDialogState = {
  open: boolean
  record: PayrollRecordItem | null
  amount: string
  method: PaymentMethod
  reference: string
  notes: string
}

type Dictionary = {
  back: string
  pageTitle: string
  pageDescription: string
  refresh: string
  runSummary: string
  recordsList: string
  salarySlip: string
  salaryDetailsCenterTitle: string
  month: string
  status: string
  totalNet: string
  totalPaid: string
  totalRemaining: string
  progress: string
  accounting: string
  totalRecords: string
  paidRecords: string
  unpaidRecords: string
  partialRecords: string
  searchTitle: string
  searchPlaceholder: string
  searchHint: string
  all: string
  paid: string
  unpaid: string
  partial: string
  employee: string
  paidAmount: string
  remainingAmount: string
  actions: string
  details: string
  pay: string
  slip: string
  loading: string
  noData: string
  loadFailed: string
  paymentFailed: string
  paymentSuccess: string
  enterAmount: string
  paymentMethod: string
  bank: string
  cash: string
  invalidAmount: string
  yes: string
  no: string
  unknown: string
  baseSalary: string
  allowance: string
  bonus: string
  overtime: string
  deductions: string
  netSalary: string
  generatedAt: string
  noSlipSelected: string
  employeeNumber: string
  department: string
  jobTitle: string
  branches: string
  printHint: string
  print: string
  exportExcel: string
  exportLoading: string
  printing: string
  noRecordsToExport: string
  noRecordsToPrint: string
  excelExportSuccess: string
  excelExportFailed: string
  printFailed: string
  recordId: string
  employeeId: string
  filtersApplied: string
  statusAll: string
  printSlip: string
  slipPrinting: string
  noSlipToPrint: string
  salaryDetails: string
  companyName: string
  earningsDetails: string
  deductionDetails: string
  item: string
  amount: string
  days: string
  quantity: string
  notes: string
  summary: string
  grossSalary: string
  totalDeductions: string
  paymentStatus: string
  paidAt: string
  signatures: string
  receivedBy: string
  accountantSignature: string
  companyStamp: string
  noDetailsAvailable: string
  createdBySystem: string
  createdByPrimey: string
  contractType: string
  basicSalaryRef: string
  earnings: string
  deductionsSide: string
  totalEarnings: string
  salaryNet: string
  userSignature: string
  managerSignature: string
  bankName: string
  iban: string
  accountType: string
  salaryCard: string
  paymentDate: string
  employmentStartDate: string
  payrollPeriod: string
  effectivePeriod: string
  eligibleDays: string
  payableDaysBeforeDeduction: string
  payableDaysAfterDeduction: string
  unpaidAbsenceDays: string
  inferredAbsenceDays: string
  leavePaidDays: string
  leavePartialUnpaidDays: string
  referenceBaseSalary: string
  referenceAllowance: string
  proratedBaseSalary: string
  proratedAllowance: string
  payrollPeriodStart: string
  payrollPeriodEnd: string
  effectiveStartDate: string
  effectiveEndDate: string
  cannotPayZero: string
  periodDetails: string
  referenceDetails: string
  paymentDialogTitle: string
  paymentDialogDescription: string
  paymentDialogEmployee: string
  paymentDialogRemaining: string
  paymentDialogAmountLabel: string
  paymentDialogMethodLabel: string
  paymentDialogReferenceLabel: string
  paymentDialogReferencePlaceholder: string
  paymentDialogNotesLabel: string
  paymentDialogNotesPlaceholder: string
  paymentDialogCancel: string
  paymentDialogSubmit: string
  paymentReferenceRequired: string
  paymentAmountExceeded: string
}

const translations: Record<Locale, Dictionary> = {
  ar: {
    back: "رجوع",
    pageTitle: "تفاصيل تشغيل الرواتب",
    pageDescription: "عرض ملخص التشغيل وسجلات الموظفين والدفع الجزئي وقسيمة الراتب",
    refresh: "تحديث",
    runSummary: "ملخص التشغيل",
    recordsList: "سجلات الرواتب",
    salarySlip: "قسيمة الراتب",
    salaryDetailsCenterTitle: "تفصيل الراتب",
    month: "الشهر",
    status: "الحالة",
    totalNet: "إجمالي الصافي",
    totalPaid: "إجمالي المدفوع",
    totalRemaining: "إجمالي المتبقي",
    progress: "التقدم",
    accounting: "التطابق",
    totalRecords: "إجمالي السجلات",
    paidRecords: "السجلات المدفوعة",
    unpaidRecords: "السجلات غير المدفوعة",
    partialRecords: "السجلات الجزئية",
    searchTitle: "البحث والفلاتر",
    searchPlaceholder: "ابحث باسم الموظف...",
    searchHint: "يمكنك البحث بالاسم أو تصفية الحالة",
    all: "الكل",
    paid: "مدفوع",
    unpaid: "غير مدفوع",
    partial: "جزئي",
    employee: "الموظف",
    paidAmount: "المدفوع",
    remainingAmount: "المتبقي",
    actions: "الإجراءات",
    details: "تفاصيل",
    pay: "دفع",
    slip: "قسيمة",
    loading: "جاري تحميل البيانات...",
    noData: "لا توجد سجلات مطابقة",
    loadFailed: "تعذر تحميل بيانات التشغيل",
    paymentFailed: "تعذر تنفيذ عملية الدفع",
    paymentSuccess: "تم تسجيل الدفع بنجاح",
    enterAmount: "أدخل مبلغ الدفع",
    paymentMethod: "طريقة الدفع",
    bank: "تحويل بنكي",
    cash: "نقدي",
    invalidAmount: "المبلغ غير صالح",
    yes: "نعم",
    no: "لا",
    unknown: "غير معروف",
    baseSalary: "الراتب الأساسي",
    allowance: "البدلات",
    bonus: "المكافآت",
    overtime: "الإضافي",
    deductions: "الخصومات",
    netSalary: "صافي الراتب",
    generatedAt: "تاريخ الإنشاء",
    noSlipSelected: "اختر سجلًا لعرض قسيمة الراتب",
    employeeNumber: "رقم الموظف",
    department: "القسم",
    jobTitle: "المسمى الوظيفي",
    branches: "الفروع",
    printHint: "الأرقام والتواريخ تعرض دائمًا بالإنجليزية",
    print: "طباعة",
    exportExcel: "تصدير إكسل",
    exportLoading: "جاري التصدير...",
    printing: "جاري تجهيز الطباعة...",
    noRecordsToExport: "لا توجد سجلات لتصديرها",
    noRecordsToPrint: "لا توجد سجلات للطباعة",
    excelExportSuccess: "تم تصدير ملف Excel بنجاح",
    excelExportFailed: "تعذر تصدير ملف Excel",
    printFailed: "تعذر فتح نافذة الطباعة",
    recordId: "رقم السجل",
    employeeId: "رقم الموظف",
    filtersApplied: "الفلاتر المطبقة",
    statusAll: "الكل",
    printSlip: "طباعة القسيمة",
    slipPrinting: "جاري تجهيز القسيمة...",
    noSlipToPrint: "لا توجد قسيمة محددة للطباعة",
    salaryDetails: "تفاصيل الراتب",
    companyName: "الشركة",
    earningsDetails: "الإيرادات",
    deductionDetails: "الخصومات",
    item: "البند",
    amount: "المبلغ",
    days: "الأيام",
    quantity: "الكمية",
    notes: "التفاصيل",
    summary: "الملخص",
    grossSalary: "إجمالي الإيرادات",
    totalDeductions: "مجموع الخصومات",
    paymentStatus: "حالة الدفع",
    paidAt: "تاريخ الدفع",
    signatures: "التوقيعات",
    receivedBy: "توقيع المستخدم",
    accountantSignature: "توقيع المدير",
    companyStamp: "ختم الشركة",
    noDetailsAvailable: "لا توجد تفاصيل إضافية متاحة",
    createdBySystem: "أنشئ بواسطة",
    createdByPrimey: "نظام Mhamcloud للموارد البشرية",
    contractType: "نوع العقد",
    basicSalaryRef: "الراتب المرجعي",
    earnings: "الإيرادات",
    deductionsSide: "الخصومات",
    totalEarnings: "مجموع الراتب",
    salaryNet: "صافي الراتب",
    userSignature: "توقيع المستخدم",
    managerSignature: "توقيع المدير",
    bankName: "اسم البنك",
    iban: "آيبان",
    accountType: "نوع الحساب",
    salaryCard: "بطاقة راتب",
    paymentDate: "التاريخ",
    employmentStartDate: "تاريخ بداية العمل",
    payrollPeriod: "فترة الرواتب",
    effectivePeriod: "فترة الاستحقاق",
    eligibleDays: "الأيام المستحقة",
    payableDaysBeforeDeduction: "الأيام قبل الخصم",
    payableDaysAfterDeduction: "الأيام بعد الخصم",
    unpaidAbsenceDays: "أيام الغياب غير المدفوعة",
    inferredAbsenceDays: "أيام الغياب المستنتجة",
    leavePaidDays: "أيام الإجازة المدفوعة",
    leavePartialUnpaidDays: "أيام الإجازة غير المدفوعة",
    referenceBaseSalary: "الراتب الأساسي المرجعي",
    referenceAllowance: "البدلات المرجعية",
    proratedBaseSalary: "الراتب الأساسي المحتسب",
    proratedAllowance: "البدلات المحتسبة",
    payrollPeriodStart: "بداية فترة الرواتب",
    payrollPeriodEnd: "نهاية فترة الرواتب",
    effectiveStartDate: "بداية فترة الاستحقاق",
    effectiveEndDate: "نهاية فترة الاستحقاق",
    cannotPayZero: "لا يوجد مبلغ متبقٍ للدفع",
    periodDetails: "تفاصيل الفترة",
    referenceDetails: "المرجع والاحتساب",
    paymentDialogTitle: "تسجيل دفعة راتب",
    paymentDialogDescription: "أدخل تفاصيل الدفعة من داخل النظام بدل نافذة المتصفح.",
    paymentDialogEmployee: "الموظف",
    paymentDialogRemaining: "المتبقي",
    paymentDialogAmountLabel: "مبلغ الدفع",
    paymentDialogMethodLabel: "نوع الدفع",
    paymentDialogReferenceLabel: "مرجع التحويل",
    paymentDialogReferencePlaceholder: "مثال: TRX-2026-0001",
    paymentDialogNotesLabel: "ملاحظات",
    paymentDialogNotesPlaceholder: "اكتب ملاحظة داخلية إن وجدت",
    paymentDialogCancel: "إلغاء",
    paymentDialogSubmit: "تأكيد الدفع",
    paymentReferenceRequired: "مرجع التحويل مطلوب عند اختيار التحويل البنكي",
    paymentAmountExceeded: "مبلغ الدفع أكبر من المبلغ المتبقي",
  },
  en: {
    back: "Back",
    pageTitle: "Payroll Run Details",
    pageDescription: "View run summary, employee payroll records, partial payments, and salary slip",
    refresh: "Refresh",
    runSummary: "Run Summary",
    recordsList: "Payroll Records",
    salarySlip: "Salary Slip",
    salaryDetailsCenterTitle: "Salary Details",
    month: "Month",
    status: "Status",
    totalNet: "Total Net",
    totalPaid: "Total Paid",
    totalRemaining: "Total Remaining",
    progress: "Progress",
    accounting: "Accounting",
    totalRecords: "Total Records",
    paidRecords: "Paid Records",
    unpaidRecords: "Unpaid Records",
    partialRecords: "Partial Records",
    searchTitle: "Search & Filters",
    searchPlaceholder: "Search by employee name...",
    searchHint: "You can search by employee name or filter by payment status",
    all: "All",
    paid: "Paid",
    unpaid: "Unpaid",
    partial: "Partial",
    employee: "Employee",
    paidAmount: "Paid Amount",
    remainingAmount: "Remaining Amount",
    actions: "Actions",
    details: "Details",
    pay: "Pay",
    slip: "Slip",
    loading: "Loading data...",
    noData: "No matching records found",
    loadFailed: "Failed to load payroll run data",
    paymentFailed: "Failed to apply payment",
    paymentSuccess: "Payment applied successfully",
    enterAmount: "Enter payment amount",
    paymentMethod: "Payment method",
    bank: "Bank Transfer",
    cash: "Cash",
    invalidAmount: "Invalid amount",
    yes: "Yes",
    no: "No",
    unknown: "Unknown",
    baseSalary: "Base Salary",
    allowance: "Allowance",
    bonus: "Bonus",
    overtime: "Overtime",
    deductions: "Deductions",
    netSalary: "Net Salary",
    generatedAt: "Generated At",
    noSlipSelected: "Select a record to preview the salary slip",
    employeeNumber: "Employee No.",
    department: "Department",
    jobTitle: "Job Title",
    branches: "Branches",
    printHint: "Numbers and dates are always shown in English",
    print: "Print",
    exportExcel: "Export Excel",
    exportLoading: "Exporting...",
    printing: "Preparing print...",
    noRecordsToExport: "No records to export",
    noRecordsToPrint: "No records to print",
    excelExportSuccess: "Excel file exported successfully",
    excelExportFailed: "Failed to export Excel file",
    printFailed: "Failed to open print window",
    recordId: "Record ID",
    employeeId: "Employee ID",
    filtersApplied: "Applied Filters",
    statusAll: "All",
    printSlip: "Print Slip",
    slipPrinting: "Preparing slip...",
    noSlipToPrint: "No selected salary slip to print",
    salaryDetails: "Salary Details",
    companyName: "Company",
    earningsDetails: "Earnings",
    deductionDetails: "Deductions",
    item: "Item",
    amount: "Amount",
    days: "Days",
    quantity: "Quantity",
    notes: "Details",
    summary: "Summary",
    grossSalary: "Total Earnings",
    totalDeductions: "Total Deductions",
    paymentStatus: "Payment Status",
    paidAt: "Paid At",
    signatures: "Signatures",
    receivedBy: "User Signature",
    accountantSignature: "Manager Signature",
    companyStamp: "Company Stamp",
    noDetailsAvailable: "No additional details available",
    createdBySystem: "Created by",
    createdByPrimey: "Mham Cloud System",
    contractType: "Contract Type",
    basicSalaryRef: "Reference Salary",
    earnings: "Earnings",
    deductionsSide: "Deductions",
    totalEarnings: "Total Earnings",
    salaryNet: "Net Salary",
    userSignature: "User Signature",
    managerSignature: "Manager Signature",
    bankName: "Bank Name",
    iban: "IBAN",
    accountType: "Account Type",
    salaryCard: "Salary Card",
    paymentDate: "Date",
    employmentStartDate: "Employment Start Date",
    payrollPeriod: "Payroll Period",
    effectivePeriod: "Effective Period",
    eligibleDays: "Eligible Days",
    payableDaysBeforeDeduction: "Payable Days Before Deduction",
    payableDaysAfterDeduction: "Payable Days After Deduction",
    unpaidAbsenceDays: "Unpaid Absence Days",
    inferredAbsenceDays: "Inferred Absence Days",
    leavePaidDays: "Paid Leave Days",
    leavePartialUnpaidDays: "Unpaid Leave Days",
    referenceBaseSalary: "Reference Base Salary",
    referenceAllowance: "Reference Allowance",
    proratedBaseSalary: "Prorated Base Salary",
    proratedAllowance: "Prorated Allowance",
    payrollPeriodStart: "Payroll Period Start",
    payrollPeriodEnd: "Payroll Period End",
    effectiveStartDate: "Effective Start Date",
    effectiveEndDate: "Effective End Date",
    cannotPayZero: "No remaining amount to pay",
    periodDetails: "Period Details",
    referenceDetails: "Reference & Calculation",
    paymentDialogTitle: "Record Salary Payment",
    paymentDialogDescription: "Enter the payment details from the system UI.",
    paymentDialogEmployee: "Employee",
    paymentDialogRemaining: "Remaining",
    paymentDialogAmountLabel: "Payment Amount",
    paymentDialogMethodLabel: "Payment Method",
    paymentDialogReferenceLabel: "Transfer Reference",
    paymentDialogReferencePlaceholder: "Example: TRX-2026-0001",
    paymentDialogNotesLabel: "Notes",
    paymentDialogNotesPlaceholder: "Write an internal note if needed",
    paymentDialogCancel: "Cancel",
    paymentDialogSubmit: "Confirm Payment",
    paymentReferenceRequired: "Transfer reference is required for bank transfer",
    paymentAmountExceeded: "Payment amount is greater than remaining amount",
  },
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

function detectLocale(): Locale {
  if (typeof document !== "undefined") {
    const htmlLang = document.documentElement.lang?.toLowerCase().trim() || ""
    if (htmlLang.startsWith("ar")) return "ar"
    if (htmlLang.startsWith("en")) return "en"

    const htmlDir = document.documentElement.dir?.toLowerCase().trim() || ""
    if (htmlDir === "rtl") return "ar"
    if (htmlDir === "ltr") return "en"

    const cookieLocale =
      getCookie("locale") ||
      getCookie("lang") ||
      getCookie("NEXT_LOCALE")

    if (cookieLocale?.toLowerCase().startsWith("ar")) return "ar"
    if (cookieLocale?.toLowerCase().startsWith("en")) return "en"

    const localStorageLocale =
      typeof window !== "undefined"
        ? window.localStorage.getItem("primey-locale")
        : null

    if (localStorageLocale?.toLowerCase().startsWith("ar")) return "ar"
    if (localStorageLocale?.toLowerCase().startsWith("en")) return "en"
  }

  if (typeof navigator !== "undefined") {
    const language = navigator.language?.toLowerCase() || ""
    if (language.startsWith("ar")) return "ar"
  }

  return "en"
}

function getApiBaseUrl() {
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
  if (envBase) return envBase.replace(/\/+$/, "")

  if (typeof window !== "undefined") {
    const { origin, hostname, port } = window.location

    if (port === "3000") {
      return `${window.location.protocol}//${hostname}:8000`
    }

    return origin.replace(/\/+$/, "")
  }

  return "http://localhost:8000"
}

function formatNumber(value?: number | string | null, maximumFractionDigits = 0) {
  if (value === null || value === undefined || value === "") return "0"

  const numericValue =
    typeof value === "number" ? value : Number(String(value).replace(/,/g, ""))

  if (Number.isNaN(numericValue)) return String(value)

  return new Intl.NumberFormat("en-US", {
    useGrouping: true,
    minimumFractionDigits: 0,
    maximumFractionDigits,
  }).format(numericValue)
}

function formatDate(value?: string | null) {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")

  return `${year}-${month}-${day}`
}

function formatDateTime(value?: string | null) {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"

  const hh = date.getHours()
  const mm = String(date.getMinutes()).padStart(2, "0")
  const suffix = hh >= 12 ? "PM" : "AM"
  const normalizedHour = hh % 12 === 0 ? 12 : hh % 12

  return `${normalizedHour}:${mm}${suffix} ${formatDate(value)}`
}

function formatMonth(value?: string | null) {
  if (!value) return "—"

  const clean = String(value).trim()
  if (/^\d{4}-\d{2}$/.test(clean)) return clean

  const date = new Date(clean)
  if (Number.isNaN(date.getTime())) return clean

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")

  return `${year}-${month}`
}

function getArabicMonthName(monthValue?: string | null) {
  const clean = formatMonth(monthValue)
  const match = clean.match(/^(\d{4})-(\d{2})$/)
  if (!match) return clean

  const monthNames = [
    "يناير",
    "فبراير",
    "مارس",
    "أبريل",
    "مايو",
    "يونيو",
    "يوليو",
    "أغسطس",
    "سبتمبر",
    "أكتوبر",
    "نوفمبر",
    "ديسمبر",
  ]

  const monthIndex = Number(match[2]) - 1
  if (monthIndex < 0 || monthIndex > 11) return clean

  return `${monthNames[monthIndex]} ${match[1]}`
}

function getRunStatusLabel(status: RunStatus, locale: Locale) {
  const normalized = String(status || "").toUpperCase()

  if (normalized === "DRAFT") return locale === "ar" ? "مسودة" : "Draft"
  if (normalized === "CALCULATED") return locale === "ar" ? "محسوبة" : "Calculated"
  if (normalized === "APPROVED") return locale === "ar" ? "معتمدة" : "Approved"
  if (normalized === "PAID") return locale === "ar" ? "مدفوعة" : "Paid"

  return status || (locale === "ar" ? "غير معروف" : "Unknown")
}

function getRecordStatusLabel(status: RecordStatus, locale: Locale) {
  const normalized = String(status || "").toUpperCase()

  if (normalized === "PAID") return locale === "ar" ? "مدفوع" : "Paid"
  if (normalized === "PARTIAL") return locale === "ar" ? "جزئي" : "Partial"
  if (normalized === "UNPAID") return locale === "ar" ? "غير مدفوع" : "Unpaid"
  if (normalized === "PENDING") return locale === "ar" ? "غير مدفوع" : "Pending"

  return status || (locale === "ar" ? "غير معروف" : "Unknown")
}

function getPaymentMethodLabel(method: string | null | undefined, locale: Locale) {
  const normalized = String(method || "").toUpperCase()
  if (normalized === "BANK") return locale === "ar" ? "تحويل بنكي" : "Bank Transfer"
  if (normalized === "CASH") return locale === "ar" ? "نقدي" : "Cash"
  return locale === "ar" ? "غير محدد" : "Not specified"
}

function getBadgeClasses(
  variant: "draft" | "calculated" | "approved" | "paid" | "partial" | "unpaid"
) {
  if (variant === "paid") return "border-emerald-200 bg-emerald-50 text-emerald-700"
  if (variant === "approved") return "border-blue-200 bg-blue-50 text-blue-700"
  if (variant === "calculated") return "border-amber-200 bg-amber-50 text-amber-700"
  if (variant === "partial") return "border-orange-200 bg-orange-50 text-orange-700"
  if (variant === "unpaid") return "border-red-200 bg-red-50 text-red-700"
  return "border-slate-200 bg-slate-50 text-slate-700"
}

function StatusBadge({
  text,
  variant,
}: {
  text: string
  variant: "draft" | "calculated" | "approved" | "paid" | "partial" | "unpaid"
}) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        getBadgeClasses(variant),
      ].join(" ")}
    >
      {text}
    </span>
  )
}

function getRunBadgeVariant(status: RunStatus) {
  const normalized = String(status || "").toUpperCase()
  if (normalized === "PAID") return "paid" as const
  if (normalized === "APPROVED") return "approved" as const
  if (normalized === "CALCULATED") return "calculated" as const
  return "draft" as const
}

function getRecordBadgeVariant(status: RecordStatus) {
  const normalized = String(status || "").toUpperCase()
  if (normalized === "PAID") return "paid" as const
  if (normalized === "PARTIAL") return "partial" as const
  return "unpaid" as const
}

function getTableAlignClass(
  kind: "start" | "center" | "end",
  isArabic: boolean
) {
  if (kind === "center") return "text-center"
  if (kind === "end") return isArabic ? "text-left" : "text-right"
  return isArabic ? "text-right" : "text-left"
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;")
}

function toNumericValue(value?: number | string | null) {
  if (value === null || value === undefined || value === "") return 0
  const parsed =
    typeof value === "number" ? value : Number(String(value).replace(/,/g, ""))
  return Number.isFinite(parsed) ? parsed : 0
}

function normalizeLineItems(
  items?: SalarySlipLineItem[] | null
): SalarySlipLineItem[] {
  if (!Array.isArray(items)) return []

  return items
    .map((item) => ({
      code: item?.code || "",
      label: item?.label || "",
      amount: toNumericValue(item?.amount),
      days:
        item?.days === null || item?.days === undefined || item?.days === ""
          ? null
          : item.days,
      quantity:
        item?.quantity === null || item?.quantity === undefined || item?.quantity === ""
          ? null
          : item.quantity,
      unit: item?.unit || null,
      notes: item?.notes || null,
      category: item?.category || null,
    }))
    .filter((item) => item.label || toNumericValue(item.amount) !== 0)
}

function normalizeFacts(facts?: SalarySlipFact[] | null): SalarySlipFact[] {
  if (!Array.isArray(facts)) return []
  return facts.filter((fact) => {
    const label = String(fact?.label || "").trim()
    const value = fact?.value
    return Boolean(label && value !== null && value !== undefined && value !== "")
  })
}

function getStructuredSlipData(slip: SalarySlipResponse | null) {
  if (!slip) {
    return {
      earningsItems: [] as SalarySlipLineItem[],
      deductionItems: [] as SalarySlipLineItem[],
      facts: [] as SalarySlipFact[],
      summary: {
        grossSalary: 0,
        totalDeductions: 0,
        netSalary: 0,
        paidAmount: 0,
        remainingAmount: 0,
      },
    }
  }

  const payload = slip.print_payload
  const earningsItems = normalizeLineItems(payload?.earnings_items)
  const deductionItems = normalizeLineItems(payload?.deduction_items)
  const facts = normalizeFacts(payload?.facts)

  const fallbackEarnings: SalarySlipLineItem[] = [
    {
      code: "base_salary_prorated",
      label: "Base Salary",
      amount:
        slip.salary?.prorated_base_salary ??
        slip.salary?.base_salary ??
        0,
    },
    {
      code: "allowance_prorated",
      label: "Allowance",
      amount:
        slip.salary?.prorated_allowance ??
        slip.salary?.allowance ??
        0,
    },
    {
      code: "bonus",
      label: "Bonus",
      amount: slip.salary?.bonus ?? 0,
    },
    {
      code: "overtime",
      label: "Overtime",
      amount: slip.salary?.overtime ?? 0,
    },
  ].filter((item) => toNumericValue(item.amount) > 0)

  const fallbackDeductions: SalarySlipLineItem[] = [
    {
      code: "deductions_total",
      label: "Deductions",
      amount: slip.salary?.deductions ?? 0,
    },
  ].filter((item) => toNumericValue(item.amount) > 0)

  const finalEarnings = earningsItems.length > 0 ? earningsItems : fallbackEarnings
  const finalDeductions =
    deductionItems.length > 0 ? deductionItems : fallbackDeductions

  const grossSalary =
    toNumericValue(payload?.summary?.gross_salary) ||
    finalEarnings.reduce((sum, item) => sum + toNumericValue(item.amount), 0)

  const totalDeductions =
    toNumericValue(payload?.summary?.total_deductions) ||
    finalDeductions.reduce((sum, item) => sum + toNumericValue(item.amount), 0)

  const netSalary =
    toNumericValue(payload?.summary?.net_salary) ||
    toNumericValue(slip.salary?.net_salary)

  const paidAmount =
    toNumericValue(payload?.summary?.paid_amount) ||
    toNumericValue(slip.payment?.paid_amount)

  const remainingAmount =
    toNumericValue(payload?.summary?.remaining_amount) ||
    toNumericValue(slip.payment?.remaining_amount)

  return {
    earningsItems: finalEarnings,
    deductionItems: finalDeductions,
    facts,
    summary: {
      grossSalary,
      totalDeductions,
      netSalary,
      paidAmount,
      remainingAmount,
    },
  }
}

function localizeSlipLabel(label: string, locale: Locale) {
  const normalized = label.trim().toLowerCase()

  const map: Record<string, { ar: string; en: string }> = {
    "base salary": { ar: "الراتب الأساسي", en: "Base Salary" },
    allowance: { ar: "البدلات", en: "Allowance" },
    bonus: { ar: "مكافأة", en: "Bonus" },
    overtime: { ar: "إضافي", en: "Overtime" },
    deductions: { ar: "خصومات", en: "Deductions" },
    "absence deduction": { ar: "خصم غياب", en: "Absence Deduction" },
    "late deduction": { ar: "خصم تأخير", en: "Late Deduction" },
    "administrative deduction": { ar: "خصم إداري", en: "Administrative Deduction" },
    "loan / advance": { ar: "سلفة", en: "Loan / Advance" },
    "penalty / disciplinary deduction": { ar: "جزاء / خصم تأديبي", en: "Penalty / Disciplinary Deduction" },
    "other deductions": { ar: "خصومات أخرى", en: "Other Deductions" },
  }

  const item = map[normalized]
  if (!item) return label
  return locale === "ar" ? item.ar : item.en
}

function getRemainingAmount(record: PayrollRecordItem) {
  return toNumericValue(record.remaining_amount)
}

function buildPeriodRows(
  slip: SalarySlipResponse | null,
  t: Dictionary
): Array<{ label: string; value: string }> {
  if (!slip?.period) return []

  const period = slip.period
  return [
    {
      label: t.employmentStartDate,
      value: formatDate(period.employment_start_date || null),
    },
    {
      label: t.payrollPeriodStart,
      value: formatDate(period.payroll_period_start || null),
    },
    {
      label: t.payrollPeriodEnd,
      value: formatDate(period.payroll_period_end || null),
    },
    {
      label: t.effectiveStartDate,
      value: formatDate(period.effective_start_date || null),
    },
    {
      label: t.effectiveEndDate,
      value: formatDate(period.effective_end_date || null),
    },
    {
      label: t.eligibleDays,
      value: formatNumber(period.eligible_days ?? 0, 2),
    },
    {
      label: t.payableDaysBeforeDeduction,
      value: formatNumber(period.payable_days_before_deduction ?? 0, 2),
    },
    {
      label: t.payableDaysAfterDeduction,
      value: formatNumber(period.payable_days_after_deduction ?? 0, 2),
    },
    {
      label: t.unpaidAbsenceDays,
      value: formatNumber(period.unpaid_absence_days ?? 0, 2),
    },
    {
      label: t.inferredAbsenceDays,
      value: formatNumber(period.inferred_absence_days ?? 0, 2),
    },
    {
      label: t.leavePaidDays,
      value: formatNumber(period.leave_paid_days ?? 0, 2),
    },
    {
      label: t.leavePartialUnpaidDays,
      value: formatNumber(period.leave_partial_unpaid_days ?? 0, 2),
    },
  ].filter((row) => row.value !== "0" && row.value !== "0.00" && row.value !== "—")
}

function buildReferenceRows(
  slip: SalarySlipResponse | null,
  t: Dictionary
): Array<{ label: string; value: string }> {
  if (!slip?.salary) return []

  return [
    {
      label: t.referenceBaseSalary,
      value: formatNumber(slip.salary.reference_base_salary ?? 0, 2),
    },
    {
      label: t.referenceAllowance,
      value: formatNumber(slip.salary.reference_allowance ?? 0, 2),
    },
    {
      label: t.proratedBaseSalary,
      value: formatNumber(
        slip.salary.prorated_base_salary ??
          slip.salary.base_salary ??
          0,
        2
      ),
    },
    {
      label: t.proratedAllowance,
      value: formatNumber(
        slip.salary.prorated_allowance ??
          slip.salary.allowance ??
          0,
        2
      ),
    },
  ].filter((row) => row.value !== "0.00" && row.value !== "0")
}

function getDefaultPaymentDialogState(): PaymentDialogState {
  return {
    open: false,
    record: null,
    amount: "",
    method: "BANK",
    reference: "",
    notes: "",
  }
}

export default function CompanyPayrollRunDetailsPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const router = useRouter()
  const resolvedParams = use(params)
  const runId = resolvedParams.id

  const [locale, setLocale] = useState<Locale>("en")
  const [summary, setSummary] = useState<PayrollRunSummary | null>(null)
  const [records, setRecords] = useState<PayrollRecordItem[]>([])
  const [selectedSlip, setSelectedSlip] = useState<SalarySlipResponse | null>(null)
  const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<
    "ALL" | "PAID" | "UNPAID" | "PARTIAL"
  >("ALL")
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [actioningKey, setActioningKey] = useState<string | null>(null)
  const [slipLoading, setSlipLoading] = useState(false)
  const [exportingExcel, setExportingExcel] = useState(false)
  const [printing, setPrinting] = useState(false)
  const [printingSlip, setPrintingSlip] = useState(false)
  const [paymentDialog, setPaymentDialog] = useState<PaymentDialogState>(
    getDefaultPaymentDialogState()
  )

  const apiBaseUrl = getApiBaseUrl()
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

  const loadPageData = useCallback(
    async (silent = false) => {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      try {
        const [summaryRes, recordsRes] = await Promise.all([
          fetch(`${apiBaseUrl}/api/company/payroll/runs/${runId}/`, {
            credentials: "include",
            cache: "no-store",
            headers: { Accept: "application/json" },
          }),
          fetch(`${apiBaseUrl}/api/company/payroll/runs/${runId}/records/`, {
            credentials: "include",
            cache: "no-store",
            headers: { Accept: "application/json" },
          }),
        ])

        if (!summaryRes.ok || !recordsRes.ok) {
          throw new Error("Failed to load payroll run data")
        }

        const summaryData = await summaryRes.json()
        const recordsData = await recordsRes.json()

        setSummary(summaryData || null)
        setRecords(Array.isArray(recordsData?.results) ? recordsData.results : [])
      } catch (error) {
        console.error("Failed loading payroll run details:", error)
        setSummary(null)
        setRecords([])
        toast.error(translations[detectLocale()].loadFailed)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [apiBaseUrl, runId]
  )

  useEffect(() => {
    void loadPageData()
  }, [loadPageData])

  const filteredRecords = useMemo(() => {
    const term = search.trim().toLowerCase()

    return records.filter((record) => {
      const nameMatches = (record.employee_name || "").toLowerCase().includes(term)
      const statusMatches = String(record.status || "").toLowerCase().includes(term)
      const matchesSearch = !term || nameMatches || statusMatches

      const normalizedStatus = String(record.status || "").toUpperCase()
      const statusAlias =
        normalizedStatus === "PENDING" ? "UNPAID" : normalizedStatus

      const matchesStatus =
        statusFilter === "ALL" || statusAlias === statusFilter

      return matchesSearch && matchesStatus
    })
  }, [records, search, statusFilter])

  const handleViewSlip = async (recordId: number) => {
    setSelectedRecordId(recordId)
    setSlipLoading(true)

    try {
      const res = await fetch(`${apiBaseUrl}/api/company/payroll/slip/${recordId}/`, {
        credentials: "include",
        cache: "no-store",
        headers: { Accept: "application/json" },
      })

      const data = await res.json().catch(() => null)

      if (!res.ok) {
        const message =
          data?.detail ||
          data?.error ||
          translations[detectLocale()].loadFailed

        toast.error(String(message))
        return
      }

      setSelectedSlip(data || null)
    } catch (error) {
      console.error("Failed loading salary slip:", error)
      toast.error(t.loadFailed)
    } finally {
      setSlipLoading(false)
    }
  }

  const openPaymentDialog = (record: PayrollRecordItem) => {
    const remainingAmount = getRemainingAmount(record)

    if (remainingAmount <= 0) {
      toast.error(t.cannotPayZero)
      return
    }

    setPaymentDialog({
      open: true,
      record,
      amount: String(remainingAmount),
      method: "BANK",
      reference: "",
      notes: "",
    })
  }

  const closePaymentDialog = () => {
    if (paymentDialog.record && actioningKey === `pay-${paymentDialog.record.record_id}`) {
      return
    }
    setPaymentDialog(getDefaultPaymentDialogState())
  }

  const submitPaymentDialog = async () => {
    const record = paymentDialog.record
    if (!record) return

    const remainingAmount = getRemainingAmount(record)
    const amount = Number(String(paymentDialog.amount || "").replace(/,/g, ""))

    if (!Number.isFinite(amount) || amount <= 0) {
      toast.error(t.invalidAmount)
      return
    }

    if (amount > remainingAmount) {
      toast.error(t.paymentAmountExceeded)
      return
    }

    if (paymentDialog.method === "BANK" && !paymentDialog.reference.trim()) {
      toast.error(t.paymentReferenceRequired)
      return
    }

    const actionKey = `pay-${record.record_id}`
    setActioningKey(actionKey)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        `${apiBaseUrl}/api/company/payroll/records/${record.record_id}/pay/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || "",
          },
          body: JSON.stringify({
            amount,
            method: paymentDialog.method,
            payment_method: paymentDialog.method,
            reference: paymentDialog.reference.trim() || null,
            notes: paymentDialog.notes.trim() || null,
          }),
        }
      )

      const data = await res.json().catch(() => null)

      if (!res.ok) {
        const message =
          data?.detail ||
          data?.error ||
          translations[detectLocale()].paymentFailed

        toast.error(String(message))
        return
      }

      toast.success(t.paymentSuccess)
      setPaymentDialog(getDefaultPaymentDialogState())
      await loadPageData(true)

      if (selectedRecordId === record.record_id) {
        await handleViewSlip(record.record_id)
      }
    } catch (error) {
      console.error("Payroll record payment failed:", error)
      toast.error(t.paymentFailed)
    } finally {
      setActioningKey(null)
    }
  }

  const topStats = useMemo(() => {
    return {
      totalNet: summary?.amounts?.total_net ?? 0,
      totalPaid: summary?.amounts?.total_paid ?? 0,
      totalRemaining:
        summary?.amounts?.total_remaining ??
        summary?.amounts?.total_net ??
        0,
      totalRecords:
        summary?.counts?.total_records ??
        records.length ??
        0,
    }
  }, [summary, records])

  const normalizedStatusFilterLabel = useMemo(() => {
    if (statusFilter === "PAID") return t.paid
    if (statusFilter === "UNPAID") return t.unpaid
    if (statusFilter === "PARTIAL") return t.partial
    return t.statusAll
  }, [statusFilter, t])

  const exportRows = useMemo(() => {
    return filteredRecords.map((record) => ({
      [t.recordId]: record.record_id,
      [t.employeeId]: record.employee_id,
      [t.employee]: record.employee_name || "—",
      [t.status]: getRecordStatusLabel(record.status, locale),
      [t.netSalary]: Number(String(record.net_salary ?? 0).replace(/,/g, "")) || 0,
      [t.paidAmount]: Number(String(record.paid_amount ?? 0).replace(/,/g, "")) || 0,
      [t.remainingAmount]:
        Number(String(record.remaining_amount ?? 0).replace(/,/g, "")) || 0,
      [t.month]: formatMonth(summary?.month),
    }))
  }, [filteredRecords, locale, summary?.month, t])

  const handleExportExcel = async () => {
    if (filteredRecords.length === 0) {
      toast.error(t.noRecordsToExport)
      return
    }

    setExportingExcel(true)

    try {
      const XLSX = await import("xlsx")
      const worksheet = XLSX.utils.json_to_sheet(exportRows)
      const workbook = XLSX.utils.book_new()

      XLSX.utils.book_append_sheet(workbook, worksheet, "Payroll Records")
      worksheet["!cols"] = [
        { wch: 12 },
        { wch: 12 },
        { wch: 28 },
        { wch: 16 },
        { wch: 16 },
        { wch: 16 },
        { wch: 16 },
        { wch: 14 },
      ]

      const fileMonth = formatMonth(summary?.month).replace(/[^\d-]/g, "") || "run"
      const fileName = `payroll-records-${fileMonth}-run-${runId}.xlsx`

      XLSX.writeFile(workbook, fileName)
      toast.success(t.excelExportSuccess)
    } catch (error) {
      console.error("Excel export failed:", error)
      toast.error(t.excelExportFailed)
    } finally {
      setExportingExcel(false)
    }
  }

  const handlePrint = () => {
    if (filteredRecords.length === 0) {
      toast.error(t.noRecordsToPrint)
      return
    }

    setPrinting(true)

    try {
      const printWindow = window.open("", "_blank", "width=1200,height=800")
      if (!printWindow) {
        toast.error(t.printFailed)
        return
      }

      const pageTitle = escapeHtml(t.recordsList)
      const reportTitle = escapeHtml(t.pageTitle)
      const companyName = escapeHtml(selectedSlip?.company?.name || "Mham Cloud")
      const monthValue = escapeHtml(formatMonth(summary?.month))
      const statusValue = escapeHtml(normalizedStatusFilterLabel)
      const searchValue = escapeHtml(search.trim() || "—")
      const totalCount = filteredRecords.length

      const rowsHtml = filteredRecords
        .map(
          (record) => `
            <tr>
              <td>${escapeHtml(String(record.record_id))}</td>
              <td>${escapeHtml(String(record.employee_id))}</td>
              <td>${escapeHtml(record.employee_name || "—")}</td>
              <td>${escapeHtml(getRecordStatusLabel(record.status, locale))}</td>
              <td>${escapeHtml(formatNumber(record.net_salary, 2))}</td>
              <td>${escapeHtml(formatNumber(record.paid_amount, 2))}</td>
              <td>${escapeHtml(formatNumber(record.remaining_amount, 2))}</td>
            </tr>
          `
        )
        .join("")

      const html = `
        <!DOCTYPE html>
        <html lang="${locale}" dir="${dir}">
          <head>
            <meta charset="UTF-8" />
            <title>${pageTitle}</title>
            <style>
              * { box-sizing: border-box; }
              body {
                margin: 0;
                padding: 24px;
                font-family: Arial, "Segoe UI", sans-serif;
                color: #111827;
                background: #ffffff;
              }
              .header { margin-bottom: 20px; }
              .title {
                font-size: 28px;
                font-weight: 700;
                margin: 0 0 8px 0;
              }
              .subtitle {
                font-size: 14px;
                color: #6b7280;
                margin: 0;
              }
              .meta-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 12px;
                margin: 20px 0 24px;
              }
              .meta-card {
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 12px 14px;
                background: #fafafa;
              }
              .meta-label {
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 6px;
              }
              .meta-value {
                font-size: 16px;
                font-weight: 600;
              }
              table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
              }
              th, td {
                border: 1px solid #e5e7eb;
                padding: 10px 12px;
                font-size: 13px;
                vertical-align: middle;
                word-wrap: break-word;
              }
              th {
                background: #f3f4f6;
                font-weight: 700;
              }
              .text-start { text-align: ${isArabic ? "right" : "left"}; }
              .text-center { text-align: center; }
              .footer {
                margin-top: 18px;
                font-size: 12px;
                color: #6b7280;
              }
              @media print {
                body { padding: 0; }
              }
            </style>
          </head>
          <body>
            <div class="header">
              <h1 class="title">${reportTitle}</h1>
              <p class="subtitle">${companyName}</p>
            </div>

            <div class="meta-grid">
              <div class="meta-card">
                <div class="meta-label">${escapeHtml(t.month)}</div>
                <div class="meta-value">${monthValue}</div>
              </div>
              <div class="meta-card">
                <div class="meta-label">${escapeHtml(t.totalRecords)}</div>
                <div class="meta-value">${escapeHtml(formatNumber(totalCount))}</div>
              </div>
              <div class="meta-card">
                <div class="meta-label">${escapeHtml(t.filtersApplied)}</div>
                <div class="meta-value">${statusValue}</div>
              </div>
              <div class="meta-card">
                <div class="meta-label">${escapeHtml(t.searchTitle)}</div>
                <div class="meta-value">${searchValue}</div>
              </div>
            </div>

            <table>
              <thead>
                <tr>
                  <th class="text-center">${escapeHtml(t.recordId)}</th>
                  <th class="text-center">${escapeHtml(t.employeeId)}</th>
                  <th class="text-start">${escapeHtml(t.employee)}</th>
                  <th class="text-center">${escapeHtml(t.status)}</th>
                  <th class="text-center">${escapeHtml(t.netSalary)}</th>
                  <th class="text-center">${escapeHtml(t.paidAmount)}</th>
                  <th class="text-center">${escapeHtml(t.remainingAmount)}</th>
                </tr>
              </thead>
              <tbody>
                ${rowsHtml}
              </tbody>
            </table>

            <div class="footer">
              ${escapeHtml(t.printHint)}
            </div>

            <script>
              window.onload = function () {
                window.focus();
                window.print();
              };
            </script>
          </body>
        </html>
      `

      printWindow.document.open()
      printWindow.document.write(html)
      printWindow.document.close()
    } catch (error) {
      console.error("Print failed:", error)
      toast.error(t.printFailed)
    } finally {
      setPrinting(false)
    }
  }

  const handlePrintSlip = () => {
    if (!selectedSlip) {
      toast.error(t.noSlipToPrint)
      return
    }

    setPrintingSlip(true)

    try {
      const printWindow = window.open("", "_blank", "width=1200,height=1050")
      if (!printWindow) {
        toast.error(t.printFailed)
        return
      }

      const structured = getStructuredSlipData(selectedSlip)

      const company = selectedSlip.company || {}
      const employee = selectedSlip.employee || {}
      const financialInfo = selectedSlip.financial_info || {}
      const payment = selectedSlip.payment || {}
      const salary = selectedSlip.salary || {}
      const period = selectedSlip.period || {}

      const companyName = escapeHtml(company.name || "—")
      const employeeName = escapeHtml(employee.full_name || "—")
      const employeeNumber = escapeHtml(employee.employee_number || "—")
      const department = escapeHtml(employee.department || "—")
      const jobTitle = escapeHtml(employee.job_title || "—")
      const contractType = escapeHtml(selectedSlip.contract?.contract_type || "—")

      const companyAddressParts = [
        company.building_number,
        company.street,
        company.district,
        company.city,
        company.postal_code,
        company.short_address,
      ]
        .filter(Boolean)
        .map((item) => String(item).trim())
        .filter(Boolean)

      const companyAddress = escapeHtml(
        companyAddressParts.length > 0 ? companyAddressParts.join(" - ") : "—"
      )

      const paymentMethod = escapeHtml(
        getPaymentMethodLabel(payment.payment_method, locale)
      )
      const paidAt = escapeHtml(formatDate(payment.paid_at || null))
      const generatedAt = escapeHtml(formatDate(selectedSlip.generated_at))
      const generatedAtDateTime = escapeHtml(formatDateTime(selectedSlip.generated_at))
      const paymentStatus = escapeHtml(
        getRecordStatusLabel(
          (selectedSlip.payment_status || "") as RecordStatus,
          locale
        )
      )

      const logoUrl = company.logo_url ? escapeHtml(String(company.logo_url)) : ""
      const monthDisplay =
        locale === "ar"
          ? escapeHtml(getArabicMonthName(selectedSlip.month))
          : escapeHtml(formatMonth(selectedSlip.month))

      const bankName = escapeHtml(financialInfo.bank_name || "—")
      const iban = escapeHtml(financialInfo.iban || "—")

      const earningsRows = structured.earningsItems
      const deductionsRows = structured.deductionItems
      const maxRows = Math.max(earningsRows.length, deductionsRows.length, 4)

      const tableRowsHtml = Array.from({ length: maxRows })
        .map((_, index) => {
          const earning = earningsRows[index]
          const deduction = deductionsRows[index]

          const deductionExtra: string[] = []
          if (deduction?.days !== null && deduction?.days !== undefined) {
            deductionExtra.push(
              locale === "ar"
                ? `عدد الأيام ${String(deduction.days)}`
                : `Days ${String(deduction.days)}`
            )
          }
          if (deduction?.quantity !== null && deduction?.quantity !== undefined) {
            deductionExtra.push(
              deduction.unit
                ? `${String(deduction.quantity)} ${String(deduction.unit)}`
                : String(deduction.quantity)
            )
          }
          if (deduction?.notes) {
            deductionExtra.push(String(deduction.notes))
          }

          const earningExtra: string[] = []
          if (earning?.days !== null && earning?.days !== undefined) {
            earningExtra.push(
              locale === "ar"
                ? `عدد الأيام ${String(earning.days)}`
                : `Days ${String(earning.days)}`
            )
          }
          if (earning?.quantity !== null && earning?.quantity !== undefined) {
            earningExtra.push(
              earning.unit
                ? `${String(earning.quantity)} ${String(earning.unit)}`
                : String(earning.quantity)
            )
          }
          if (earning?.notes) {
            earningExtra.push(String(earning.notes))
          }

          return `
            <tr>
              <td class="amount-cell">
                ${deduction ? escapeHtml(formatNumber(deduction.amount, 2)) : ""}
              </td>
              <td class="item-cell">
                ${deduction ? escapeHtml(localizeSlipLabel(String(deduction.label || "—"), locale)) : ""}
              </td>
              <td class="detail-cell">
                ${deduction ? escapeHtml(deductionExtra.join(" - ")) : ""}
              </td>

              <td class="detail-cell">
                ${earning ? escapeHtml(earningExtra.join(" - ")) : ""}
              </td>
              <td class="amount-cell">
                ${earning ? escapeHtml(formatNumber(earning.amount, 2)) : ""}
              </td>
              <td class="item-cell">
                ${earning ? escapeHtml(localizeSlipLabel(String(earning.label || "—"), locale)) : ""}
              </td>
            </tr>
          `
        })
        .join("")

      const logoHtml = logoUrl
        ? `<img src="${logoUrl}" alt="Company Logo" class="company-logo" />`
        : `<div class="company-name-fallback">${companyName}</div>`

      const periodRows = [
        {
          label: escapeHtml(t.employmentStartDate),
          value: escapeHtml(formatDate(period.employment_start_date || null)),
        },
        {
          label: escapeHtml(t.payrollPeriod),
          value: escapeHtml(
            `${formatDate(period.payroll_period_start || null)} → ${formatDate(period.payroll_period_end || null)}`
          ),
        },
        {
          label: escapeHtml(t.effectivePeriod),
          value: escapeHtml(
            `${formatDate(period.effective_start_date || null)} → ${formatDate(period.effective_end_date || null)}`
          ),
        },
        {
          label: escapeHtml(t.eligibleDays),
          value: escapeHtml(formatNumber(period.eligible_days ?? 0, 2)),
        },
        {
          label: escapeHtml(t.payableDaysAfterDeduction),
          value: escapeHtml(formatNumber(period.payable_days_after_deduction ?? 0, 2)),
        },
        {
          label: escapeHtml(t.unpaidAbsenceDays),
          value: escapeHtml(formatNumber(period.unpaid_absence_days ?? 0, 2)),
        },
      ]
        .filter((row) => row.value !== "—" && row.value !== "0.00" && row.value !== "0")
        .map(
          (row) => `
            <tr>
              <td class="meta-label-cell">${row.label}</td>
              <td class="meta-value-cell">${row.value}</td>
            </tr>
          `
        )
        .join("")

      const referenceRows = [
        {
          label: escapeHtml(t.referenceBaseSalary),
          value: escapeHtml(formatNumber(salary.reference_base_salary ?? financialInfo.basic_salary ?? 0, 2)),
        },
        {
          label: escapeHtml(t.referenceAllowance),
          value: escapeHtml(formatNumber(salary.reference_allowance ?? 0, 2)),
        },
        {
          label: escapeHtml(t.proratedBaseSalary),
          value: escapeHtml(formatNumber(salary.prorated_base_salary ?? salary.base_salary ?? 0, 2)),
        },
        {
          label: escapeHtml(t.proratedAllowance),
          value: escapeHtml(formatNumber(salary.prorated_allowance ?? salary.allowance ?? 0, 2)),
        },
      ]
        .filter((row) => row.value !== "0.00" && row.value !== "0")
        .map(
          (row) => `
            <tr>
              <td class="meta-label-cell">${row.label}</td>
              <td class="meta-value-cell">${row.value}</td>
            </tr>
          `
        )
        .join("")

      const html = `
        <!DOCTYPE html>
        <html lang="${locale}" dir="rtl">
          <head>
            <meta charset="UTF-8" />
            <title>${escapeHtml(t.salarySlip)}</title>
            <style>
              * { box-sizing: border-box; }
              body {
                margin: 0;
                padding: 20px;
                background: #ffffff;
                color: #111827;
                font-family: Arial, "Segoe UI", sans-serif;
              }
              .slip {
                width: 100%;
                max-width: 980px;
                margin: 0 auto;
                background: #fff;
              }
              .topbar {
                display: grid;
                grid-template-columns: 1fr auto 1fr;
                align-items: start;
                gap: 16px;
                margin-bottom: 10px;
              }
              .top-left,
              .top-right {
                font-size: 13px;
                line-height: 1.7;
                color: #111827;
              }
              .top-left {
                text-align: left;
                font-weight: 700;
                padding-top: 8px;
              }
              .top-right {
                text-align: right;
              }
              .company-wrap {
                display: flex;
                align-items: flex-start;
                justify-content: flex-end;
                gap: 12px;
              }
              .company-logo {
                max-width: 100px;
                max-height: 52px;
                object-fit: contain;
                display: block;
              }
              .company-name-fallback {
                font-size: 24px;
                font-weight: 800;
                color: #111827;
              }
              .company-meta {
                font-size: 13px;
                line-height: 1.6;
              }
              .center-title {
                text-align: center;
                margin: 14px 0 18px;
              }
              .center-title h1 {
                margin: 0;
                font-size: 34px;
                font-weight: 600;
                color: #111827;
              }
              .center-title .month {
                margin-top: 4px;
                font-size: 20px;
                font-weight: 500;
              }
              .employee-box {
                display: grid;
                grid-template-columns: 1fr;
                gap: 4px;
                width: 46%;
                margin-right: auto;
                margin-bottom: 16px;
                font-size: 14px;
                line-height: 1.6;
              }
              .meta-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 18px;
                font-size: 13px;
                margin-bottom: 8px;
              }
              .meta-row .right,
              .meta-row .left {
                white-space: nowrap;
              }
              .meta-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 14px;
                margin-bottom: 16px;
              }
              .meta-table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                font-size: 13px;
              }
              .meta-table th,
              .meta-table td {
                border: 1px solid #d1d5db;
                padding: 8px 10px;
              }
              .meta-table th {
                background: #f8fafc;
                font-weight: 700;
                text-align: center;
              }
              .meta-label-cell {
                width: 50%;
                font-weight: 600;
              }
              .meta-value-cell {
                width: 50%;
                text-align: center;
              }
              table.salary-table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                margin-top: 6px;
                font-size: 13px;
              }
              .salary-table th,
              .salary-table td {
                border: 1px solid #c9c9c9;
                padding: 8px 8px;
                vertical-align: top;
                min-height: 36px;
              }
              .salary-table th {
                background: #33495f;
                color: #ffffff;
                font-weight: 700;
                font-size: 14px;
              }
              .salary-table .section-title {
                text-align: center;
              }
              .salary-table .amount-cell {
                width: 13%;
                text-align: center;
                font-weight: 500;
              }
              .salary-table .item-cell {
                width: 16%;
                text-align: right;
              }
              .salary-table .detail-cell {
                width: 21%;
                text-align: right;
                color: #374151;
              }
              .summary-label-cell {
                font-weight: 700;
                text-align: right;
              }
              .summary-value-cell {
                font-weight: 700;
                text-align: center;
              }
              .footer-space {
                height: 18px;
              }
              @media print {
                body { padding: 0; }
                .slip { max-width: none; }
              }
            </style>
          </head>
          <body>
            <div class="slip">
              <div class="topbar">
                <div class="top-left">
                  ${escapeHtml(t.createdByPrimey)}<br />
                  ${generatedAt}
                </div>

                <div></div>

                <div class="top-right">
                  <div class="company-wrap">
                    <div class="company-meta">
                      ${companyName}<br />
                      ${companyAddress !== "—" ? `${companyAddress}<br />` : ""}
                      ${company.phone ? `${escapeHtml(String(company.phone))}<br />` : ""}
                      ${company.email ? `${escapeHtml(String(company.email))}` : ""}
                    </div>
                    ${logoHtml}
                  </div>
                </div>
              </div>

              <div class="center-title">
                <h1>${escapeHtml(t.salaryDetailsCenterTitle)}</h1>
                <div class="month">${monthDisplay}</div>
              </div>

              <div class="employee-box">
                <div>${escapeHtml(locale === "ar" ? "اسم الموظف" : "Employee Name")}: ${employeeName}</div>
                <div>${escapeHtml(locale === "ar" ? "رقم الموظف" : "Employee Number")}: ${employeeNumber}</div>
                <div>${escapeHtml(locale === "ar" ? "القسم" : "Department")}: ${department}</div>
                <div>${escapeHtml(locale === "ar" ? "المسمى الوظيفي" : "Job Title")}: ${jobTitle}</div>
                <div>${escapeHtml(locale === "ar" ? "نوع العقد" : "Contract Type")}: ${contractType}</div>
              </div>

              <div class="meta-row">
                <div class="right">${escapeHtml(t.receivedBy)}: ${escapeHtml(locale === "ar" ? "المستخدم" : "User")} | ${generatedAtDateTime}</div>
                <div class="left">${escapeHtml(t.paymentStatus)}: ${paymentStatus}</div>
              </div>

              <div class="meta-grid">
                <table class="meta-table">
                  <thead>
                    <tr>
                      <th colspan="2">${escapeHtml(t.periodDetails)}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${periodRows || `<tr><td colspan="2" style="text-align:center;">—</td></tr>`}
                  </tbody>
                </table>

                <table class="meta-table">
                  <thead>
                    <tr>
                      <th colspan="2">${escapeHtml(t.referenceDetails)}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${referenceRows || `<tr><td colspan="2" style="text-align:center;">—</td></tr>`}
                  </tbody>
                </table>
              </div>

              <table class="salary-table">
                <thead>
                  <tr>
                    <th colspan="3" class="section-title">${escapeHtml(t.deductionDetails)}</th>
                    <th colspan="3" class="section-title">${escapeHtml(t.earningsDetails)}</th>
                  </tr>
                </thead>
                <tbody>
                  ${tableRowsHtml}

                  <tr>
                    <td class="amount-cell summary-value-cell">${escapeHtml(formatNumber(structured.summary.totalDeductions, 2))}</td>
                    <td class="item-cell summary-label-cell" colspan="2">${escapeHtml(t.totalDeductions)}</td>
                    <td class="detail-cell"></td>
                    <td class="amount-cell summary-value-cell">${escapeHtml(formatNumber(structured.summary.grossSalary, 2))}</td>
                    <td class="item-cell summary-label-cell">${escapeHtml(t.totalEarnings)}</td>
                  </tr>

                  <tr>
                    <td class="amount-cell summary-value-cell">${escapeHtml(formatNumber(structured.summary.netSalary, 2))}</td>
                    <td class="item-cell summary-label-cell" colspan="2">${escapeHtml(t.salaryNet)}</td>
                    <td class="detail-cell"></td>
                    <td class="amount-cell"></td>
                    <td class="item-cell"></td>
                  </tr>

                  <tr class="footer-space"><td colspan="6"></td></tr>

                  <tr>
                    <td colspan="3">${escapeHtml(t.bankName)} : ${bankName}</td>
                    <td colspan="3">${escapeHtml(t.paymentMethod)} : ${paymentMethod}</td>
                  </tr>
                  <tr>
                    <td colspan="3">${escapeHtml(t.iban)} : ${iban}</td>
                    <td colspan="3">${escapeHtml(t.paymentDate)} : ${paidAt}</td>
                  </tr>
                  <tr>
                    <td colspan="3">${escapeHtml(t.referenceBaseSalary)} : ${escapeHtml(formatNumber(salary.reference_base_salary ?? financialInfo.basic_salary ?? 0, 2))}</td>
                    <td colspan="3">${escapeHtml(t.generatedAt)} : ${generatedAt}</td>
                  </tr>
                  <tr>
                    <td colspan="3">${escapeHtml(t.managerSignature)} :</td>
                    <td colspan="3">${escapeHtml(t.userSignature)} :</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <script>
              window.onload = function () {
                window.focus();
                window.print();
              };
            </script>
          </body>
        </html>
      `

      printWindow.document.open()
      printWindow.document.write(html)
      printWindow.document.close()
    } catch (error) {
      console.error("Salary slip print failed:", error)
      toast.error(t.printFailed)
    } finally {
      setPrintingSlip(false)
    }
  }

  const structuredSlip = useMemo(
    () => getStructuredSlipData(selectedSlip),
    [selectedSlip]
  )

  const periodRows = useMemo(
    () => buildPeriodRows(selectedSlip, t),
    [selectedSlip, t]
  )

  const referenceRows = useMemo(
    () => buildReferenceRows(selectedSlip, t),
    [selectedSlip, t]
  )

  const currentPaymentRecord = paymentDialog.record
  const currentRemainingAmount = currentPaymentRecord
    ? getRemainingAmount(currentPaymentRecord)
    : 0
  const currentAmountValue = Number(
    String(paymentDialog.amount || "").replace(/,/g, "")
  )
  const currentAmountIsValid =
    Number.isFinite(currentAmountValue) && currentAmountValue > 0
  const currentAmountExceeded =
    currentAmountIsValid && currentAmountValue > currentRemainingAmount

  return (
    <div dir={dir} className="space-y-6">
      <Dialog open={paymentDialog.open} onOpenChange={(open) => {
        if (!open) closePaymentDialog()
      }}>
        <DialogContent dir={dir} className="sm:max-w-xl rounded-3xl p-0 overflow-hidden">
          <div className="border-b bg-muted/20 px-6 py-5">
            <DialogHeader className="space-y-2">
              <DialogTitle className="text-xl font-semibold">
                {t.paymentDialogTitle}
              </DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground">
                {t.paymentDialogDescription}
              </DialogDescription>
            </DialogHeader>
          </div>

          <div className="space-y-5 px-6 py-6">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border bg-muted/20 p-4">
                <p className="text-xs text-muted-foreground">{t.paymentDialogEmployee}</p>
                <p className="mt-1 font-semibold">
                  {currentPaymentRecord?.employee_name || "—"}
                </p>
              </div>

              <div className="rounded-2xl border bg-muted/20 p-4">
                <p className="text-xs text-muted-foreground">{t.paymentDialogRemaining}</p>
                <p className="mt-1 font-semibold tabular-nums">
                  {formatNumber(currentRemainingAmount, 2)}
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  {t.paymentDialogAmountLabel}
                </label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  dir="ltr"
                  value={paymentDialog.amount}
                  onChange={(e) =>
                    setPaymentDialog((prev) => ({
                      ...prev,
                      amount: e.target.value,
                    }))
                  }
                  className="h-11 rounded-2xl"
                />
                {currentAmountExceeded && (
                  <p className="text-xs text-red-600">{t.paymentAmountExceeded}</p>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">
                  {t.paymentDialogMethodLabel}
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant={paymentDialog.method === "BANK" ? "default" : "outline"}
                    className="h-11 rounded-2xl"
                    onClick={() =>
                      setPaymentDialog((prev) => ({
                        ...prev,
                        method: "BANK",
                      }))
                    }
                  >
                    {t.bank}
                  </Button>

                  <Button
                    type="button"
                    variant={paymentDialog.method === "CASH" ? "default" : "outline"}
                    className="h-11 rounded-2xl"
                    onClick={() =>
                      setPaymentDialog((prev) => ({
                        ...prev,
                        method: "CASH",
                        reference: "",
                      }))
                    }
                  >
                    {t.cash}
                  </Button>
                </div>
              </div>
            </div>

            {paymentDialog.method === "BANK" && (
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  {t.paymentDialogReferenceLabel}
                </label>
                <Input
                  value={paymentDialog.reference}
                  onChange={(e) =>
                    setPaymentDialog((prev) => ({
                      ...prev,
                      reference: e.target.value,
                    }))
                  }
                  placeholder={t.paymentDialogReferencePlaceholder}
                  dir="ltr"
                  className="h-11 rounded-2xl"
                />
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium">
                {t.paymentDialogNotesLabel}
              </label>
              <textarea
                value={paymentDialog.notes}
                onChange={(e) =>
                  setPaymentDialog((prev) => ({
                    ...prev,
                    notes: e.target.value,
                  }))
                }
                placeholder={t.paymentDialogNotesPlaceholder}
                className="min-h-[110px] w-full rounded-2xl border bg-background px-3 py-3 text-sm outline-none ring-0 transition placeholder:text-muted-foreground focus:border-ring"
              />
            </div>
          </div>

          <DialogFooter className="border-t bg-muted/10 px-6 py-4 sm:justify-between">
            <Button
              type="button"
              variant="outline"
              className="rounded-2xl"
              onClick={closePaymentDialog}
              disabled={
                !!currentPaymentRecord &&
                actioningKey === `pay-${currentPaymentRecord.record_id}`
              }
            >
              {t.paymentDialogCancel}
            </Button>

            <Button
              type="button"
              className="gap-2 rounded-2xl"
              onClick={() => void submitPaymentDialog()}
              disabled={
                !currentPaymentRecord ||
                actioningKey === `pay-${currentPaymentRecord?.record_id}` ||
                !currentAmountIsValid ||
                currentAmountExceeded
              }
            >
              {currentPaymentRecord &&
              actioningKey === `pay-${currentPaymentRecord.record_id}` ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Banknote className="h-4 w-4" />
              )}
              {t.paymentDialogSubmit}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => router.push("/company/payroll")}
            >
              <ArrowLeft className="h-4 w-4" />
              {t.back}
            </Button>
          </div>

          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            {t.pageTitle}
          </h1>
          <p className="text-sm text-muted-foreground md:text-base">
            {t.pageDescription}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            onClick={handlePrint}
            disabled={loading || printing || filteredRecords.length === 0}
            className="gap-2"
          >
            {printing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Printer className="h-4 w-4" />
            )}
            {printing ? t.printing : t.print}
          </Button>

          <Button
            variant="outline"
            onClick={() => void handleExportExcel()}
            disabled={loading || exportingExcel || filteredRecords.length === 0}
            className="gap-2"
          >
            {exportingExcel ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <FileSpreadsheet className="h-4 w-4" />
            )}
            {exportingExcel ? t.exportLoading : t.exportExcel}
          </Button>

          <Button
            variant="outline"
            onClick={() => void loadPageData(true)}
            disabled={refreshing || loading}
            className="gap-2"
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {t.refresh}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.totalNet}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(topStats.totalNet, 2)}
              </p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-3">
              <CircleDollarSign className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.totalPaid}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(topStats.totalPaid, 2)}
              </p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-3">
              <Banknote className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.totalRemaining}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(topStats.totalRemaining, 2)}
              </p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-3">
              <Wallet className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardContent className="flex items-center justify-between p-5">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{t.totalRecords}</p>
              <p className="text-3xl font-semibold tabular-nums">
                {formatNumber(topStats.totalRecords)}
              </p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-3">
              <Receipt className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="border-border/60 xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-base md:text-lg">{t.runSummary}</CardTitle>
          </CardHeader>

          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12 text-muted-foreground">
                <Loader2 className="me-2 h-5 w-5 animate-spin" />
                {t.loading}
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">{t.month}</p>
                  <p className="mt-1 font-semibold tabular-nums">
                    {formatMonth(summary?.month)}
                  </p>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">{t.status}</p>
                  <div className="mt-2">
                    <StatusBadge
                      text={getRunStatusLabel(summary?.status || "", locale)}
                      variant={getRunBadgeVariant(summary?.status || "")}
                    />
                  </div>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">{t.progress}</p>
                  <p className="mt-1 font-semibold tabular-nums">
                    {formatNumber(summary?.progress_percent ?? 0)}%
                  </p>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">{t.accounting}</p>
                  <p className="mt-1 font-semibold">
                    {summary?.accounting_consistency ? t.yes : t.no}
                  </p>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">{t.paidRecords}</p>
                  <p className="mt-1 font-semibold tabular-nums">
                    {formatNumber(summary?.counts?.paid_records ?? 0)}
                  </p>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">{t.partialRecords}</p>
                  <p className="mt-1 font-semibold tabular-nums">
                    {formatNumber(summary?.counts?.partial_records ?? 0)}
                  </p>
                </div>

                <div className="rounded-2xl border bg-muted/20 p-4">
                  <p className="text-xs text-muted-foreground">{t.unpaidRecords}</p>
                  <p className="mt-1 font-semibold tabular-nums">
                    {formatNumber(summary?.counts?.unpaid_records ?? 0)}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/60">
          <CardHeader className="flex flex-row items-center justify-between gap-3">
            <CardTitle className="text-base md:text-lg">{t.salarySlip}</CardTitle>

            <Button
              size="sm"
              variant="outline"
              className="gap-2"
              onClick={handlePrintSlip}
              disabled={!selectedSlip || slipLoading || printingSlip}
            >
              {printingSlip ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Printer className="h-4 w-4" />
              )}
              {printingSlip ? t.slipPrinting : t.printSlip}
            </Button>
          </CardHeader>

          <CardContent>
            {slipLoading ? (
              <div className="flex items-center justify-center py-12 text-muted-foreground">
                <Loader2 className="me-2 h-5 w-5 animate-spin" />
                {t.loading}
              </div>
            ) : !selectedSlip ? (
              <div className="rounded-2xl border border-dashed p-6 text-sm text-muted-foreground">
                {t.noSlipSelected}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="rounded-2xl border bg-muted/20 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold">
                        {selectedSlip.employee?.full_name || "—"}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground tabular-nums">
                        {t.employeeNumber}:{" "}
                        {selectedSlip.employee?.employee_number || "—"}
                      </p>
                    </div>

                    <StatusBadge
                      text={getRecordStatusLabel(
                        (selectedSlip.payment_status || "") as RecordStatus,
                        locale
                      )}
                      variant={getRecordBadgeVariant(
                        (selectedSlip.payment_status || "") as RecordStatus
                      )}
                    />
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.month}</p>
                    <p className="mt-1 font-medium tabular-nums">
                      {formatMonth(selectedSlip.month)}
                    </p>
                  </div>

                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.generatedAt}</p>
                    <p className="mt-1 font-medium tabular-nums">
                      {formatDate(selectedSlip.generated_at)}
                    </p>
                  </div>

                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.department}</p>
                    <p className="mt-1 font-medium">
                      {selectedSlip.employee?.department || "—"}
                    </p>
                  </div>

                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.jobTitle}</p>
                    <p className="mt-1 font-medium">
                      {selectedSlip.employee?.job_title || "—"}
                    </p>
                  </div>
                </div>

                {referenceRows.length > 0 && (
                  <div className="rounded-xl border p-3">
                    <p className="mb-3 text-xs font-semibold text-muted-foreground">
                      {t.referenceDetails}
                    </p>

                    <div className="grid gap-3 sm:grid-cols-2">
                      {referenceRows.map((row) => (
                        <div key={row.label} className="rounded-xl border bg-muted/20 p-3">
                          <p className="text-xs text-muted-foreground">{row.label}</p>
                          <p className="mt-1 font-medium tabular-nums">{row.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {periodRows.length > 0 && (
                  <div className="rounded-xl border p-3">
                    <p className="mb-3 text-xs font-semibold text-muted-foreground">
                      {t.periodDetails}
                    </p>

                    <div className="grid gap-3 sm:grid-cols-2">
                      {periodRows.map((row) => (
                        <div key={row.label} className="rounded-xl border bg-muted/20 p-3">
                          <p className="text-xs text-muted-foreground">{row.label}</p>
                          <p className="mt-1 font-medium tabular-nums">{row.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.baseSalary}</p>
                    <p className="mt-1 font-medium tabular-nums">
                      {formatNumber(
                        selectedSlip.salary?.prorated_base_salary ??
                          selectedSlip.salary?.base_salary ??
                          0,
                        2
                      )}
                    </p>
                  </div>

                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.allowance}</p>
                    <p className="mt-1 font-medium tabular-nums">
                      {formatNumber(
                        selectedSlip.salary?.prorated_allowance ??
                          selectedSlip.salary?.allowance ??
                          0,
                        2
                      )}
                    </p>
                  </div>

                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.bonus}</p>
                    <p className="mt-1 font-medium tabular-nums">
                      {formatNumber(selectedSlip.salary?.bonus ?? 0, 2)}
                    </p>
                  </div>

                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.overtime}</p>
                    <p className="mt-1 font-medium tabular-nums">
                      {formatNumber(selectedSlip.salary?.overtime ?? 0, 2)}
                    </p>
                  </div>

                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.deductions}</p>
                    <p className="mt-1 font-medium tabular-nums">
                      {formatNumber(selectedSlip.salary?.deductions ?? 0, 2)}
                    </p>
                  </div>

                  <div className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{t.netSalary}</p>
                    <p className="mt-1 font-semibold tabular-nums">
                      {formatNumber(selectedSlip.salary?.net_salary ?? 0, 2)}
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border p-3">
                  <p className="mb-3 text-xs font-semibold text-muted-foreground">
                    {t.earningsDetails}
                  </p>

                  {structuredSlip.earningsItems.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      {t.noDetailsAvailable}
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {structuredSlip.earningsItems.map((item, index) => (
                        <div
                          key={`${item.code || "earning"}-${index}`}
                          className="rounded-lg border bg-muted/20 p-3"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-sm font-medium">
                              {localizeSlipLabel(item.label || "—", locale)}
                            </p>
                            <p className="text-sm font-semibold tabular-nums">
                              {formatNumber(item.amount, 2)}
                            </p>
                          </div>

                          <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                            {item.days !== null && item.days !== undefined && (
                              <span className="rounded-full border px-2 py-1">
                                {t.days}: {String(item.days)}
                              </span>
                            )}
                            {item.quantity !== null && item.quantity !== undefined && (
                              <span className="rounded-full border px-2 py-1">
                                {t.quantity}: {String(item.quantity)}
                                {item.unit ? ` ${item.unit}` : ""}
                              </span>
                            )}
                            {item.notes && (
                              <span className="rounded-full border px-2 py-1">
                                {item.notes}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="rounded-xl border p-3">
                  <p className="mb-3 text-xs font-semibold text-muted-foreground">
                    {t.deductionDetails}
                  </p>

                  {structuredSlip.deductionItems.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      {t.noDetailsAvailable}
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {structuredSlip.deductionItems.map((item, index) => (
                        <div
                          key={`${item.code || "deduction"}-${index}`}
                          className="rounded-lg border bg-muted/20 p-3"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-sm font-medium">
                              {localizeSlipLabel(item.label || "—", locale)}
                            </p>
                            <p className="text-sm font-semibold tabular-nums">
                              {formatNumber(item.amount, 2)}
                            </p>
                          </div>

                          <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                            {item.days !== null && item.days !== undefined && (
                              <span className="rounded-full border px-2 py-1">
                                {t.days}: {String(item.days)}
                              </span>
                            )}
                            {item.quantity !== null && item.quantity !== undefined && (
                              <span className="rounded-full border px-2 py-1">
                                {t.quantity}: {String(item.quantity)}
                                {item.unit ? ` ${item.unit}` : ""}
                              </span>
                            )}
                            {item.notes && (
                              <span className="rounded-full border px-2 py-1">
                                {item.notes}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {structuredSlip.facts.length > 0 && (
                  <div className="rounded-xl border p-3">
                    <p className="mb-3 text-xs font-semibold text-muted-foreground">
                      {t.details}
                    </p>

                    <div className="flex flex-wrap gap-2">
                      {structuredSlip.facts.map((fact, index) => (
                        <span
                          key={`${fact.key || "fact"}-${index}`}
                          className="rounded-full border bg-muted/20 px-3 py-1 text-xs"
                        >
                          {fact.label}: {String(fact.value)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/60">
        <CardHeader className="pb-3">
          <CardTitle className="text-base md:text-lg">{t.searchTitle}</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="relative">
            <Search
              className={[
                "absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
                isArabic ? "right-3" : "left-3",
              ].join(" ")}
            />

            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t.searchPlaceholder}
              className={isArabic ? "pr-10" : "pl-10"}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { key: "ALL", label: t.all },
              { key: "PAID", label: t.paid },
              { key: "UNPAID", label: t.unpaid },
              { key: "PARTIAL", label: t.partial },
            ].map((item) => {
              const active = statusFilter === item.key

              return (
                <Button
                  key={item.key}
                  type="button"
                  size="sm"
                  variant={active ? "default" : "outline"}
                  className="rounded-xl"
                  onClick={() =>
                    setStatusFilter(
                      item.key as "ALL" | "PAID" | "UNPAID" | "PARTIAL"
                    )
                  }
                >
                  {item.label}
                </Button>
              )
            })}
          </div>

          <p className="text-xs text-muted-foreground">{t.searchHint}</p>
        </CardContent>
      </Card>

      <Card className="hidden border-border/60 lg:block">
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <CardTitle className="text-base md:text-lg">{t.recordsList}</CardTitle>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              className="gap-2"
              onClick={handlePrint}
              disabled={loading || printing || filteredRecords.length === 0}
            >
              {printing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Printer className="h-4 w-4" />
              )}
              {t.print}
            </Button>

            <Button
              size="sm"
              variant="outline"
              className="gap-2"
              onClick={() => void handleExportExcel()}
              disabled={loading || exportingExcel || filteredRecords.length === 0}
            >
              {exportingExcel ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              {t.exportExcel}
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-14 text-muted-foreground">
              <Loader2 className="me-2 h-5 w-5 animate-spin" />
              {t.loading}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className={getTableAlignClass("start", isArabic)}>
                    {t.employee}
                  </TableHead>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.status}
                  </TableHead>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.netSalary}
                  </TableHead>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.paidAmount}
                  </TableHead>
                  <TableHead className={getTableAlignClass("center", isArabic)}>
                    {t.remainingAmount}
                  </TableHead>
                  <TableHead className={getTableAlignClass("end", isArabic)}>
                    {t.actions}
                  </TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {filteredRecords.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={6}
                      className="py-12 text-center text-muted-foreground"
                    >
                      {t.noData}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredRecords.map((record) => {
                    const isRunApproved =
                      String(record.run_status || "").toUpperCase() === "APPROVED"
                    const normalizedRecordStatus = String(record.status || "").toUpperCase()
                    const isPaid = normalizedRecordStatus === "PAID"
                    const remainingAmount = getRemainingAmount(record)
                    const canPay = isRunApproved && !isPaid && remainingAmount > 0

                    return (
                      <TableRow key={record.record_id}>
                        <TableCell className={getTableAlignClass("start", isArabic)}>
                          <div className="space-y-1">
                            <p className="font-medium">{record.employee_name}</p>
                            <p className="text-xs text-muted-foreground tabular-nums">
                              #{formatNumber(record.employee_id)}
                            </p>
                          </div>
                        </TableCell>

                        <TableCell className="align-middle text-center whitespace-nowrap">
                          <StatusBadge
                            text={getRecordStatusLabel(record.status, locale)}
                            variant={getRecordBadgeVariant(record.status)}
                          />
                        </TableCell>

                        <TableCell className="align-middle text-center tabular-nums whitespace-nowrap">
                          {formatNumber(record.net_salary, 2)}
                        </TableCell>

                        <TableCell className="align-middle text-center tabular-nums whitespace-nowrap">
                          {formatNumber(record.paid_amount, 2)}
                        </TableCell>

                        <TableCell className="align-middle text-center tabular-nums whitespace-nowrap">
                          {formatNumber(record.remaining_amount, 2)}
                        </TableCell>

                        <TableCell className={getTableAlignClass("end", isArabic)}>
                          <div
                            className={[
                              "flex flex-wrap gap-2",
                              isArabic ? "justify-start" : "justify-end",
                            ].join(" ")}
                          >
                            <Button
                              size="sm"
                              variant="outline"
                              className="gap-2"
                              onClick={() => void handleViewSlip(record.record_id)}
                            >
                              <FileText className="h-4 w-4" />
                              {t.slip}
                            </Button>

                            <Button
                              size="sm"
                              variant="outline"
                              className="gap-2"
                              onClick={() => void handleViewSlip(record.record_id)}
                            >
                              <Eye className="h-4 w-4" />
                              {t.details}
                            </Button>

                            <Button
                              size="sm"
                              className="gap-2"
                              disabled={
                                !canPay ||
                                actioningKey === `pay-${record.record_id}`
                              }
                              onClick={() => openPaymentDialog(record)}
                            >
                              {actioningKey === `pay-${record.record_id}` ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Banknote className="h-4 w-4" />
                              )}
                              {t.pay}
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:hidden">
        <Card className="border-border/60">
          <CardHeader className="space-y-3">
            <CardTitle className="text-base md:text-lg">{t.recordsList}</CardTitle>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                className="gap-2"
                onClick={handlePrint}
                disabled={loading || printing || filteredRecords.length === 0}
              >
                {printing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Printer className="h-4 w-4" />
                )}
                {t.print}
              </Button>

              <Button
                size="sm"
                variant="outline"
                className="gap-2"
                onClick={() => void handleExportExcel()}
                disabled={loading || exportingExcel || filteredRecords.length === 0}
              >
                {exportingExcel ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                {t.exportExcel}
              </Button>
            </div>
          </CardHeader>

          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-14 text-muted-foreground">
                <Loader2 className="me-2 h-5 w-5 animate-spin" />
                {t.loading}
              </div>
            ) : filteredRecords.length === 0 ? (
              <div className="py-10 text-center text-sm text-muted-foreground">
                {t.noData}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredRecords.map((record) => {
                  const isRunApproved =
                    String(record.run_status || "").toUpperCase() === "APPROVED"
                  const normalizedRecordStatus = String(record.status || "").toUpperCase()
                  const isPaid = normalizedRecordStatus === "PAID"
                  const remainingAmount = getRemainingAmount(record)
                  const canPay = isRunApproved && !isPaid && remainingAmount > 0

                  return (
                    <div
                      key={record.record_id}
                      className="rounded-2xl border border-border/60 bg-background p-4 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <Receipt className="h-4 w-4 shrink-0 text-muted-foreground" />
                            <h3 className="truncate font-semibold">
                              {record.employee_name}
                            </h3>
                          </div>
                          <p className="text-sm text-muted-foreground tabular-nums">
                            #{formatNumber(record.record_id)}
                          </p>
                        </div>

                        <StatusBadge
                          text={getRecordStatusLabel(record.status, locale)}
                          variant={getRecordBadgeVariant(record.status)}
                        />
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.netSalary}</p>
                          <p className="mt-1 font-medium tabular-nums">
                            {formatNumber(record.net_salary, 2)}
                          </p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.paidAmount}</p>
                          <p className="mt-1 font-medium tabular-nums">
                            {formatNumber(record.paid_amount, 2)}
                          </p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.remainingAmount}</p>
                          <p className="mt-1 font-medium tabular-nums">
                            {formatNumber(record.remaining_amount, 2)}
                          </p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.status}</p>
                          <p className="mt-1 font-medium">
                            {getRecordStatusLabel(record.status, locale)}
                          </p>
                        </div>
                      </div>

                      <div className="mt-4 flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          className="flex-1 gap-2"
                          onClick={() => void handleViewSlip(record.record_id)}
                        >
                          <FileText className="h-4 w-4" />
                          {t.slip}
                        </Button>

                        <Button
                          variant="outline"
                          className="flex-1 gap-2"
                          onClick={() => void handleViewSlip(record.record_id)}
                        >
                          <Eye className="h-4 w-4" />
                          {t.details}
                        </Button>

                        <Button
                          className="w-full gap-2 sm:w-auto"
                          disabled={
                            !canPay ||
                            actioningKey === `pay-${record.record_id}`
                          }
                          onClick={() => openPaymentDialog(record)}
                        >
                          {actioningKey === `pay-${record.record_id}` ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Banknote className="h-4 w-4" />
                          )}
                          {t.pay}
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <p className="text-xs text-muted-foreground">{t.printHint}</p>
    </div>
  )
}