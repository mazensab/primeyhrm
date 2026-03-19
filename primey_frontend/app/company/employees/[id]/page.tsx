"use client"

import Image from "next/image"
import Link from "next/link"
import { useEffect, useMemo, useState, type ComponentType } from "react"
import { useParams, useRouter } from "next/navigation"
import {
  ArrowLeft,
  BadgeCheck,
  Briefcase,
  Building2,
  CalendarDays,
  Check,
  CreditCard,
  Fingerprint,
  IdCard,
  Landmark,
  Loader2,
  Mail,
  Phone,
  ShieldCheck,
  User2,
  Wallet,
  Clock3,
  Activity,
  CircleDollarSign,
  MapPinned,
  UserSquare2,
  Pencil,
  Save,
  X,
  FileText,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ======================================================
// Types
// ======================================================

type EmployeeProfile = {
  full_name?: string | null
  email?: string | null
  mobile_number?: string | null
  avatar?: string | null
  username?: string | null
  arabic_name?: string | null
  date_of_birth?: string | null
  nationality?: string | null
  gender?: string | null
  national_id?: string | null
  national_id_issue_date?: string | null
  national_id_expiry_date?: string | null
  passport_number?: string | null
  passport_issue_date?: string | null
  passport_expiry_date?: string | null
  employment_type?: string | null
  employee_number?: string | null
  join_date?: string | null
  work_start_date?: string | null
  probation_end_date?: string | null
  end_date?: string | null
  gosi_number?: string | null
}

type FinancialInfo = {
  basic_salary?: number | null
  housing_allowance?: number | null
  transport_allowance?: number | null
  food_allowance?: number | null
  other_allowances?: number | null
  is_gosi_enabled?: boolean | null
  is_tax_enabled?: boolean | null
  bank_name?: string | null
  iban?: string | null
}

type PayrollRecord = {
  id: number
  month?: string | null
  base_salary?: number | null
  allowance?: number | null
  bonus?: number | null
  overtime?: number | null
  deductions?: number | null
  net_salary?: number | null
  paid_amount?: number | null
  remaining_amount?: number | null
  is_fully_paid?: boolean
  status?: string | null
}

type Branch = {
  id: number
  name: string
  biotime_code?: string | null
}

type LookupItem = {
  id: number
  name: string
}

type WorkSchedule = {
  id: number
  name: string
  is_active: boolean
}

type BiotimeInfo = {
  employee_id?: string | null
  full_name?: string | null
  is_active?: boolean | null
  department?: string | null
  enrolled_fingers?: number | null
  card_number?: string | null
  photo_url?: string | null
  created_at?: string | null
  updated_at?: string | null
}

type EmployeeDetailResponse = {
  id: number
  full_name?: string | null
  name?: string | null
  email?: string | null
  phone?: string | null
  avatar?: string | null
  photo_url?: string | null
  role?: string | null
  status_label?: string | null
  status?: string | null
  biotime_code?: string | null
  biotime?: BiotimeInfo | null
  financial_info?: FinancialInfo | null
  payroll_records?: PayrollRecord[]
  profile?: EmployeeProfile
  department?: LookupItem | null
  job_title?: LookupItem | null
  branches?: Branch[]
  default_work_schedule?: WorkSchedule | null
  created_at?: string | null
  updated_at?: string | null
}

type PersonalFormState = {
  full_name: string
  arabic_name: string
  email: string
  mobile_number: string
  username: string
  nationality: string
  gender: string
  date_of_birth: string
  gosi_number: string
}

type EmploymentFormState = {
  employee_number: string
  employment_type: string
  department_id: string
  job_title_id: string
  work_schedule_id: string
  work_schedule_status: string
  join_date: string
  work_start_date: string
  probation_end_date: string
  end_date: string
}

type DocumentsFormState = {
  national_id: string
  national_id_issue_date: string
  national_id_expiry_date: string
  passport_number: string
  passport_issue_date: string
  passport_expiry_date: string
}

type FinancialFormState = {
  basic_salary: string
  housing_allowance: string
  transport_allowance: string
  food_allowance: string
  other_allowances: string
  bank_name: string
  iban: string
  is_gosi_enabled: string
  is_tax_enabled: string
}

// ======================================================
// Helpers
// ======================================================

function formatDate(value?: string | null) {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }

  return date.toLocaleDateString("en-CA")
}

function toInputDate(value?: string | null) {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value).slice(0, 10)
  }
  return date.toLocaleDateString("en-CA")
}

function formatDateTime(value?: string | null) {
  if (!value) return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }

  return `${date.toLocaleDateString("en-CA")} ${date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  })}`
}

function formatMoney(value?: number | null) {
  const amount = Number(value || 0)
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

function toEditableMoney(value?: number | null) {
  if (value === null || value === undefined) return ""
  return String(value)
}

function statusVariant(status?: string | null) {
  const normalized = String(status || "").toUpperCase()

  if (normalized === "ACTIVE" || normalized === "PAID") return "default"
  if (
    normalized === "INACTIVE" ||
    normalized === "UNPAID" ||
    normalized === "FAILED" ||
    normalized === "CANCELLED"
  ) {
    return "destructive"
  }

  return "secondary"
}

function getInitials(name?: string | null) {
  const clean = String(name || "").trim()
  if (!clean) return "EM"

  const parts = clean.split(/\s+/).filter(Boolean)
  return parts
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("")
}

function toNullableString(value: string) {
  const clean = value.trim()
  return clean === "" ? null : clean
}

function toNullableNumber(value: string) {
  const clean = value.trim()
  if (clean === "") return null
  const parsed = Number(clean)
  return Number.isFinite(parsed) ? parsed : null
}

function boolFromSelect(value: string) {
  return value === "true"
}

function normalizeLookupItems(input: unknown): LookupItem[] {
  if (!Array.isArray(input)) return []

  return input
    .map((item: any) => {
      const id = Number(item?.id)
      const name =
        item?.name ||
        item?.title ||
        item?.label ||
        item?.department_name ||
        item?.job_title_name

      if (!Number.isFinite(id) || !String(name || "").trim()) return null

      return {
        id,
        name: String(name).trim(),
      }
    })
    .filter(Boolean) as LookupItem[]
}

function normalizeBranches(input: unknown): Branch[] {
  if (!Array.isArray(input)) return []

  return input
    .map((item: any) => {
      const id = Number(item?.id)
      const name =
        item?.name ||
        item?.branch_name ||
        item?.title

      if (!Number.isFinite(id) || !String(name || "").trim()) return null

      return {
        id,
        name: String(name).trim(),
        biotime_code: item?.biotime_code || null,
      }
    })
    .filter(Boolean) as Branch[]
}

function normalizeWorkSchedules(input: unknown): WorkSchedule[] {
  if (!Array.isArray(input)) return []

  return input
    .map((item: any) => {
      const id = Number(item?.id)
      const name =
        item?.name ||
        item?.title ||
        item?.schedule_name

      if (!Number.isFinite(id) || !String(name || "").trim()) return null

      return {
        id,
        name: String(name).trim(),
        is_active: Boolean(item?.is_active ?? true),
      }
    })
    .filter(Boolean) as WorkSchedule[]
}

function extractArrayByKeys(payload: any, keys: string[]) {
  if (!payload || typeof payload !== "object") return []

  for (const key of keys) {
    if (Array.isArray(payload?.[key])) return payload[key]
  }

  if (payload?.data && typeof payload.data === "object") {
    for (const key of keys) {
      if (Array.isArray(payload.data?.[key])) return payload.data[key]
    }
  }

  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.items)) return payload.items
  if (Array.isArray(payload)) return payload

  return []
}

async function fetchLookupWithFallback<T>({
  urls,
  keys,
  normalizer,
}: {
  urls: string[]
  keys: string[]
  normalizer: (input: unknown) => T[]
}): Promise<T[]> {
  for (const url of urls) {
    try {
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
        cache: "no-store",
      })

      if (!response.ok) continue

      const payload = await response.json().catch(() => null)
      const raw = extractArrayByKeys(payload, keys)
      const normalized = normalizer(raw)

      if (normalized.length > 0) {
        return normalized
      }
    } catch (error) {
      console.error(`Lookup fetch failed for ${url}:`, error)
    }
  }

  return []
}

function DetailItem({
  icon: Icon,
  label,
  value,
}: {
  icon: ComponentType<{ className?: string }>
  label: string
  value?: string | number | null
}) {
  return (
    <div className="rounded-2xl border bg-background/70 p-4">
      <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span>{label}</span>
      </div>
      <div className="break-words text-sm font-semibold text-foreground">
        {value !== undefined && value !== null && String(value).trim() !== ""
          ? String(value)
          : "—"}
      </div>
    </div>
  )
}

function EditableField({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  type?: string
  placeholder?: string
}) {
  return (
    <div className="rounded-2xl border bg-background/70 p-4">
      <div className="mb-2 text-xs font-medium text-muted-foreground">{label}</div>
      <Input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder || label}
        className="rounded-xl"
      />
    </div>
  )
}

function EditableSelect({
  label,
  value,
  onChange,
  items,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  items: { label: string; value: string }[]
}) {
  return (
    <div className="rounded-2xl border bg-background/70 p-4">
      <div className="mb-2 text-xs font-medium text-muted-foreground">{label}</div>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="rounded-xl">
          <SelectValue placeholder={label} />
        </SelectTrigger>
        <SelectContent>
          {items.map((item) => (
            <SelectItem key={item.value} value={item.value}>
              {item.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon: Icon,
  footer,
}: {
  title: string
  value: string
  icon: ComponentType<{ className?: string }>
  footer?: string
}) {
  return (
    <Card className="rounded-3xl border-border/60 shadow-sm">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="mt-2 text-2xl font-bold tracking-tight">{value}</p>
            {footer ? (
              <p className="mt-2 text-xs text-muted-foreground">{footer}</p>
            ) : null}
          </div>
          <div className="rounded-2xl border bg-muted/50 p-3">
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function SectionHeaderActions({
  isEditing,
  saving,
  onEdit,
  onCancel,
  onSave,
}: {
  isEditing: boolean
  saving: boolean
  onEdit: () => void
  onCancel: () => void
  onSave: () => void
}) {
  if (!isEditing) {
    return (
      <Button variant="outline" className="rounded-2xl" onClick={onEdit}>
        <Pencil className="me-2 h-4 w-4" />
        تعديل
      </Button>
    )
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        variant="outline"
        className="rounded-2xl"
        onClick={onCancel}
        disabled={saving}
      >
        <X className="me-2 h-4 w-4" />
        إلغاء
      </Button>
      <Button className="rounded-2xl" onClick={onSave} disabled={saving}>
        {saving ? (
          <Loader2 className="me-2 h-4 w-4 animate-spin" />
        ) : (
          <Save className="me-2 h-4 w-4" />
        )}
        حفظ
      </Button>
    </div>
  )
}

// ======================================================
// Page
// ======================================================

export default function EmployeeDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const employeeId = Array.isArray(params?.id) ? params.id[0] : params?.id

  const [data, setData] = useState<EmployeeDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [pushingBiotime, setPushingBiotime] = useState(false)
  const [biotimeLinked, setBiotimeLinked] = useState(false)

  const [loadingLookups, setLoadingLookups] = useState(false)
  const [availableBranches, setAvailableBranches] = useState<Branch[]>([])
  const [departmentOptions, setDepartmentOptions] = useState<LookupItem[]>([])
  const [jobTitleOptions, setJobTitleOptions] = useState<LookupItem[]>([])
  const [workScheduleOptions, setWorkScheduleOptions] = useState<WorkSchedule[]>([])

  const [editingPersonal, setEditingPersonal] = useState(false)
  const [editingEmployment, setEditingEmployment] = useState(false)
  const [editingDocuments, setEditingDocuments] = useState(false)
  const [editingFinancial, setEditingFinancial] = useState(false)
  const [editingBranches, setEditingBranches] = useState(false)

  const [savingPersonal, setSavingPersonal] = useState(false)
  const [savingEmployment, setSavingEmployment] = useState(false)
  const [savingDocuments, setSavingDocuments] = useState(false)
  const [savingFinancial, setSavingFinancial] = useState(false)
  const [savingBranches, setSavingBranches] = useState(false)

  const [selectedBranchIds, setSelectedBranchIds] = useState<string[]>([])

  const [personalForm, setPersonalForm] = useState<PersonalFormState>({
    full_name: "",
    arabic_name: "",
    email: "",
    mobile_number: "",
    username: "",
    nationality: "",
    gender: "",
    date_of_birth: "",
    gosi_number: "",
  })

  const [employmentForm, setEmploymentForm] = useState<EmploymentFormState>({
    employee_number: "",
    employment_type: "",
    department_id: "",
    job_title_id: "",
    work_schedule_id: "",
    work_schedule_status: "ACTIVE",
    join_date: "",
    work_start_date: "",
    probation_end_date: "",
    end_date: "",
  })

  const [documentsForm, setDocumentsForm] = useState<DocumentsFormState>({
    national_id: "",
    national_id_issue_date: "",
    national_id_expiry_date: "",
    passport_number: "",
    passport_issue_date: "",
    passport_expiry_date: "",
  })

  const [financialForm, setFinancialForm] = useState<FinancialFormState>({
    basic_salary: "",
    housing_allowance: "",
    transport_allowance: "",
    food_allowance: "",
    other_allowances: "",
    bank_name: "",
    iban: "",
    is_gosi_enabled: "false",
    is_tax_enabled: "false",
  })

  const fillFormsFromData = (payload: EmployeeDetailResponse) => {
    const profile = payload.profile || {}
    const financial = payload.financial_info || null

    setPersonalForm({
      full_name: profile.full_name || payload.full_name || "",
      arabic_name: profile.arabic_name || "",
      email: profile.email || payload.email || "",
      mobile_number: profile.mobile_number || payload.phone || "",
      username: profile.username || "",
      nationality: profile.nationality || "",
      gender: profile.gender || "",
      date_of_birth: toInputDate(profile.date_of_birth),
      gosi_number: profile.gosi_number || "",
    })

    setEmploymentForm({
      employee_number: profile.employee_number || "",
      employment_type: profile.employment_type || "",
      department_id: payload.department?.id ? String(payload.department.id) : "",
      job_title_id: payload.job_title?.id ? String(payload.job_title.id) : "",
      work_schedule_id: payload.default_work_schedule?.id
        ? String(payload.default_work_schedule.id)
        : "",
      work_schedule_status: payload.default_work_schedule?.is_active ? "ACTIVE" : "INACTIVE",
      join_date: toInputDate(profile.join_date),
      work_start_date: toInputDate(profile.work_start_date),
      probation_end_date: toInputDate(profile.probation_end_date),
      end_date: toInputDate(profile.end_date),
    })

    setSelectedBranchIds((payload.branches || []).map((branch) => String(branch.id)))

    setDocumentsForm({
      national_id: profile.national_id || "",
      national_id_issue_date: toInputDate(profile.national_id_issue_date),
      national_id_expiry_date: toInputDate(profile.national_id_expiry_date),
      passport_number: profile.passport_number || "",
      passport_issue_date: toInputDate(profile.passport_issue_date),
      passport_expiry_date: toInputDate(profile.passport_expiry_date),
    })

    setFinancialForm({
      basic_salary: toEditableMoney(financial?.basic_salary),
      housing_allowance: toEditableMoney(financial?.housing_allowance),
      transport_allowance: toEditableMoney(financial?.transport_allowance),
      food_allowance: toEditableMoney(financial?.food_allowance),
      other_allowances: toEditableMoney(financial?.other_allowances),
      bank_name: financial?.bank_name || "",
      iban: financial?.iban || "",
      is_gosi_enabled: String(Boolean(financial?.is_gosi_enabled)),
      is_tax_enabled: String(Boolean(financial?.is_tax_enabled)),
    })

    setBiotimeLinked(Boolean(payload?.biotime || payload?.biotime_code))
  }

  const fetchEmployee = async (showLoader = true) => {
    if (!employeeId) return

    try {
      if (showLoader) setLoading(true)
      else setRefreshing(true)

      const response = await fetch(
        `${API_BASE}/api/company/employees/${employeeId}/`,
        {
          method: "GET",
          credentials: "include",
          headers: {
            Accept: "application/json",
          },
          cache: "no-store",
        }
      )

      const payload = await response.json().catch(() => null)

      if (!response.ok) {
        throw new Error(
          payload?.message || payload?.error || "Failed to load employee details"
        )
      }

      setData((prev) => {
        if (!prev) return payload

        const payloadHasBiotime = Boolean(payload?.biotime || payload?.biotime_code)
        const prevHasBiotime = Boolean(prev?.biotime || prev?.biotime_code || biotimeLinked)

        if (!payloadHasBiotime && prevHasBiotime) {
          return {
            ...payload,
            biotime_code: payload?.biotime_code || prev?.biotime_code || null,
            biotime: payload?.biotime || prev?.biotime || null,
          }
        }

        return payload
      })

      fillFormsFromData(payload)
    } catch (error) {
      console.error("Employee details error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر تحميل تفاصيل الموظف"
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const loadLookups = async () => {
    try {
      setLoadingLookups(true)

      const [branchesResult, departmentsResult, jobTitlesResult, schedulesResult] =
        await Promise.all([
          fetchLookupWithFallback<Branch>({
            urls: [`${API_BASE}/api/company/branches/list/`],
            keys: ["branches"],
            normalizer: normalizeBranches,
          }),
          fetchLookupWithFallback<LookupItem>({
            urls: [`${API_BASE}/api/company/departments/list/`],
            keys: ["departments"],
            normalizer: normalizeLookupItems,
          }),
          fetchLookupWithFallback<LookupItem>({
            urls: [`${API_BASE}/api/company/job-titles/list/`],
            keys: ["job_titles"],
            normalizer: normalizeLookupItems,
          }),
          fetchLookupWithFallback<WorkSchedule>({
            urls: [`${API_BASE}/api/company/work-schedules/`],
            keys: ["schedules"],
            normalizer: normalizeWorkSchedules,
          }),
        ])

      setAvailableBranches(branchesResult)
      setDepartmentOptions(departmentsResult)
      setJobTitleOptions(jobTitlesResult)
      setWorkScheduleOptions(schedulesResult)
    } catch (error) {
      console.error("Lookup loading error:", error)
    } finally {
      setLoadingLookups(false)
    }
  }

  const handlePushEmployeeToBiotime = async () => {
    if (!employeeId) {
      toast.error("معرّف الموظف غير متوفر")
      return
    }

    try {
      setPushingBiotime(true)

      const response = await fetch(
        `${API_BASE}/api/company/biotime/push-employee/${employeeId}/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            Accept: "application/json",
          },
        }
      )

      const payload = await response.json().catch(() => null)

      if (!response.ok) {
        throw new Error(
          payload?.message || payload?.error || "تعذر ربط الموظف مع BioTime"
        )
      }

      setBiotimeLinked(true)

      setData((prev) => {
        if (!prev) return prev

        return {
          ...prev,
          biotime_code:
            payload?.biotime_code ||
            payload?.employee_code ||
            prev.biotime_code ||
            String(prev.id),
          biotime: {
            employee_id:
              payload?.biotime_code ||
              payload?.employee_code ||
              prev.biotime?.employee_id ||
              String(prev.id),
            full_name:
              payload?.full_name ||
              prev.profile?.full_name ||
              prev.full_name ||
              prev.name ||
              "—",
            is_active: true,
            department:
              payload?.department ||
              prev.department?.name ||
              prev.biotime?.department ||
              "—",
            enrolled_fingers: prev.biotime?.enrolled_fingers ?? 0,
            card_number: prev.biotime?.card_number || null,
            photo_url:
              prev.biotime?.photo_url ||
              prev.photo_url ||
              prev.avatar ||
              prev.profile?.avatar ||
              null,
            created_at: prev.biotime?.created_at || new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        }
      })

      toast.success(payload?.message || "تم ربط الموظف مع BioTime بنجاح")

      await fetchEmployee(false)
    } catch (error) {
      console.error("Push employee to BioTime error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر ربط الموظف مع BioTime"
      )
    } finally {
      setPushingBiotime(false)
    }
  }

  useEffect(() => {
    fetchEmployee(true)
    loadLookups()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employeeId])

  const profile = data?.profile || {}
  const financial = data?.financial_info || null
  const payroll = data?.payroll_records || []
  const branches = data?.branches || []

  const hasBiotimeLink = Boolean(data?.biotime || data?.biotime_code || biotimeLinked)

  const biotime: BiotimeInfo | null = data?.biotime
    ? data.biotime
    : hasBiotimeLink
      ? {
          employee_id: data?.biotime_code || String(data?.id || ""),
          full_name:
            data?.profile?.full_name ||
            data?.full_name ||
            data?.name ||
            "—",
          is_active: true,
          department: data?.department?.name || "—",
          enrolled_fingers: 0,
          card_number: null,
          photo_url:
            data?.photo_url ||
            data?.avatar ||
            data?.profile?.avatar ||
            null,
          created_at: data?.created_at || null,
          updated_at: data?.updated_at || null,
        }
      : null

  const selectedDepartment = useMemo(
    () =>
      departmentOptions.find(
        (item) => String(item.id) === String(employmentForm.department_id)
      ) || data?.department || null,
    [departmentOptions, employmentForm.department_id, data?.department]
  )

  const selectedJobTitle = useMemo(
    () =>
      jobTitleOptions.find(
        (item) => String(item.id) === String(employmentForm.job_title_id)
      ) || data?.job_title || null,
    [jobTitleOptions, employmentForm.job_title_id, data?.job_title]
  )

  const selectedWorkSchedule = useMemo(
    () =>
      workScheduleOptions.find(
        (item) => String(item.id) === String(employmentForm.work_schedule_id)
      ) || data?.default_work_schedule || null,
    [workScheduleOptions, employmentForm.work_schedule_id, data?.default_work_schedule]
  )

  const linkedBranchesPreview = useMemo(() => {
    if (editingBranches && availableBranches.length > 0) {
      return availableBranches.filter((branch) =>
        selectedBranchIds.includes(String(branch.id))
      )
    }
    return branches
  }, [editingBranches, availableBranches, selectedBranchIds, branches])

  const totalAllowances = useMemo(() => {
    return (
      Number(financial?.housing_allowance || 0) +
      Number(financial?.transport_allowance || 0) +
      Number(financial?.food_allowance || 0) +
      Number(financial?.other_allowances || 0)
    )
  }, [financial])

  const latestPayroll = payroll[0] || null
  const avatar =
    data?.avatar || data?.photo_url || profile?.avatar || biotime?.photo_url || ""

  const saveSection = async (
    section: "personal" | "employment" | "documents" | "financial" | "branches",
    body: Record<string, unknown>
  ) => {
    if (!employeeId) {
      throw new Error("Employee id is missing")
    }

    const endpoints = [
      `${API_BASE}/api/company/employees/${employeeId}/update/`,
      `${API_BASE}/api/company/employees/${employeeId}/`,
    ]

    let lastError = "تعذر حفظ التعديلات"

    for (const url of endpoints) {
      for (const method of ["PATCH", "PUT"]) {
        try {
          const response = await fetch(url, {
            method,
            credentials: "include",
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
            },
            body: JSON.stringify({
              section,
              ...body,
            }),
          })

          const payload = await response.json().catch(() => null)

          if (response.ok) {
            if (payload && typeof payload === "object") {
              const merged = {
                ...(data || {}),
                ...(payload?.employee || {}),
                ...(payload?.data || {}),
                ...(payload?.result || {}),
                ...(payload?.updated_employee || {}),
              } as EmployeeDetailResponse

              setData(merged)
              fillFormsFromData(merged)
            } else if (data) {
              fillFormsFromData(data)
            }

            return
          }

          if (response.status !== 404 && response.status !== 405) {
            lastError =
              payload?.message ||
              payload?.error ||
              `Save failed (${response.status})`
            throw new Error(lastError)
          }
        } catch (error) {
          if (
            error instanceof Error &&
            !error.message.includes("Save failed (404)") &&
            !error.message.includes("Save failed (405)")
          ) {
            throw error
          }
        }
      }
    }

    throw new Error(lastError)
  }

  const handleSavePersonal = async () => {
    try {
      setSavingPersonal(true)

      await saveSection("personal", {
        profile: {
          full_name: toNullableString(personalForm.full_name),
          arabic_name: toNullableString(personalForm.arabic_name),
          email: toNullableString(personalForm.email),
          mobile_number: toNullableString(personalForm.mobile_number),
          username: toNullableString(personalForm.username),
          nationality: toNullableString(personalForm.nationality),
          gender: toNullableString(personalForm.gender),
          date_of_birth: toNullableString(personalForm.date_of_birth),
          gosi_number: toNullableString(personalForm.gosi_number),
        },
      })

      toast.success("تم حفظ البيانات الشخصية بنجاح")
      setEditingPersonal(false)
      await fetchEmployee(false)
    } catch (error) {
      console.error("Save personal error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر حفظ البيانات الشخصية"
      )
    } finally {
      setSavingPersonal(false)
    }
  }

  const handleSaveEmployment = async () => {
    try {
      setSavingEmployment(true)

      await saveSection("employment", {
        profile: {
          employee_number: toNullableString(employmentForm.employee_number),
          employment_type: toNullableString(employmentForm.employment_type),
          join_date: toNullableString(employmentForm.join_date),
          work_start_date: toNullableString(employmentForm.work_start_date),
          probation_end_date: toNullableString(employmentForm.probation_end_date),
          end_date: toNullableString(employmentForm.end_date),
        },
        department_id: toNullableNumber(employmentForm.department_id),
        department_name: selectedDepartment?.name || null,
        job_title_id: toNullableNumber(employmentForm.job_title_id),
        job_title_name: selectedJobTitle?.name || null,
        work_schedule_id: toNullableNumber(employmentForm.work_schedule_id),
        work_schedule_name: selectedWorkSchedule?.name || null,
        work_schedule_status: employmentForm.work_schedule_status,
      })

      toast.success("تم حفظ بيانات التوظيف بنجاح")
      setEditingEmployment(false)
      await fetchEmployee(false)
    } catch (error) {
      console.error("Save employment error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر حفظ بيانات التوظيف"
      )
    } finally {
      setSavingEmployment(false)
    }
  }

  const handleSaveBranches = async () => {
    try {
      setSavingBranches(true)

      const numericBranchIds = selectedBranchIds
        .map((id) => Number(id))
        .filter((id) => Number.isFinite(id))

      await saveSection("branches", {
        branch_ids: numericBranchIds,
        selected_branch_ids: numericBranchIds,
        branches_ids: numericBranchIds,
      })

      toast.success("تم حفظ الفروع المرتبطة بنجاح")
      setEditingBranches(false)
      await fetchEmployee(false)
    } catch (error) {
      console.error("Save branches error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر حفظ الفروع المرتبطة"
      )
    } finally {
      setSavingBranches(false)
    }
  }

  const handleSaveDocuments = async () => {
    try {
      setSavingDocuments(true)

      await saveSection("documents", {
        profile: {
          national_id: toNullableString(documentsForm.national_id),
          national_id_issue_date: toNullableString(documentsForm.national_id_issue_date),
          national_id_expiry_date: toNullableString(documentsForm.national_id_expiry_date),
          passport_number: toNullableString(documentsForm.passport_number),
          passport_issue_date: toNullableString(documentsForm.passport_issue_date),
          passport_expiry_date: toNullableString(documentsForm.passport_expiry_date),
        },
      })

      toast.success("تم حفظ الوثائق بنجاح")
      setEditingDocuments(false)
      await fetchEmployee(false)
    } catch (error) {
      console.error("Save documents error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر حفظ الوثائق"
      )
    } finally {
      setSavingDocuments(false)
    }
  }

  const handleSaveFinancial = async () => {
    try {
      setSavingFinancial(true)

      await saveSection("financial", {
        financial_info: {
          basic_salary: toNullableNumber(financialForm.basic_salary),
          housing_allowance: toNullableNumber(financialForm.housing_allowance),
          transport_allowance: toNullableNumber(financialForm.transport_allowance),
          food_allowance: toNullableNumber(financialForm.food_allowance),
          other_allowances: toNullableNumber(financialForm.other_allowances),
          bank_name: toNullableString(financialForm.bank_name),
          iban: toNullableString(financialForm.iban),
          is_gosi_enabled: boolFromSelect(financialForm.is_gosi_enabled),
          is_tax_enabled: boolFromSelect(financialForm.is_tax_enabled),
        },
      })

      toast.success("تم حفظ البيانات المالية بنجاح")
      setEditingFinancial(false)
      await fetchEmployee(false)
    } catch (error) {
      console.error("Save financial error:", error)
      toast.error(
        error instanceof Error ? error.message : "تعذر حفظ البيانات المالية"
      )
    } finally {
      setSavingFinancial(false)
    }
  }

  const cancelPersonal = () => {
    if (data) fillFormsFromData(data)
    setEditingPersonal(false)
  }

  const cancelEmployment = () => {
    if (data) fillFormsFromData(data)
    setEditingEmployment(false)
  }

  const cancelBranches = () => {
    if (data) fillFormsFromData(data)
    setEditingBranches(false)
  }

  const cancelDocuments = () => {
    if (data) fillFormsFromData(data)
    setEditingDocuments(false)
  }

  const cancelFinancial = () => {
    if (data) fillFormsFromData(data)
    setEditingFinancial(false)
  }

  const toggleBranchSelection = (branchId: number) => {
    const value = String(branchId)
    setSelectedBranchIds((prev) =>
      prev.includes(value)
        ? prev.filter((item) => item !== value)
        : [...prev, value]
    )
  }

  if (loading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="flex items-center gap-3 rounded-2xl border bg-background px-5 py-4 shadow-sm">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm font-medium">جاري تحميل تفاصيل الموظف...</span>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <Card className="rounded-3xl border-border/60">
          <CardContent className="flex flex-col items-center justify-center gap-4 p-10 text-center">
            <UserSquare2 className="h-12 w-12 text-muted-foreground" />
            <div>
              <h2 className="text-xl font-bold">تعذر تحميل بيانات الموظف</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                تحقق من المسار أو من صلاحية الوصول للشركة الحالية.
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <Button onClick={() => fetchEmployee(true)}>إعادة المحاولة</Button>
              <Button variant="outline" onClick={() => router.push("/company/employees")}>
                العودة إلى الموظفين
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* ================================================== */}
      {/* Header */}
      {/* ================================================== */}
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="icon"
            className="rounded-2xl"
            onClick={() => router.push("/company/employees")}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight">
                تفاصيل الموظف
              </h1>
              <Badge variant={statusVariant(data?.status)}>
                {data?.status || "—"}
              </Badge>
              {data?.role ? <Badge variant="secondary">{data.role}</Badge> : null}
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              عرض شامل لبيانات الموظف، التوظيف، الراتب، والربط مع BioTime.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="outline"
            className="rounded-2xl"
            onClick={() => fetchEmployee(false)}
            disabled={refreshing}
          >
            {refreshing ? (
              <Loader2 className="me-2 h-4 w-4 animate-spin" />
            ) : (
              <Activity className="me-2 h-4 w-4" />
            )}
            تحديث
          </Button>

          <Button asChild className="rounded-2xl">
            <Link href="/company/profile">بروفايل المستخدم</Link>
          </Button>
        </div>
      </div>

      {/* ================================================== */}
      {/* Hero */}
      {/* ================================================== */}
      <Card className="overflow-hidden rounded-[28px] border-border/60 shadow-sm">
        <CardContent className="p-0">
          <div className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-background to-background" />
            <div className="relative flex flex-col gap-6 p-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex min-w-0 items-center gap-4">
                <Avatar className="h-20 w-20 rounded-3xl border shadow-sm">
                  <AvatarImage
                    src={avatar}
                    alt={profile?.full_name || data?.full_name || "Employee"}
                  />
                  <AvatarFallback className="rounded-3xl text-lg font-bold">
                    {getInitials(profile?.full_name || data?.full_name)}
                  </AvatarFallback>
                </Avatar>

                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="truncate text-2xl font-bold">
                      {profile?.full_name || data?.full_name || "—"}
                    </h2>
                    {hasBiotimeLink ? (
                      <Badge className="rounded-full">
                        <BadgeCheck className="me-1 h-3.5 w-3.5" />
                        BioTime Active
                      </Badge>
                    ) : null}
                  </div>

                  {profile?.arabic_name ? (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {profile.arabic_name}
                    </p>
                  ) : null}

                  <div className="mt-3 flex flex-wrap gap-2">
                    {profile?.employee_number ? (
                      <Badge variant="secondary" className="rounded-full">
                        Employee No: {profile.employee_number}
                      </Badge>
                    ) : null}

                    {data?.department?.name ? (
                      <Badge variant="secondary" className="rounded-full">
                        {data.department.name}
                      </Badge>
                    ) : null}

                    {data?.job_title?.name ? (
                      <Badge variant="secondary" className="rounded-full">
                        {data.job_title.name}
                      </Badge>
                    ) : null}

                    {profile?.employment_type ? (
                      <Badge variant="secondary" className="rounded-full">
                        {profile.employment_type}
                      </Badge>
                    ) : null}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:min-w-[440px]">
                <div className="rounded-3xl border bg-background/80 p-4 shadow-sm">
                  <p className="text-xs text-muted-foreground">البريد الإلكتروني</p>
                  <p className="mt-2 truncate text-sm font-semibold">
                    {profile?.email || data?.email || "—"}
                  </p>
                </div>

                <div className="rounded-3xl border bg-background/80 p-4 shadow-sm">
                  <p className="text-xs text-muted-foreground">رقم الجوال</p>
                  <p className="mt-2 text-sm font-semibold">
                    {profile?.mobile_number || data?.phone || "—"}
                  </p>
                </div>

                <div className="rounded-3xl border bg-background/80 p-4 shadow-sm">
                  <p className="text-xs text-muted-foreground">اسم المستخدم</p>
                  <p className="mt-2 text-sm font-semibold">
                    {profile?.username || "—"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ================================================== */}
      {/* Stats */}
      {/* ================================================== */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="الراتب الأساسي"
          value={formatMoney(financial?.basic_salary)}
          icon={CircleDollarSign}
          footer="SAR"
        />
        <StatCard
          title="إجمالي البدلات"
          value={formatMoney(totalAllowances)}
          icon={Wallet}
          footer="SAR"
        />
        <StatCard
          title="آخر صافي راتب"
          value={formatMoney(latestPayroll?.net_salary)}
          icon={CreditCard}
          footer={latestPayroll?.month ? `Payroll ${latestPayroll.month}` : "لا يوجد سجل"}
        />
        <StatCard
          title="عدد الفروع"
          value={String(branches.length)}
          icon={MapPinned}
          footer={data?.default_work_schedule?.name || "بدون جدول دوام"}
        />
      </div>

      {/* ================================================== */}
      {/* Main Grid */}
      {/* ================================================== */}
      <div className="grid grid-cols-1 gap-6 2xl:grid-cols-3">
        <div className="space-y-6 2xl:col-span-2">
          {/* Personal Information */}
          <Card className="rounded-[28px] border-border/60 shadow-sm">
            <CardHeader>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <User2 className="h-5 w-5" />
                    المعلومات الشخصية
                  </CardTitle>
                  <CardDescription>
                    بيانات الهوية، الجنسية، ومعلومات الموظف الأساسية.
                  </CardDescription>
                </div>

                <SectionHeaderActions
                  isEditing={editingPersonal}
                  saving={savingPersonal}
                  onEdit={() => setEditingPersonal(true)}
                  onCancel={cancelPersonal}
                  onSave={handleSavePersonal}
                />
              </div>
            </CardHeader>

            <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {editingPersonal ? (
                <>
                  <EditableField
                    label="الاسم الكامل"
                    value={personalForm.full_name}
                    onChange={(value) =>
                      setPersonalForm((prev) => ({ ...prev, full_name: value }))
                    }
                  />
                  <EditableField
                    label="الاسم العربي"
                    value={personalForm.arabic_name}
                    onChange={(value) =>
                      setPersonalForm((prev) => ({ ...prev, arabic_name: value }))
                    }
                  />
                  <EditableField
                    label="البريد الإلكتروني"
                    type="email"
                    value={personalForm.email}
                    onChange={(value) =>
                      setPersonalForm((prev) => ({ ...prev, email: value }))
                    }
                  />
                  <EditableField
                    label="رقم الجوال"
                    value={personalForm.mobile_number}
                    onChange={(value) =>
                      setPersonalForm((prev) => ({ ...prev, mobile_number: value }))
                    }
                  />
                  <EditableField
                    label="اسم المستخدم"
                    value={personalForm.username}
                    onChange={(value) =>
                      setPersonalForm((prev) => ({ ...prev, username: value }))
                    }
                  />
                  <EditableField
                    label="الجنسية"
                    value={personalForm.nationality}
                    onChange={(value) =>
                      setPersonalForm((prev) => ({ ...prev, nationality: value }))
                    }
                  />
                  <EditableSelect
                    label="الجنس"
                    value={personalForm.gender || "UNSPECIFIED"}
                    onChange={(value) =>
                      setPersonalForm((prev) => ({
                        ...prev,
                        gender: value === "UNSPECIFIED" ? "" : value,
                      }))
                    }
                    items={[
                      { label: "غير محدد", value: "UNSPECIFIED" },
                      { label: "ذكر", value: "male" },
                      { label: "أنثى", value: "female" },
                    ]}
                  />
                  <EditableField
                    label="تاريخ الميلاد"
                    type="date"
                    value={personalForm.date_of_birth}
                    onChange={(value) =>
                      setPersonalForm((prev) => ({ ...prev, date_of_birth: value }))
                    }
                  />
                  <EditableField
                    label="رقم التأمينات GOSI"
                    value={personalForm.gosi_number}
                    onChange={(value) =>
                      setPersonalForm((prev) => ({ ...prev, gosi_number: value }))
                    }
                  />
                </>
              ) : (
                <>
                  <DetailItem icon={User2} label="الاسم الكامل" value={profile?.full_name} />
                  <DetailItem icon={User2} label="الاسم العربي" value={profile?.arabic_name} />
                  <DetailItem icon={Mail} label="البريد الإلكتروني" value={profile?.email} />
                  <DetailItem icon={Phone} label="رقم الجوال" value={profile?.mobile_number} />
                  <DetailItem icon={IdCard} label="اسم المستخدم" value={profile?.username} />
                  <DetailItem icon={ShieldCheck} label="الجنسية" value={profile?.nationality} />
                  <DetailItem icon={User2} label="الجنس" value={profile?.gender} />
                  <DetailItem
                    icon={CalendarDays}
                    label="تاريخ الميلاد"
                    value={formatDate(profile?.date_of_birth)}
                  />
                  <DetailItem
                    icon={BadgeCheck}
                    label="رقم التأمينات GOSI"
                    value={profile?.gosi_number}
                  />
                </>
              )}
            </CardContent>
          </Card>

          {/* Employment Information */}
          <Card className="rounded-[28px] border-border/60 shadow-sm">
            <CardHeader>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Briefcase className="h-5 w-5" />
                    معلومات التوظيف
                  </CardTitle>
                  <CardDescription>
                    القسم، المسمى الوظيفي، التواريخ الوظيفية، وجدول العمل.
                  </CardDescription>
                </div>

                <SectionHeaderActions
                  isEditing={editingEmployment}
                  saving={savingEmployment}
                  onEdit={() => setEditingEmployment(true)}
                  onCancel={cancelEmployment}
                  onSave={handleSaveEmployment}
                />
              </div>
            </CardHeader>

            <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {editingEmployment ? (
                <>
                  <EditableField
                    label="رقم الموظف"
                    value={employmentForm.employee_number}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({ ...prev, employee_number: value }))
                    }
                  />
                  <EditableField
                    label="نوع التوظيف"
                    value={employmentForm.employment_type}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({ ...prev, employment_type: value }))
                    }
                  />

                  <EditableSelect
                    label="القسم"
                    value={employmentForm.department_id || "__none__"}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({
                        ...prev,
                        department_id: value === "__none__" ? "" : value,
                      }))
                    }
                    items={[
                      { label: "بدون قسم", value: "__none__" },
                      ...departmentOptions.map((item) => ({
                        label: item.name,
                        value: String(item.id),
                      })),
                    ]}
                  />

                  <EditableSelect
                    label="المسمى الوظيفي"
                    value={employmentForm.job_title_id || "__none__"}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({
                        ...prev,
                        job_title_id: value === "__none__" ? "" : value,
                      }))
                    }
                    items={[
                      { label: "بدون مسمى وظيفي", value: "__none__" },
                      ...jobTitleOptions.map((item) => ({
                        label: item.name,
                        value: String(item.id),
                      })),
                    ]}
                  />

                  <EditableSelect
                    label="جدول الدوام"
                    value={employmentForm.work_schedule_id || "__none__"}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({
                        ...prev,
                        work_schedule_id: value === "__none__" ? "" : value,
                      }))
                    }
                    items={[
                      { label: "بدون جدول دوام", value: "__none__" },
                      ...workScheduleOptions.map((item) => ({
                        label: item.is_active ? item.name : `${item.name} (Inactive)`,
                        value: String(item.id),
                      })),
                    ]}
                  />

                  <EditableSelect
                    label="حالة جدول الدوام"
                    value={employmentForm.work_schedule_status}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({ ...prev, work_schedule_status: value }))
                    }
                    items={[
                      { label: "ACTIVE", value: "ACTIVE" },
                      { label: "INACTIVE", value: "INACTIVE" },
                    ]}
                  />

                  <EditableField
                    label="تاريخ الانضمام"
                    type="date"
                    value={employmentForm.join_date}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({ ...prev, join_date: value }))
                    }
                  />
                  <EditableField
                    label="بداية العمل"
                    type="date"
                    value={employmentForm.work_start_date}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({ ...prev, work_start_date: value }))
                    }
                  />
                  <EditableField
                    label="نهاية التجربة"
                    type="date"
                    value={employmentForm.probation_end_date}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({ ...prev, probation_end_date: value }))
                    }
                  />
                  <EditableField
                    label="تاريخ نهاية العقد"
                    type="date"
                    value={employmentForm.end_date}
                    onChange={(value) =>
                      setEmploymentForm((prev) => ({ ...prev, end_date: value }))
                    }
                  />

                  {loadingLookups ? (
                    <div className="rounded-2xl border border-dashed bg-background/70 p-4 text-sm text-muted-foreground md:col-span-2 xl:col-span-3">
                      جاري تحميل القوائم المنسدلة...
                    </div>
                  ) : null}
                </>
              ) : (
                <>
                  <DetailItem icon={IdCard} label="رقم الموظف" value={profile?.employee_number} />
                  <DetailItem
                    icon={Briefcase}
                    label="نوع التوظيف"
                    value={profile?.employment_type}
                  />
                  <DetailItem icon={Building2} label="القسم" value={data?.department?.name} />
                  <DetailItem icon={Briefcase} label="المسمى الوظيفي" value={data?.job_title?.name} />
                  <DetailItem
                    icon={Clock3}
                    label="جدول الدوام"
                    value={data?.default_work_schedule?.name}
                  />
                  <DetailItem
                    icon={BadgeCheck}
                    label="حالة جدول الدوام"
                    value={
                      data?.default_work_schedule
                        ? data.default_work_schedule.is_active
                          ? "ACTIVE"
                          : "INACTIVE"
                        : "—"
                    }
                  />
                  <DetailItem
                    icon={CalendarDays}
                    label="تاريخ الانضمام"
                    value={formatDate(profile?.join_date)}
                  />
                  <DetailItem
                    icon={CalendarDays}
                    label="بداية العمل"
                    value={formatDate(profile?.work_start_date)}
                  />
                  <DetailItem
                    icon={CalendarDays}
                    label="نهاية التجربة"
                    value={formatDate(profile?.probation_end_date)}
                  />
                  <DetailItem
                    icon={CalendarDays}
                    label="تاريخ نهاية العقد"
                    value={formatDate(profile?.end_date)}
                  />
                  <DetailItem
                    icon={Activity}
                    label="تاريخ الإنشاء"
                    value={formatDateTime(data?.created_at)}
                  />
                  <DetailItem
                    icon={Activity}
                    label="آخر تحديث"
                    value={formatDateTime(data?.updated_at)}
                  />
                </>
              )}
            </CardContent>
          </Card>

          {/* Identity Documents */}
          <Card className="rounded-[28px] border-border/60 shadow-sm">
            <CardHeader>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5" />
                    الوثائق الرسمية
                  </CardTitle>
                  <CardDescription>
                    الهوية الوطنية والجواز وتواريخ الإصدار والانتهاء.
                  </CardDescription>
                </div>

                <SectionHeaderActions
                  isEditing={editingDocuments}
                  saving={savingDocuments}
                  onEdit={() => setEditingDocuments(true)}
                  onCancel={cancelDocuments}
                  onSave={handleSaveDocuments}
                />
              </div>
            </CardHeader>

            <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {editingDocuments ? (
                <>
                  <EditableField
                    label="رقم الهوية الوطنية"
                    value={documentsForm.national_id}
                    onChange={(value) =>
                      setDocumentsForm((prev) => ({ ...prev, national_id: value }))
                    }
                  />
                  <EditableField
                    label="إصدار الهوية"
                    type="date"
                    value={documentsForm.national_id_issue_date}
                    onChange={(value) =>
                      setDocumentsForm((prev) => ({ ...prev, national_id_issue_date: value }))
                    }
                  />
                  <EditableField
                    label="انتهاء الهوية"
                    type="date"
                    value={documentsForm.national_id_expiry_date}
                    onChange={(value) =>
                      setDocumentsForm((prev) => ({ ...prev, national_id_expiry_date: value }))
                    }
                  />
                  <EditableField
                    label="رقم الجواز"
                    value={documentsForm.passport_number}
                    onChange={(value) =>
                      setDocumentsForm((prev) => ({ ...prev, passport_number: value }))
                    }
                  />
                  <EditableField
                    label="إصدار الجواز"
                    type="date"
                    value={documentsForm.passport_issue_date}
                    onChange={(value) =>
                      setDocumentsForm((prev) => ({ ...prev, passport_issue_date: value }))
                    }
                  />
                  <EditableField
                    label="انتهاء الجواز"
                    type="date"
                    value={documentsForm.passport_expiry_date}
                    onChange={(value) =>
                      setDocumentsForm((prev) => ({ ...prev, passport_expiry_date: value }))
                    }
                  />
                </>
              ) : (
                <>
                  <DetailItem
                    icon={IdCard}
                    label="رقم الهوية الوطنية"
                    value={profile?.national_id}
                  />
                  <DetailItem
                    icon={CalendarDays}
                    label="إصدار الهوية"
                    value={formatDate(profile?.national_id_issue_date)}
                  />
                  <DetailItem
                    icon={CalendarDays}
                    label="انتهاء الهوية"
                    value={formatDate(profile?.national_id_expiry_date)}
                  />
                  <DetailItem
                    icon={IdCard}
                    label="رقم الجواز"
                    value={profile?.passport_number}
                  />
                  <DetailItem
                    icon={CalendarDays}
                    label="إصدار الجواز"
                    value={formatDate(profile?.passport_issue_date)}
                  />
                  <DetailItem
                    icon={CalendarDays}
                    label="انتهاء الجواز"
                    value={formatDate(profile?.passport_expiry_date)}
                  />
                </>
              )}
            </CardContent>
          </Card>

          {/* Payroll History */}
          <Card className="rounded-[28px] border-border/60 shadow-sm">
            <CardHeader>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Wallet className="h-5 w-5" />
                    آخر سجلات الرواتب
                  </CardTitle>
                  <CardDescription>
                    آخر 12 سجل راتب قادمة من الباكند.
                  </CardDescription>
                </div>

                <Badge variant="secondary" className="rounded-full">
                  <FileText className="me-1 h-3.5 w-3.5" />
                  View Only
                </Badge>
              </div>
            </CardHeader>

            <CardContent>
              {payroll.length === 0 ? (
                <div className="rounded-3xl border border-dashed p-8 text-center text-sm text-muted-foreground">
                  لا توجد سجلات رواتب لهذا الموظف حتى الآن.
                </div>
              ) : (
                <div className="space-y-4">
                  {payroll.map((record) => (
                    <div
                      key={record.id}
                      className="rounded-3xl border bg-background/70 p-4 shadow-sm"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="text-base font-bold">
                              Payroll {record.month || "—"}
                            </h3>
                            <Badge variant={statusVariant(record.status)}>
                              {record.status || "—"}
                            </Badge>
                            {record.is_fully_paid ? (
                              <Badge variant="default">Fully Paid</Badge>
                            ) : (
                              <Badge variant="secondary">Partial / Pending</Badge>
                            )}
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                          <div className="rounded-2xl border p-3">
                            <p className="text-xs text-muted-foreground">Base</p>
                            <p className="mt-1 text-sm font-bold">
                              {formatMoney(record.base_salary)}
                            </p>
                          </div>
                          <div className="rounded-2xl border p-3">
                            <p className="text-xs text-muted-foreground">Allowance</p>
                            <p className="mt-1 text-sm font-bold">
                              {formatMoney(record.allowance)}
                            </p>
                          </div>
                          <div className="rounded-2xl border p-3">
                            <p className="text-xs text-muted-foreground">Overtime</p>
                            <p className="mt-1 text-sm font-bold">
                              {formatMoney(record.overtime)}
                            </p>
                          </div>
                          <div className="rounded-2xl border p-3">
                            <p className="text-xs text-muted-foreground">Bonus</p>
                            <p className="mt-1 text-sm font-bold">
                              {formatMoney(record.bonus)}
                            </p>
                          </div>
                          <div className="rounded-2xl border p-3">
                            <p className="text-xs text-muted-foreground">Deductions</p>
                            <p className="mt-1 text-sm font-bold">
                              {formatMoney(record.deductions)}
                            </p>
                          </div>
                          <div className="rounded-2xl border p-3">
                            <p className="text-xs text-muted-foreground">Net Salary</p>
                            <p className="mt-1 text-sm font-bold">
                              {formatMoney(record.net_salary)}
                            </p>
                          </div>
                          <div className="rounded-2xl border p-3">
                            <p className="text-xs text-muted-foreground">Paid</p>
                            <p className="mt-1 text-sm font-bold">
                              {formatMoney(record.paid_amount)}
                            </p>
                          </div>
                          <div className="rounded-2xl border p-3">
                            <p className="text-xs text-muted-foreground">Remaining</p>
                            <p className="mt-1 text-sm font-bold">
                              {formatMoney(record.remaining_amount)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {/* Branches */}
          <Card className="rounded-[28px] border-border/60 shadow-sm">
            <CardHeader>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5" />
                    الفروع المرتبطة
                  </CardTitle>
                  <CardDescription>
                    عرض الفروع الحالية مع إمكانية اختيار أكثر من فرع للموظف.
                  </CardDescription>
                </div>

                <SectionHeaderActions
                  isEditing={editingBranches}
                  saving={savingBranches}
                  onEdit={() => setEditingBranches(true)}
                  onCancel={cancelBranches}
                  onSave={handleSaveBranches}
                />
              </div>
            </CardHeader>

            <CardContent>
              {editingBranches ? (
                <div className="space-y-4">
                  {loadingLookups ? (
                    <div className="rounded-2xl border border-dashed p-5 text-center text-sm text-muted-foreground">
                      جاري تحميل جميع الفروع...
                    </div>
                  ) : availableBranches.length === 0 ? (
                    <div className="rounded-2xl border border-dashed p-5 text-center text-sm text-muted-foreground">
                      لا توجد فروع متاحة في الشركة الحالية.
                    </div>
                  ) : (
                    <>
                      <div className="flex flex-wrap gap-2">
                        {linkedBranchesPreview.length > 0 ? (
                          linkedBranchesPreview.map((branch) => (
                            <Badge key={branch.id} variant="secondary" className="rounded-full">
                              {branch.name}
                            </Badge>
                          ))
                        ) : (
                          <Badge variant="outline" className="rounded-full">
                            لا يوجد أي فرع محدد حاليًا
                          </Badge>
                        )}
                      </div>

                      <div className="space-y-3">
                        {availableBranches.map((branch) => {
                          const checked = selectedBranchIds.includes(String(branch.id))

                          return (
                            <button
                              key={branch.id}
                              type="button"
                              onClick={() => toggleBranchSelection(branch.id)}
                              className={`w-full rounded-2xl border p-4 text-start transition ${
                                checked
                                  ? "border-primary bg-primary/5"
                                  : "bg-background/70 hover:bg-muted/40"
                              }`}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="min-w-0">
                                  <p className="font-semibold">{branch.name}</p>
                                  <p className="mt-1 text-xs text-muted-foreground">
                                    BioTime Code: {branch.biotime_code || "—"}
                                  </p>
                                </div>

                                <div
                                  className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded-md border ${
                                    checked
                                      ? "border-primary bg-primary text-primary-foreground"
                                      : "border-border bg-background"
                                  }`}
                                >
                                  {checked ? <Check className="h-3.5 w-3.5" /> : null}
                                </div>
                              </div>
                            </button>
                          )
                        })}
                      </div>
                    </>
                  )}
                </div>
              ) : branches.length === 0 ? (
                <div className="rounded-2xl border border-dashed p-5 text-center text-sm text-muted-foreground">
                  لا توجد فروع مرتبطة.
                </div>
              ) : (
                <div className="space-y-3">
                  {branches.map((branch) => (
                    <div
                      key={branch.id}
                      className="rounded-2xl border bg-background/70 p-4"
                    >
                      <p className="font-semibold">{branch.name}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        BioTime Code: {branch.biotime_code || "—"}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Financial */}
          <Card className="rounded-[28px] border-border/60 shadow-sm">
            <CardHeader>
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Landmark className="h-5 w-5" />
                    البيانات المالية
                  </CardTitle>
                  <CardDescription>
                    تعديل الرواتب والبدلات والبنك والخيارات المالية.
                  </CardDescription>
                </div>

                <SectionHeaderActions
                  isEditing={editingFinancial}
                  saving={savingFinancial}
                  onEdit={() => setEditingFinancial(true)}
                  onCancel={cancelFinancial}
                  onSave={handleSaveFinancial}
                />
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {editingFinancial ? (
                <>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <EditableField
                      label="الراتب الأساسي"
                      type="number"
                      value={financialForm.basic_salary}
                      onChange={(value) =>
                        setFinancialForm((prev) => ({ ...prev, basic_salary: value }))
                      }
                    />
                    <EditableField
                      label="بدل السكن"
                      type="number"
                      value={financialForm.housing_allowance}
                      onChange={(value) =>
                        setFinancialForm((prev) => ({ ...prev, housing_allowance: value }))
                      }
                    />
                    <EditableField
                      label="بدل النقل"
                      type="number"
                      value={financialForm.transport_allowance}
                      onChange={(value) =>
                        setFinancialForm((prev) => ({ ...prev, transport_allowance: value }))
                      }
                    />
                    <EditableField
                      label="بدل الطعام"
                      type="number"
                      value={financialForm.food_allowance}
                      onChange={(value) =>
                        setFinancialForm((prev) => ({ ...prev, food_allowance: value }))
                      }
                    />
                    <EditableField
                      label="بدلات أخرى"
                      type="number"
                      value={financialForm.other_allowances}
                      onChange={(value) =>
                        setFinancialForm((prev) => ({ ...prev, other_allowances: value }))
                      }
                    />
                    <EditableField
                      label="اسم البنك"
                      value={financialForm.bank_name}
                      onChange={(value) =>
                        setFinancialForm((prev) => ({ ...prev, bank_name: value }))
                      }
                    />
                    <div className="md:col-span-2">
                      <EditableField
                        label="IBAN"
                        value={financialForm.iban}
                        onChange={(value) =>
                          setFinancialForm((prev) => ({ ...prev, iban: value }))
                        }
                      />
                    </div>
                    <EditableSelect
                      label="GOSI"
                      value={financialForm.is_gosi_enabled}
                      onChange={(value) =>
                        setFinancialForm((prev) => ({ ...prev, is_gosi_enabled: value }))
                      }
                      items={[
                        { label: "Enabled", value: "true" },
                        { label: "Disabled", value: "false" },
                      ]}
                    />
                    <EditableSelect
                      label="Tax"
                      value={financialForm.is_tax_enabled}
                      onChange={(value) =>
                        setFinancialForm((prev) => ({ ...prev, is_tax_enabled: value }))
                      }
                      items={[
                        { label: "Enabled", value: "true" },
                        { label: "Disabled", value: "false" },
                      ]}
                    />
                  </div>

                  <div className="rounded-3xl border p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Image
                        src="/currency/sar.svg"
                        alt="SAR"
                        width={18}
                        height={18}
                        className="h-[18px] w-[18px] object-contain"
                      />
                      <span className="text-sm font-semibold">المجموع التقديري بعد التعديل</span>
                    </div>

                    <div className="text-2xl font-bold">
                      {formatMoney(
                        Number(financialForm.basic_salary || 0) +
                          Number(financialForm.housing_allowance || 0) +
                          Number(financialForm.transport_allowance || 0) +
                          Number(financialForm.food_allowance || 0) +
                          Number(financialForm.other_allowances || 0)
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="rounded-3xl border p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Image
                        src="/currency/sar.svg"
                        alt="SAR"
                        width={18}
                        height={18}
                        className="h-[18px] w-[18px] object-contain"
                      />
                      <span className="text-sm font-semibold">الراتب والبدلات</span>
                    </div>

                    <div className="space-y-3 text-sm">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">الراتب الأساسي</span>
                        <span className="font-semibold">
                          {formatMoney(financial?.basic_salary)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">بدل السكن</span>
                        <span className="font-semibold">
                          {formatMoney(financial?.housing_allowance)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">بدل النقل</span>
                        <span className="font-semibold">
                          {formatMoney(financial?.transport_allowance)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">بدل الطعام</span>
                        <span className="font-semibold">
                          {formatMoney(financial?.food_allowance)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">بدلات أخرى</span>
                        <span className="font-semibold">
                          {formatMoney(financial?.other_allowances)}
                        </span>
                      </div>

                      <Separator />

                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium">الإجمالي التقديري</span>
                        <span className="text-base font-bold">
                          {formatMoney(
                            Number(financial?.basic_salary || 0) + totalAllowances
                          )}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-3xl border p-4">
                    <p className="mb-3 text-sm font-semibold">البنك والالتزامات</p>
                    <div className="space-y-3 text-sm">
                      <div>
                        <p className="text-xs text-muted-foreground">اسم البنك</p>
                        <p className="mt-1 font-semibold">
                          {financial?.bank_name || "—"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">IBAN</p>
                        <p className="mt-1 break-all font-semibold">
                          {financial?.iban || "—"}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2 pt-1">
                        <Badge variant={financial?.is_gosi_enabled ? "default" : "secondary"}>
                          GOSI {financial?.is_gosi_enabled ? "Enabled" : "Disabled"}
                        </Badge>
                        <Badge variant={financial?.is_tax_enabled ? "default" : "secondary"}>
                          Tax {financial?.is_tax_enabled ? "Enabled" : "Disabled"}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Biotime */}
          <Card className="rounded-[28px] border-border/60 shadow-sm">
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <CardTitle className="flex items-center gap-2">
                  <Fingerprint className="h-5 w-5" />
                  BioTime
                </CardTitle>

                {!hasBiotimeLink ? (
                  <Button
                    className="rounded-2xl"
                    onClick={handlePushEmployeeToBiotime}
                    disabled={pushingBiotime}
                  >
                    {pushingBiotime ? (
                      <Loader2 className="me-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Fingerprint className="me-2 h-4 w-4" />
                    )}
                    ربط الموظف
                  </Button>
                ) : null}
              </div>
            </CardHeader>
            <CardContent>
              {!hasBiotimeLink ? (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-dashed p-5 text-center text-sm text-muted-foreground">
                    هذا الموظف غير مرتبط حاليًا بـ BioTime.
                  </div>

                  <div className="rounded-2xl border bg-muted/30 p-4 text-xs text-muted-foreground">
                    عند الضغط على زر ربط الموظف سيتم إرسال بيانات الموظف الحالية إلى BioTime
                    ثم تحديث هذه البطاقة تلقائيًا بعد نجاح العملية.
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <Badge variant={biotime?.is_active ? "default" : "secondary"}>
                      {biotime?.is_active ? "Linked & Active" : "Linked"}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      Code: {data?.biotime_code || biotime?.employee_id || "—"}
                    </span>
                  </div>

                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-xs text-muted-foreground">الاسم في BioTime</p>
                      <p className="mt-1 font-semibold">{biotime?.full_name || "—"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">القسم</p>
                      <p className="mt-1 font-semibold">{biotime?.department || "—"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Card Number</p>
                      <p className="mt-1 font-semibold">{biotime?.card_number || "—"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Enrolled Fingers</p>
                      <p className="mt-1 font-semibold">
                        {biotime?.enrolled_fingers ?? "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Created At</p>
                      <p className="mt-1 font-semibold">
                        {formatDateTime(biotime?.created_at)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Updated At</p>
                      <p className="mt-1 font-semibold">
                        {formatDateTime(biotime?.updated_at)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}