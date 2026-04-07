"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react"
import {
  Activity,
  Briefcase,
  Building2,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Eye,
  FileDown,
  FileSpreadsheet,
  GitBranch,
  Layers3,
  Loader2,
  Mail,
  Pencil,
  Phone,
  Plane,
  Plus,
  RefreshCw,
  Search,
  Shield,
  Sparkles,
  UserCheck,
  UserCog,
  UserPlus,
  UserX,
  Users,
  XCircle,
  Crown,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
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

type Lang = "ar" | "en"
type Direction = "rtl" | "ltr"
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

const translations = {
  ar: {
    pageTitle: "الموظفون",
    pageDescription:
      "إدارة الموظفين داخل الشركة مع البحث والفلاتر وربط الأقسام والفروع وجداول الدوام.",
    addEmployee: "إضافة موظف",
    refresh: "تحديث",
    pdf: "PDF",
    excel: "Excel",

    fullName: "الاسم الكامل",
    arabicName: "الاسم العربي",
    employeeNumber: "الرقم الوظيفي",
    username: "اسم المستخدم",
    email: "البريد الإلكتروني",
    phone: "الجوال",
    role: "الدور",
    userStatus: "الحالة",
    department: "القسم",
    jobTitle: "المسمى الوظيفي",
    workSchedule: "جدول الدوام",
    branches: "الفروع",

    exampleFullName: "مثال: أحمد الحربي",
    exampleArabicName: "مثال: أحمد الحربي",
    exampleEmployeeNumber: "مثال: EMP-1001",
    exampleUsername: "مثال: ahmed.hr",
    exampleEmail: "example@company.com",
    examplePhone: "+9665xxxxxxxx",

    addCompanyUser: "إضافة مستخدم شركة",
    addCompanyUserDescription:
      "سيتم إنشاء مستخدم شركة فعلي وربطه بالدور المحدد داخل الشركة.",
    selectRole: "اختر الدور",
    selectStatus: "اختر الحالة",
    selectDepartment: "اختر القسم",
    selectJobTitle: "اختر المسمى الوظيفي",
    selectWorkSchedule: "اختر جدول الدوام",
    selectBranches: "اختر فرعًا أو أكثر",
    loadingDepartments: "جارٍ تحميل الأقسام...",
    loadingJobTitles: "جارٍ تحميل المسميات...",
    loadingSchedules: "جارٍ تحميل الجداول...",
    loadingBranches: "جارٍ تحميل الفروع...",
    noBranchesAvailable: "لا توجد فروع متاحة",
    roleSummary: "ملخص الدور",
    quickPreview: "معاينة سريعة",
    binding: "الربط",
    companyBinding: "شركة",
    cancel: "إلغاء",
    creating: "جارٍ الإنشاء...",
    saveUser: "حفظ المستخدم",

    totalEmployees: "إجمالي الموظفين",
    activeEmployees: "الموظفون النشطون",
    inactiveEmployees: "الموظفون غير النشطين",
    departmentsCount: "الأقسام",
    allEmployeesDesc: "جميع الموظفين داخل الشركة",
    activeEmployeesDesc: "الحسابات النشطة حالياً",
    inactiveEmployeesDesc: "الحسابات أو الملفات غير النشطة",
    departmentsCountDesc: "عدد الأقسام الحالية",

    filtersTitle: "البحث والتصفية",
    filtersDescription: "ابحث وصفِّ الموظفين حسب الاسم والحالة والقسم والفرع",
    searchPlaceholder:
      "ابحث بالاسم، اليوزر، البريد، الجوال، الرقم الوظيفي، القسم، الوظيفة...",
    filterStatus: "الحالة",
    filterDepartment: "القسم",
    filterBranch: "الفرع",
    allStatuses: "كل الحالات",
    allDepartments: "كل الأقسام",
    allBranches: "كل الفروع",
    reset: "إعادة تعيين",
    filtersReset: "تمت إعادة تعيين الفلاتر",

    employeesList: "قائمة الموظفين",
    totalResults: "إجمالي النتائج",
    loadingEmployees: "جارٍ تحميل الموظفين...",
    noResults: "لا توجد نتائج",
    noResultsDescription: "لا توجد بيانات مطابقة للفلاتر الحالية",

    employee: "الموظف",
    employeeNo: "الرقم الوظيفي",
    employeeBranches: "الفروع",
    joinDate: "تاريخ الانضمام",
    view: "عرض",
    actions: "الإجراءات",

    branchCardTitle: "الفروع",
    branchCardSubtitle: "عرض وإضافة فروع الشركة",
    noBranches: "لا توجد فروع حالياً",
    addBranchTitle: "إضافة فرع جديد",
    addBranchDescription: "سيتم إنشاء فرع جديد داخل الشركة الحالية",
    addBranchPlaceholder: "مثال: الفرع الرئيسي",

    departmentCardTitle: "الأقسام",
    departmentCardSubtitle: "عرض وإضافة أقسام الشركة",
    noDepartments: "لا توجد أقسام حالياً",
    addDepartmentTitle: "إضافة قسم جديد",
    addDepartmentDescription: "سيتم إنشاء قسم جديد داخل الشركة الحالية",
    addDepartmentPlaceholder: "مثال: الموارد البشرية",

    jobTitleCardTitle: "الوظائف",
    jobTitleCardSubtitle: "عرض وإضافة المسميات الوظيفية",
    noJobTitles: "لا توجد وظائف حالياً",
    addJobTitleTitle: "إضافة وظيفة جديدة",
    addJobTitleDescription: "سيتم إنشاء مسمى وظيفي جديد داخل الشركة الحالية",
    addJobTitlePlaceholder: "مثال: محاسب أول",

    add: "إضافة",
    save: "حفظ",
    loading: "جارٍ التحميل...",
    name: "الاسم",
    id: "المعرف",
    activeLabel: "نشط",
    inactiveLabel: "غير نشط",

    workSchedulesTitle: "فترات العمل",
    workSchedulesSubtitle: "عرض وإضافة وتعديل جداول الدوام الحالية",
    addWorkSchedule: "إضافة فترة عمل",
    editWorkSchedule: "إضافة / تعديل فترة عمل",
    editWorkScheduleDescription:
      "يمكنك إنشاء فترة جديدة أو تعديل فترة موجودة حسب نوع الدوام",
    workScheduleName: "اسم الفترة",
    workScheduleNamePlaceholder: "مثال: الفترة الصباحية",
    workScheduleType: "نوع الفترة",
    weekendDay: "يوم الإجازة",
    firstPeriodFrom: "الفترة الأولى من",
    firstPeriodTo: "الفترة الأولى إلى",
    secondPeriodFrom: "الفترة الثانية من",
    secondPeriodTo: "الفترة الثانية إلى",
    targetHours: "عدد الساعات",
    targetHoursPlaceholder: "مثال: 8",
    saveWorkSchedule: "حفظ الفترة",
    loadingWorkSchedules: "جارٍ تحميل الفترات...",
    noWorkSchedules: "لا توجد فترات عمل حالياً",
    noWorkSchedulesDescription:
      "يمكنك إضافة فترة عمل جديدة مباشرة من هذا القسم",
    type: "النوع",
    firstPeriod: "الفترة الأولى",
    secondPeriod: "الفترة الثانية",
    vacation: "الإجازة",
    hours: "الساعات",
    action: "إجراء",
    viewEdit: "عرض/تعديل",

    quickSummary: "ملخص سريع",
    goToCompanyProfile: "الانتقال إلى Company Profile",

    owner: "المالك",
    admin: "مدير النظام",
    hr: "الموارد البشرية",
    manager: "مدير",
    employeeRole: "موظف",

    statusActive: "نشط",
    statusInactive: "غير نشط",
    statusOnLeave: "في إجازة",

    fullTime: "دوام فترة واحدة",
    partTime: "دوام فترتين",
    hourly: "دوام بالساعات",

    fullNameRequired: "الاسم الكامل مطلوب",
    departmentRequired: "القسم مطلوب",
    usernameRequired: "اسم المستخدم مطلوب",
    usernameLength: "اسم المستخدم يجب أن يكون 3 أحرف على الأقل",
    emailInvalid: "يرجى إدخال بريد إلكتروني صحيح",
    companyUserCreated: "تم إنشاء مستخدم الشركة بنجاح",
    temporaryPassword: "كلمة المرور المؤقتة",
    createCompanyUserFailed: "فشل إنشاء مستخدم الشركة",

    branchNameRequired: "اسم الفرع مطلوب",
    branchCreated: "تم إنشاء الفرع بنجاح",
    branchCreateFailed: "فشل إنشاء الفرع",

    departmentNameRequired: "اسم القسم مطلوب",
    departmentCreated: "تم إنشاء القسم بنجاح",
    departmentCreateFailed: "فشل إنشاء القسم",

    jobTitleNameRequired: "اسم الوظيفة مطلوب",
    jobTitleCreated: "تم إنشاء الوظيفة بنجاح",
    jobTitleCreateFailed: "فشل إنشاء الوظيفة",

    workScheduleNameRequired: "اسم فترة العمل مطلوب",
    weekendDayRequired: "يوم الإجازة مطلوب",
    firstPeriodRequired: "أوقات الفترة الأولى مطلوبة",
    secondPeriodRequired: "أوقات الفترة الثانية مطلوبة",
    targetHoursRequired: "عدد الساعات مطلوب",
    workScheduleCreated: "تم إنشاء فترة العمل بنجاح",
    workScheduleUpdated: "تم تعديل فترة العمل بنجاح",
    workScheduleSaveFailed: "فشل حفظ فترة العمل",

    employeesFallbackEmpty: "تم عرض بيانات تجريبية لأن قائمة الموظفين فارغة",
    employeesFallbackError: "تعذر جلب البيانات الحقيقية، تم عرض بيانات تجريبية",
    lookupsLoadFailed: "فشل تحميل القوائم المساعدة",
    workScheduleAssignFailed: "تم إنشاء الموظف لكن فشل ربط جدول الدوام",
    printOpened: "تم فتح نافذة الطباعة",
    excelExportSuccess: "تم تصدير ملف الموظفين بنجاح",
    excelExportFail: "فشل تصدير ملف Excel",
    itemNameLabel: "الاسم",
    saveLoading: "جارٍ الحفظ...",
    directAddHint: "يمكنك إضافة عنصر جديد مباشرة من هذا القسم",
  },
  en: {
    pageTitle: "Employees",
    pageDescription:
      "Manage company employees with search, filters, departments, branches, and work schedules.",
    addEmployee: "Add Employee",
    refresh: "Refresh",
    pdf: "PDF",
    excel: "Excel",

    fullName: "Full Name",
    arabicName: "Arabic Name",
    employeeNumber: "Employee Number",
    username: "Username",
    email: "Email",
    phone: "Phone",
    role: "Role",
    userStatus: "Status",
    department: "Department",
    jobTitle: "Job Title",
    workSchedule: "Work Schedule",
    branches: "Branches",

    exampleFullName: "Example: Ahmed Alharbi",
    exampleArabicName: "Example: أحمد الحربي",
    exampleEmployeeNumber: "Example: EMP-1001",
    exampleUsername: "Example: ahmed.hr",
    exampleEmail: "example@company.com",
    examplePhone: "+9665xxxxxxxx",

    addCompanyUser: "Add Company User",
    addCompanyUserDescription:
      "This will create a real company user and assign the selected company role.",
    selectRole: "Select role",
    selectStatus: "Select status",
    selectDepartment: "Select department",
    selectJobTitle: "Select job title",
    selectWorkSchedule: "Select work schedule",
    selectBranches: "Select one or more branches",
    loadingDepartments: "Loading departments...",
    loadingJobTitles: "Loading job titles...",
    loadingSchedules: "Loading schedules...",
    loadingBranches: "Loading branches...",
    noBranchesAvailable: "No branches available",
    roleSummary: "Role Summary",
    quickPreview: "Quick Preview",
    binding: "Binding",
    companyBinding: "Company",
    cancel: "Cancel",
    creating: "Creating...",
    saveUser: "Save User",

    totalEmployees: "Total Employees",
    activeEmployees: "Active Employees",
    inactiveEmployees: "Inactive Employees",
    departmentsCount: "Departments",
    allEmployeesDesc: "All employees inside the company",
    activeEmployeesDesc: "Currently active accounts",
    inactiveEmployeesDesc: "Inactive accounts or files",
    departmentsCountDesc: "Current departments count",

    filtersTitle: "Search & Filter",
    filtersDescription: "Search and filter employees by name, status, department, and branch",
    searchPlaceholder:
      "Search by name, username, email, phone, employee no., department, job title...",
    filterStatus: "Status",
    filterDepartment: "Department",
    filterBranch: "Branch",
    allStatuses: "All Statuses",
    allDepartments: "All Departments",
    allBranches: "All Branches",
    reset: "Reset",
    filtersReset: "Filters reset successfully",

    employeesList: "Employees List",
    totalResults: "Total results",
    loadingEmployees: "Loading employees...",
    noResults: "No Results",
    noResultsDescription: "No data matched the current filters",

    employee: "Employee",
    employeeNo: "Employee No.",
    employeeBranches: "Branches",
    joinDate: "Join Date",
    view: "View",
    actions: "Actions",

    branchCardTitle: "Branches",
    branchCardSubtitle: "View and add company branches",
    noBranches: "No branches available",
    addBranchTitle: "Add New Branch",
    addBranchDescription: "A new branch will be created inside the current company",
    addBranchPlaceholder: "Example: Main Branch",

    departmentCardTitle: "Departments",
    departmentCardSubtitle: "View and add company departments",
    noDepartments: "No departments available",
    addDepartmentTitle: "Add New Department",
    addDepartmentDescription:
      "A new department will be created inside the current company",
    addDepartmentPlaceholder: "Example: Human Resources",

    jobTitleCardTitle: "Job Titles",
    jobTitleCardSubtitle: "View and add job titles",
    noJobTitles: "No job titles available",
    addJobTitleTitle: "Add New Job Title",
    addJobTitleDescription:
      "A new job title will be created inside the current company",
    addJobTitlePlaceholder: "Example: Senior Accountant",

    add: "Add",
    save: "Save",
    loading: "Loading...",
    name: "Name",
    id: "ID",
    activeLabel: "Active",
    inactiveLabel: "Inactive",

    workSchedulesTitle: "Work Schedules",
    workSchedulesSubtitle: "View, add, and edit current work schedules",
    addWorkSchedule: "Add Work Schedule",
    editWorkSchedule: "Add / Edit Work Schedule",
    editWorkScheduleDescription:
      "Create a new schedule or update an existing one based on work type",
    workScheduleName: "Schedule Name",
    workScheduleNamePlaceholder: "Example: Morning Shift",
    workScheduleType: "Schedule Type",
    weekendDay: "Weekend Day",
    firstPeriodFrom: "First Period From",
    firstPeriodTo: "First Period To",
    secondPeriodFrom: "Second Period From",
    secondPeriodTo: "Second Period To",
    targetHours: "Hours",
    targetHoursPlaceholder: "Example: 8",
    saveWorkSchedule: "Save Schedule",
    loadingWorkSchedules: "Loading schedules...",
    noWorkSchedules: "No work schedules available",
    noWorkSchedulesDescription:
      "You can add a new work schedule directly from this section",
    type: "Type",
    firstPeriod: "First Period",
    secondPeriod: "Second Period",
    vacation: "Weekend",
    hours: "Hours",
    action: "Action",
    viewEdit: "View / Edit",

    quickSummary: "Quick Summary",
    goToCompanyProfile: "Go to Company Profile",

    owner: "Owner",
    admin: "Admin",
    hr: "HR",
    manager: "Manager",
    employeeRole: "Employee",

    statusActive: "Active",
    statusInactive: "Inactive",
    statusOnLeave: "On Leave",

    fullTime: "Single Shift",
    partTime: "Two Shifts",
    hourly: "Hourly",

    fullNameRequired: "Full name is required",
    departmentRequired: "Department is required",
    usernameRequired: "Username is required",
    usernameLength: "Username must be at least 3 characters",
    emailInvalid: "Please enter a valid email address",
    companyUserCreated: "Company user created successfully",
    temporaryPassword: "Temporary password",
    createCompanyUserFailed: "Failed to create company user",

    branchNameRequired: "Branch name is required",
    branchCreated: "Branch created successfully",
    branchCreateFailed: "Failed to create branch",

    departmentNameRequired: "Department name is required",
    departmentCreated: "Department created successfully",
    departmentCreateFailed: "Failed to create department",

    jobTitleNameRequired: "Job title name is required",
    jobTitleCreated: "Job title created successfully",
    jobTitleCreateFailed: "Failed to create job title",

    workScheduleNameRequired: "Work schedule name is required",
    weekendDayRequired: "Weekend day is required",
    firstPeriodRequired: "First period times are required",
    secondPeriodRequired: "Second period times are required",
    targetHoursRequired: "Target hours are required",
    workScheduleCreated: "Work schedule created successfully",
    workScheduleUpdated: "Work schedule updated successfully",
    workScheduleSaveFailed: "Failed to save work schedule",

    employeesFallbackEmpty:
      "Showing demo data because the employees list is empty",
    employeesFallbackError:
      "Unable to load live data, showing demo employees instead",
    lookupsLoadFailed: "Failed to load lookup lists",
    workScheduleAssignFailed:
      "Employee created, but assigning work schedule failed",
    printOpened: "Print window opened",
    excelExportSuccess: "Employees exported successfully",
    excelExportFail: "Excel export failed",
    itemNameLabel: "Name",
    saveLoading: "Saving...",
    directAddHint: "You can add a new item directly from this section",
  },
} as const

const COMPANY_ROLE_OPTIONS_BY_LANG = {
  ar: [
    { code: "ADMIN", label: "مدير النظام" },
    { code: "HR", label: "الموارد البشرية" },
    { code: "MANAGER", label: "مدير" },
    { code: "EMPLOYEE", label: "موظف" },
  ] satisfies CompanyRoleOption[],
  en: [
    { code: "ADMIN", label: "Admin" },
    { code: "HR", label: "HR" },
    { code: "MANAGER", label: "Manager" },
    { code: "EMPLOYEE", label: "Employee" },
  ] satisfies CompanyRoleOption[],
}

const WEEKEND_DAY_OPTIONS = {
  ar: [
    { value: "fri", label: "الجمعة" },
    { value: "sat", label: "السبت" },
    { value: "sun", label: "الأحد" },
    { value: "mon", label: "الاثنين" },
    { value: "tue", label: "الثلاثاء" },
    { value: "wed", label: "الأربعاء" },
    { value: "thu", label: "الخميس" },
  ],
  en: [
    { value: "fri", label: "Friday" },
    { value: "sat", label: "Saturday" },
    { value: "sun", label: "Sunday" },
    { value: "mon", label: "Monday" },
    { value: "tue", label: "Tuesday" },
    { value: "wed", label: "Wednesday" },
    { value: "thu", label: "Thursday" },
  ],
} as const

const FALLBACK_EMPLOYEES: EmployeeRow[] = [
  {
    id: 1,
    employee_code: "EMP-1001",
    employee_number: "EMP-1001",
    full_name: "Ahmed Mohammed",
    email: "ahmed@company.com",
    phone: "+966500000001",
    avatar: "",
    username: "ahmed",
    role: "HR",
    department: "Human Resources",
    job_title: "HR Manager",
    branch: "Madinah",
    branches: [{ id: 1, name: "Madinah" }],
    status: "ACTIVE",
    join_date: "2025-01-10",
  },
  {
    id: 2,
    employee_code: "EMP-1002",
    employee_number: "EMP-1002",
    full_name: "Sara Ali",
    email: "sara@company.com",
    phone: "+966500000002",
    avatar: "",
    username: "sara",
    role: "EMPLOYEE",
    department: "Payroll",
    job_title: "Payroll Specialist",
    branch: "Riyadh",
    branches: [{ id: 2, name: "Riyadh" }],
    status: "ACTIVE",
    join_date: "2025-02-14",
  },
  {
    id: 3,
    employee_code: "EMP-1003",
    employee_number: "EMP-1003",
    full_name: "Khaled Hassan",
    email: "khaled@company.com",
    phone: "+966500000003",
    avatar: "",
    username: "khaled",
    role: "MANAGER",
    department: "Operations",
    job_title: "Operations Supervisor",
    branch: "Jeddah",
    branches: [{ id: 3, name: "Jeddah" }],
    status: "INACTIVE",
    join_date: "2024-11-03",
  },
  {
    id: 4,
    employee_code: "EMP-1004",
    employee_number: "EMP-1004",
    full_name: "Reem Abdullah",
    email: "reem@company.com",
    phone: "+966500000004",
    avatar: "",
    username: "reem",
    role: "EMPLOYEE",
    department: "Sales",
    job_title: "Sales Executive",
    branch: "Dammam",
    branches: [{ id: 4, name: "Dammam" }],
    status: "ON_LEAVE",
    join_date: "2024-08-20",
  },
]

function getDocumentLang(): Lang {
  if (typeof document === "undefined") return "ar"

  const lang =
    document.documentElement.lang ||
    document.body.getAttribute("lang") ||
    "ar"

  return lang.toLowerCase().startsWith("en") ? "en" : "ar"
}

function getDocumentDir(): Direction {
  if (typeof document === "undefined") return "rtl"

  const dir =
    document.documentElement.dir ||
    document.body.getAttribute("dir") ||
    (getDocumentLang() === "ar" ? "rtl" : "ltr")

  return dir.toLowerCase() === "ltr" ? "ltr" : "rtl"
}

function getCookie(name: string): string {
  if (typeof document === "undefined") return ""

  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))

  return cookie ? decodeURIComponent(cookie.split("=")[1]) : ""
}

function formatEnglishNumber(value: number | string | null | undefined) {
  const numericValue = Number(value || 0)
  return new Intl.NumberFormat("en-US", {
    useGrouping: false,
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue)
}

function formatDateLabel(value?: string | null) {
  if (!value || value === "-") return "—"

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value).slice(0, 10).replace(/-/g, "/")
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return `${year}/${month}/${day}`
}

function formatTimeLabel(value?: string | null) {
  if (!value) return "--"
  return String(value).slice(0, 5)
}

function getInitials(name: string) {
  const parts = name.trim().split(" ").filter(Boolean)
  if (parts.length === 0) return "EM"
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0] || ""}${parts[1][0] || ""}`.toUpperCase()
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

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function escapeHtml(value: string) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
}

function getRoleLabel(role: string, lang: Lang) {
  const normalized = String(role || "").toUpperCase() as CompanyRole
  const t = translations[lang]

  switch (normalized) {
    case "OWNER":
      return t.owner
    case "ADMIN":
      return t.admin
    case "HR":
      return t.hr
    case "MANAGER":
      return t.manager
    case "EMPLOYEE":
      return t.employeeRole
    default:
      return role || "--"
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
      return "border-yellow-200 bg-yellow-50 text-yellow-700"
    case "ADMIN":
      return "border-blue-200 bg-blue-50 text-blue-700"
    case "HR":
      return "border-violet-200 bg-violet-50 text-violet-700"
    case "MANAGER":
      return "border-amber-200 bg-amber-50 text-amber-700"
    case "EMPLOYEE":
      return "border-zinc-200 bg-zinc-50 text-zinc-700"
    default:
      return "border-zinc-200 bg-zinc-50 text-zinc-700"
  }
}

function getScheduleTypeLabel(value: string | null | undefined, lang: Lang) {
  const t = translations[lang]

  switch (value) {
    case "FULL_TIME":
      return t.fullTime
    case "PART_TIME":
      return t.partTime
    case "HOURLY":
      return t.hourly
    default:
      return value || "--"
  }
}

function formatHoursLabel(value?: string | number | null) {
  if (value === null || value === undefined || value === "") return "--"
  return formatEnglishNumber(value)
}

function getLookupActiveLabel(isActive: boolean | undefined, lang: Lang) {
  return isActive === false
    ? translations[lang].inactiveLabel
    : translations[lang].activeLabel
}

type StatusMeta = {
  label: string
  icon: React.ComponentType<{ className?: string }>
  className: string
}

function getStatusMeta(status: EmployeeStatus, lang: Lang): StatusMeta {
  const t = translations[lang]

  switch (status) {
    case "ACTIVE":
      return {
        label: t.statusActive,
        icon: CheckCircle2,
        className: "border-emerald-200 bg-emerald-50 text-emerald-700",
      }
    case "INACTIVE":
      return {
        label: t.statusInactive,
        icon: XCircle,
        className: "border-red-200 bg-red-50 text-red-700",
      }
    case "ON_LEAVE":
      return {
        label: t.statusOnLeave,
        icon: Plane,
        className: "border-amber-200 bg-amber-50 text-amber-700",
      }
    default:
      return {
        label: String(status),
        icon: Activity,
        className: "border-zinc-200 bg-zinc-50 text-zinc-700",
      }
  }
}

function StatusBadge({
  status,
  lang,
}: {
  status: EmployeeStatus
  lang: Lang
}) {
  const meta = getStatusMeta(status, lang)
  const Icon = meta.icon

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        meta.className
      )}
      dir={lang === "ar" ? "rtl" : "ltr"}
    >
      <Icon className="me-1 h-3.5 w-3.5" />
      {meta.label}
    </span>
  )
}

function downloadExcelFile(rows: EmployeeRow[], lang: Lang) {
  try {
    const t = translations[lang]

    const html = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office"
            xmlns:x="urn:schemas-microsoft-com:office:excel"
            xmlns="http://www.w3.org/TR/REC-html40">
        <head>
          <meta charset="utf-8" />
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
                  <td>${escapeHtml(String(row.id))}</td>
                  <td>${escapeHtml(row.employee_code)}</td>
                  <td>${escapeHtml(row.full_name)}</td>
                  <td>${escapeHtml(row.username || "")}</td>
                  <td>${escapeHtml(row.email)}</td>
                  <td>${escapeHtml(row.phone)}</td>
                  <td>${escapeHtml(row.role || "")}</td>
                  <td>${escapeHtml(row.department)}</td>
                  <td>${escapeHtml(row.job_title)}</td>
                  <td>${escapeHtml(row.branch)}</td>
                  <td>${escapeHtml(row.status)}</td>
                  <td>${escapeHtml(formatDateLabel(row.join_date))}</td>
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

    toast.success(t.excelExportSuccess)
  } catch (error) {
    console.error("Excel export error:", error)
    toast.error(translations[lang].excelExportFail)
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
  icon: React.ComponentType<{ className?: string }>
  valueClassName?: string
}) {
  const Icon = icon

  return (
    <Card className="border-border/60">
      <CardContent className="flex items-center justify-between p-5">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className={cn("text-3xl font-semibold tabular-nums", valueClassName)}>
            {formatEnglishNumber(value)}
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
  lang,
}: {
  title: string
  subtitle: string
  count: number
  icon: ReactNode
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
  itemIcon: ReactNode
  lang: Lang
}) {
  const t = translations[lang]

  return (
    <Card className="border-border/60">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border bg-muted/40 p-3">{icon}</div>
            <div>
              <CardTitle className="text-base">{title}</CardTitle>
              <CardDescription>{subtitle}</CardDescription>
            </div>
          </div>

          <Badge variant="secondary" dir="ltr">
            {formatEnglishNumber(count)}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                {t.add}
              </Button>
            </DialogTrigger>

            <DialogContent className="sm:max-w-md" dir={lang === "ar" ? "rtl" : "ltr"}>
              <DialogHeader>
                <DialogTitle>{createTitle}</DialogTitle>
                <DialogDescription>{createDescription}</DialogDescription>
              </DialogHeader>

              <div className="space-y-2 py-2">
                <label className="text-sm font-medium">{t.itemNameLabel}</label>
                <Input
                  value={createValue}
                  onChange={(e) => onCreateValueChange(e.target.value)}
                  placeholder={createPlaceholder}
                />
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  {t.cancel}
                </Button>
                <Button onClick={onCreate} disabled={creating} className="gap-2">
                  {creating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {t.saveLoading}
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      {t.save}
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Button variant="outline" onClick={onRefresh} className="gap-2">
            <RefreshCw className="h-4 w-4" />
            {t.refresh}
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-14 text-muted-foreground">
            <Loader2 className="me-2 h-5 w-5 animate-spin" />
            {t.loading}
          </div>
        ) : items.length === 0 ? (
          <div className="rounded-2xl border border-dashed p-8 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border bg-muted/30">
              {icon}
            </div>
            <h3 className="font-semibold">{emptyText}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{t.directAddHint}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between gap-3 rounded-2xl border border-border/60 bg-background p-3"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="rounded-xl border bg-muted/30 p-2.5">{itemIcon}</div>

                  <div className="min-w-0">
                    <div className="truncate font-medium">{item.name}</div>
                    <div className="mt-1 flex flex-wrap items-center gap-2">
                      <Badge variant="outline" dir="ltr">
                        {t.id}: {formatEnglishNumber(item.id)}
                      </Badge>

                      <Badge
                        className={cn(
                          item.is_active === false
                            ? "border-red-200 bg-red-50 text-red-700"
                            : "border-emerald-200 bg-emerald-50 text-emerald-700"
                        )}
                      >
                        {getLookupActiveLabel(item.is_active, lang)}
                      </Badge>
                    </div>
                  </div>
                </div>

                {item.biotime_code ? (
                  <Badge variant="secondary" dir="ltr">
                    {item.biotime_code}
                  </Badge>
                ) : null}
              </div>
            ))}
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
  onToggleItem,
  lang,
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
  onToggleItem: (item: LookupItem) => void
  lang: Lang
}) {
  const t = translations[lang]
  const weekendOptions = WEEKEND_DAY_OPTIONS[lang]

  return (
    <Card className="border-border/60">
      <CardHeader>
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="space-y-1">
            <CardTitle>{t.workSchedulesTitle}</CardTitle>
            <CardDescription>{t.workSchedulesSubtitle}</CardDescription>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" dir="ltr">
              {formatEnglishNumber(items.length)}
            </Badge>

            <Dialog open={open} onOpenChange={onOpenChange}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <Plus className="h-4 w-4" />
                  {t.addWorkSchedule}
                </Button>
              </DialogTrigger>

              <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl" dir={lang === "ar" ? "rtl" : "ltr"}>
                <DialogHeader>
                  <DialogTitle>{t.editWorkSchedule}</DialogTitle>
                  <DialogDescription>{t.editWorkScheduleDescription}</DialogDescription>
                </DialogHeader>

                <div className="grid grid-cols-1 gap-4 py-2 md:grid-cols-2">
                  <div className="space-y-2 md:col-span-2">
                    <label className="text-sm font-medium">{t.workScheduleName}</label>
                    <Input
                      value={createName}
                      onChange={(e) => onCreateNameChange(e.target.value)}
                      placeholder={t.workScheduleNamePlaceholder}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">{t.workScheduleType}</label>
                    <Select
                      value={createType}
                      onValueChange={(value) => onCreateTypeChange(value as ScheduleType)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={t.workScheduleType} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="FULL_TIME">{t.fullTime}</SelectItem>
                        <SelectItem value="PART_TIME">{t.partTime}</SelectItem>
                        <SelectItem value="HOURLY">{t.hourly}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">{t.weekendDay}</label>
                    <Select value={createWeekendDay} onValueChange={onCreateWeekendDayChange}>
                      <SelectTrigger>
                        <SelectValue placeholder={t.weekendDay} />
                      </SelectTrigger>
                      <SelectContent>
                        {weekendOptions.map((day) => (
                          <SelectItem key={day.value} value={day.value}>
                            {day.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {createType !== "HOURLY" && (
                    <>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">{t.firstPeriodFrom}</label>
                        <Input
                          dir="ltr"
                          type="time"
                          value={createPeriod1Start}
                          onChange={(e) => onCreatePeriod1StartChange(e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">{t.firstPeriodTo}</label>
                        <Input
                          dir="ltr"
                          type="time"
                          value={createPeriod1End}
                          onChange={(e) => onCreatePeriod1EndChange(e.target.value)}
                        />
                      </div>
                    </>
                  )}

                  {createType === "PART_TIME" && (
                    <>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">{t.secondPeriodFrom}</label>
                        <Input
                          dir="ltr"
                          type="time"
                          value={createPeriod2Start}
                          onChange={(e) => onCreatePeriod2StartChange(e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">{t.secondPeriodTo}</label>
                        <Input
                          dir="ltr"
                          type="time"
                          value={createPeriod2End}
                          onChange={(e) => onCreatePeriod2EndChange(e.target.value)}
                        />
                      </div>
                    </>
                  )}

                  {createType === "HOURLY" && (
                    <div className="space-y-2 md:col-span-2">
                      <label className="text-sm font-medium">{t.targetHours}</label>
                      <Input
                        dir="ltr"
                        type="number"
                        min="1"
                        step="0.5"
                        value={createTargetHours}
                        onChange={(e) => onCreateTargetHoursChange(e.target.value)}
                        placeholder={t.targetHoursPlaceholder}
                      />
                    </div>
                  )}
                </div>

                <DialogFooter>
                  <Button variant="outline" onClick={() => onOpenChange(false)}>
                    {t.cancel}
                  </Button>
                  <Button onClick={onCreate} disabled={creating} className="gap-2">
                    {creating ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        {t.saveLoading}
                      </>
                    ) : (
                      <>
                        <Plus className="h-4 w-4" />
                        {t.saveWorkSchedule}
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Button variant="outline" onClick={onRefresh} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              {t.refresh}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-14 text-muted-foreground">
            <Loader2 className="me-2 h-5 w-5 animate-spin" />
            {t.loadingWorkSchedules}
          </div>
        ) : items.length === 0 ? (
          <div className="rounded-2xl border border-dashed p-8 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl border bg-muted/30">
              <Clock3 className="h-5 w-5" />
            </div>
            <h3 className="font-semibold">{t.noWorkSchedules}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {t.noWorkSchedulesDescription}
            </p>
          </div>
        ) : (
          <>
            <div className="hidden lg:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t.name}</TableHead>
                    <TableHead>{t.type}</TableHead>
                    <TableHead>{t.firstPeriod}</TableHead>
                    <TableHead>{t.secondPeriod}</TableHead>
                    <TableHead>{t.vacation}</TableHead>
                    <TableHead>{t.hours}</TableHead>
                    <TableHead>{t.userStatus}</TableHead>
                    <TableHead>{t.action}</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <div className="flex items-center gap-2 font-medium">
                          <Clock3 className="h-4 w-4 text-muted-foreground" />
                          {item.name}
                        </div>
                      </TableCell>

                      <TableCell>
                        <Badge variant="outline">{getScheduleTypeLabel(item.schedule_type, lang)}</Badge>
                      </TableCell>

                      <TableCell dir="ltr">
                        {item.period1_start || item.period1_end
                          ? `${formatTimeLabel(item.period1_start)} - ${formatTimeLabel(item.period1_end)}`
                          : "--"}
                      </TableCell>

                      <TableCell dir="ltr">
                        {item.period2_start || item.period2_end
                          ? `${formatTimeLabel(item.period2_start)} - ${formatTimeLabel(item.period2_end)}`
                          : "--"}
                      </TableCell>

                      <TableCell>
                        {lang === "ar"
                          ? item.weekend_days_ar || item.weekend_days || "--"
                          : item.weekend_days || item.weekend_days_ar || "--"}
                      </TableCell>

                      <TableCell dir="ltr">{formatHoursLabel(item.target_daily_hours)}</TableCell>

                      <TableCell>
                        <Badge
                          className={cn(
                            item.is_active === false
                              ? "border-red-200 bg-red-50 text-red-700"
                              : "border-emerald-200 bg-emerald-50 text-emerald-700"
                          )}
                        >
                          {getLookupActiveLabel(item.is_active, lang)}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        <div className="flex flex-wrap items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              editItem(item)
                              onEditItem(item)
                            }}
                            className="gap-2"
                          >
                            <Pencil className="h-4 w-4" />
                            {t.viewEdit}
                          </Button>

                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onToggleItem(item)}
                            className="gap-2"
                          >
                            {item.is_active === false ? (
                              <>
                                <CheckCircle2 className="h-4 w-4" />
                                {t.statusActive}
                              </>
                            ) : (
                              <>
                                <XCircle className="h-4 w-4" />
                                {t.statusInactive}
                              </>
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="grid gap-4 lg:hidden">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="rounded-2xl border border-border/60 bg-background p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 font-semibold">
                        <Clock3 className="h-4 w-4 text-muted-foreground" />
                        {item.name}
                      </div>
                      <Badge variant="outline">{getScheduleTypeLabel(item.schedule_type, lang)}</Badge>
                    </div>

                    <Badge
                      className={cn(
                        item.is_active === false
                          ? "border-red-200 bg-red-50 text-red-700"
                          : "border-emerald-200 bg-emerald-50 text-emerald-700"
                      )}
                    >
                      {getLookupActiveLabel(item.is_active, lang)}
                    </Badge>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-xl border bg-muted/30 p-3">
                      <p className="text-xs text-muted-foreground">{t.firstPeriod}</p>
                      <p dir="ltr" className="mt-1 font-medium">
                        {item.period1_start || item.period1_end
                          ? `${formatTimeLabel(item.period1_start)} - ${formatTimeLabel(item.period1_end)}`
                          : "--"}
                      </p>
                    </div>

                    <div className="rounded-xl border bg-muted/30 p-3">
                      <p className="text-xs text-muted-foreground">{t.secondPeriod}</p>
                      <p dir="ltr" className="mt-1 font-medium">
                        {item.period2_start || item.period2_end
                          ? `${formatTimeLabel(item.period2_start)} - ${formatTimeLabel(item.period2_end)}`
                          : "--"}
                      </p>
                    </div>

                    <div className="rounded-xl border bg-muted/30 p-3">
                      <p className="text-xs text-muted-foreground">{t.vacation}</p>
                      <p className="mt-1 font-medium">
                        {lang === "ar"
                          ? item.weekend_days_ar || item.weekend_days || "--"
                          : item.weekend_days || item.weekend_days_ar || "--"}
                      </p>
                    </div>

                    <div className="rounded-xl border bg-muted/30 p-3">
                      <p className="text-xs text-muted-foreground">{t.hours}</p>
                      <p dir="ltr" className="mt-1 font-medium">
                        {formatHoursLabel(item.target_daily_hours)}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
                    <Button
                      variant="outline"
                      className="w-full gap-2"
                      onClick={() => {
                        editItem(item)
                        onEditItem(item)
                      }}
                    >
                      <Pencil className="h-4 w-4" />
                      {t.viewEdit}
                    </Button>

                    <Button
                      variant="outline"
                      className="w-full gap-2"
                      onClick={() => onToggleItem(item)}
                    >
                      {item.is_active === false ? (
                        <>
                          <CheckCircle2 className="h-4 w-4" />
                          {t.statusActive}
                        </>
                      ) : (
                        <>
                          <XCircle className="h-4 w-4" />
                          {t.statusInactive}
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

export default function CompanyEmployeesPage() {
  const [lang, setLang] = useState<Lang>("ar")
  const [direction, setDirection] = useState<Direction>("rtl")

  const [employees, setEmployees] = useState<EmployeeRow[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("ALL")
  const [departmentFilter, setDepartmentFilter] = useState("ALL")
  const [branchFilter, setBranchFilter] = useState("ALL")

  const [openCreateDialog, setOpenCreateDialog] = useState(false)
  const [fullName, setFullName] = useState("")
  const [arabicName, setArabicName] = useState("")
  const [employeeNumber, setEmployeeNumber] = useState("")
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
  const [newWorkScheduleType, setNewWorkScheduleType] = useState<ScheduleType>("FULL_TIME")
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

  const t = translations[lang]
  const isArabic = direction === "rtl"
  const roles = COMPANY_ROLE_OPTIONS_BY_LANG[lang]

  const syncLanguageState = useCallback(() => {
    const nextLang = getDocumentLang()
    const nextDir = getDocumentDir()
    setLang(nextLang)
    setDirection(nextDir)
  }, [])

  const fetchEmployees = useCallback(
    async (silent = false) => {
      if (silent) setRefreshing(true)
      else setLoading(true)

      try {
        const response = await fetch(`${API_BASE}/api/company/employees/`, {
          method: "GET",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          cache: "no-store",
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data: EmployeesApiResponse = await response.json()
        const rawResults = data.results || data.employees || data.data || []

        if (!Array.isArray(rawResults) || rawResults.length === 0) {
          setEmployees(FALLBACK_EMPLOYEES)
          toast.warning(t.employeesFallbackEmpty)
          return
        }

        setEmployees(rawResults.map(normalizeEmployeeRow))
      } catch (error) {
        console.error("Employees fetch error:", error)
        setEmployees(FALLBACK_EMPLOYEES)
        toast.warning(t.employeesFallbackError)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [t.employeesFallbackEmpty, t.employeesFallbackError]
  )

  const fetchLookups = useCallback(async () => {
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
      const workSchedulesResults = extractLookupItems(schedulesData, "work_schedules")
      setWorkScheduleOptions(
        schedulesResults.length ? schedulesResults : workSchedulesResults
      )
    } catch (error) {
      console.error("Lookup loading error:", error)
      toast.error(t.lookupsLoadFailed)
    } finally {
      setLoadingLookups(false)
    }
  }, [t.lookupsLoadFailed])

  useEffect(() => {
    syncLanguageState()

    const observer = new MutationObserver(syncLanguageState)
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    window.addEventListener("languagechange", syncLanguageState)
    window.addEventListener("focus", syncLanguageState)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", syncLanguageState)
      window.removeEventListener("focus", syncLanguageState)
    }
  }, [syncLanguageState])

  useEffect(() => {
    fetchEmployees()
    fetchLookups()
  }, [fetchEmployees, fetchLookups])

  useEffect(() => {
    if (openCreateDialog) {
      fetchLookups()
    }
  }, [openCreateDialog, fetchLookups])

  function resetCreateForm() {
    setFullName("")
    setArabicName("")
    setEmployeeNumber("")
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
    setNewWorkSchedulePeriod1Start(formatTimeLabel(item.period1_start || item.start_time || ""))
    setNewWorkSchedulePeriod1End(formatTimeLabel(item.period1_end || item.end_time || ""))
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
      prev.includes(branchId) ? prev.filter((id) => id !== branchId) : [...prev, branchId]
    )
  }

  async function handleCreateUserFromEmployees() {
    const safeFullName = fullName.trim()
    const safeArabicName = arabicName.trim()
    const safeEmployeeNumber = employeeNumber.trim()
    const safeUsername = username.trim().toLowerCase()
    const safeEmail = email.trim().toLowerCase()
    const safePhone = phone.trim()
    const safeDepartmentId = selectedDepartmentId ? Number(selectedDepartmentId) : null
    const safeJobTitleId = selectedJobTitleId ? Number(selectedJobTitleId) : null

    if (!safeFullName) {
      toast.error(t.fullNameRequired)
      return
    }

    if (!safeUsername) {
      toast.error(t.usernameRequired)
      return
    }

    if (safeUsername.length < 3) {
      toast.error(t.usernameLength)
      return
    }

    if (!safeEmail || !isValidEmail(safeEmail)) {
      toast.error(t.emailInvalid)
      return
    }

    if (!safeDepartmentId) {
      toast.error(t.departmentRequired)
      return
    }

    setSubmitting(true)

    try {
      const csrfToken = getCookie("csrftoken")
      const temporaryPassword = `Primey@${Math.floor(100000 + Math.random() * 900000)}`

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
            arabic_name: safeArabicName || null,
            employee_number: safeEmployeeNumber || null,
            mobile_number: safePhone || null,
            department_id: safeDepartmentId,
            job_title_id: safeJobTitleId,
            branch_ids: selectedBranchIds,
          },
          user: {
            username: safeUsername,
            email: safeEmail,
            password: temporaryPassword,
            role,
            status,
            phone: safePhone || null,
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
          firstError || createData.error || createData.message || t.createCompanyUserFailed
        )
      }

      const createdEmployeeId = createData.employee_id || createData.data?.employee_id

      if (createdEmployeeId && selectedWorkScheduleId) {
        const scheduleResponse = await fetch(
          `${API_BASE}/api/company/employees/${createdEmployeeId}/assign-work-schedule/`,
          {
            method: "POST",
            credentials: "include",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrfToken,
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
            scheduleData.error || scheduleData.message || t.workScheduleAssignFailed
          )
        }
      }

      toast.success(t.companyUserCreated, {
        description:
          createData.temporary_password ||
          createData.data?.temporary_password ||
          `${t.temporaryPassword}: ${temporaryPassword}`,
      })

      resetCreateForm()
      setOpenCreateDialog(false)
      await fetchEmployees(true)
    } catch (error) {
      console.error("Create company user error:", error)
      toast.error(error instanceof Error ? error.message : t.createCompanyUserFailed)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleCreateBranch() {
    const safeName = newBranchName.trim()
    if (!safeName) {
      toast.error(t.branchNameRequired)
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
        (data.success === true || data.status === "success" || data.status === "ok")

      if (!isSuccess) {
        throw new Error(data.error || data.message || t.branchCreateFailed)
      }

      toast.success(data.message || t.branchCreated)
      setNewBranchName("")
      setOpenBranchDialog(false)
      await fetchLookups()
    } catch (error) {
      console.error("Create branch error:", error)
      toast.error(error instanceof Error ? error.message : t.branchCreateFailed)
    } finally {
      setCreatingBranch(false)
    }
  }

  async function handleCreateDepartment() {
    const safeName = newDepartmentName.trim()
    if (!safeName) {
      toast.error(t.departmentNameRequired)
      return
    }

    setCreatingDepartment(true)

    try {
      const csrfToken = getCookie("csrftoken")
      const response = await fetch(`${API_BASE}/api/company/departments/create/`, {
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
        (data.success === true || data.status === "success" || data.status === "ok")

      if (!isSuccess) {
        throw new Error(data.error || data.message || t.departmentCreateFailed)
      }

      toast.success(data.message || t.departmentCreated)
      setNewDepartmentName("")
      setOpenDepartmentDialog(false)
      await fetchLookups()
    } catch (error) {
      console.error("Create department error:", error)
      toast.error(error instanceof Error ? error.message : t.departmentCreateFailed)
    } finally {
      setCreatingDepartment(false)
    }
  }

  async function handleCreateJobTitle() {
    const safeName = newJobTitleName.trim()
    if (!safeName) {
      toast.error(t.jobTitleNameRequired)
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
        (data.success === true || data.status === "success" || data.status === "ok")

      if (!isSuccess) {
        throw new Error(data.error || data.message || t.jobTitleCreateFailed)
      }

      toast.success(data.message || t.jobTitleCreated)
      setNewJobTitleName("")
      setOpenJobTitleDialog(false)
      await fetchLookups()
    } catch (error) {
      console.error("Create job title error:", error)
      toast.error(error instanceof Error ? error.message : t.jobTitleCreateFailed)
    } finally {
      setCreatingJobTitle(false)
    }
  }

  async function handleToggleWorkSchedule(item: LookupItem) {
    try {
      const csrfToken = getCookie("csrftoken")

      const response = await fetch(
        `${API_BASE}/api/company/work-schedules/${item.id}/toggle/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
        }
      )

      const data: GenericApiResponse & { is_active?: boolean } = await response.json()

      const isSuccess =
        response.ok &&
        (data.success === true || data.status === "success" || data.status === "ok")

      if (!isSuccess) {
        throw new Error(data.error || data.message || t.workScheduleSaveFailed)
      }

      toast.success(
        data.is_active === false ? t.statusInactive : t.statusActive
      )

      await fetchLookups()
    } catch (error) {
      console.error("Toggle work schedule error:", error)
      toast.error(error instanceof Error ? error.message : t.workScheduleSaveFailed)
    }
  }

  async function handleCreateWorkSchedule() {
    const safeName = newWorkScheduleName.trim()

    if (!safeName) {
      toast.error(t.workScheduleNameRequired)
      return
    }

    if (!newWorkScheduleWeekendDay) {
      toast.error(t.weekendDayRequired)
      return
    }

    if (newWorkScheduleType !== "HOURLY") {
      if (!newWorkSchedulePeriod1Start || !newWorkSchedulePeriod1End) {
        toast.error(t.firstPeriodRequired)
        return
      }

      if (newWorkScheduleType === "PART_TIME") {
        if (!newWorkSchedulePeriod2Start || !newWorkSchedulePeriod2End) {
          toast.error(t.secondPeriodRequired)
          return
        }
      }
    }

    if (newWorkScheduleType === "HOURLY" && !newWorkScheduleTargetHours) {
      toast.error(t.targetHoursRequired)
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

      if (editingScheduleId) payload.id = editingScheduleId

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
        (data.success === true || data.status === "success" || data.status === "ok")

      if (!isSuccess) {
        throw new Error(data.error || data.message || t.workScheduleSaveFailed)
      }

      toast.success(
        data.message || (editingScheduleId ? t.workScheduleUpdated : t.workScheduleCreated)
      )

      resetWorkScheduleForm()
      setOpenWorkScheduleDialog(false)
      await fetchLookups()
    } catch (error) {
      console.error("Create/update work schedule error:", error)
      toast.error(error instanceof Error ? error.message : t.workScheduleSaveFailed)
    } finally {
      setCreatingWorkSchedule(false)
    }
  }

  function handlePrint() {
    window.print()
    toast.success(t.printOpened)
  }

  const departments = useMemo(
    () => Array.from(new Set(employees.map((item) => item.department).filter(Boolean))),
    [employees]
  )

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
      const safeSearch = search.trim().toLowerCase()

      const matchesSearch =
        !safeSearch ||
        employee.full_name.toLowerCase().includes(safeSearch) ||
        employee.email.toLowerCase().includes(safeSearch) ||
        employee.phone.toLowerCase().includes(safeSearch) ||
        employee.employee_code.toLowerCase().includes(safeSearch) ||
        employee.department.toLowerCase().includes(safeSearch) ||
        employee.job_title.toLowerCase().includes(safeSearch) ||
        (employee.username || "").toLowerCase().includes(safeSearch) ||
        (employee.role || "").toLowerCase().includes(safeSearch) ||
        employee.branch.toLowerCase().includes(safeSearch)

      const matchesStatus = statusFilter === "ALL" || employee.status === statusFilter
      const matchesDepartment =
        departmentFilter === "ALL" || employee.department === departmentFilter
      const matchesBranch =
        branchFilter === "ALL" ||
        employee.branches.some((branch) => branch.name === branchFilter)

      return matchesSearch && matchesStatus && matchesDepartment && matchesBranch
    })
  }, [employees, search, statusFilter, departmentFilter, branchFilter])

  const stats = useMemo(() => {
    const total = employees.length
    const active = employees.filter((e) => e.status === "ACTIVE").length
    const inactive = employees.filter((e) => e.status === "INACTIVE").length
    const departmentsCount = departments.length
    return { total, active, inactive, departmentsCount }
  }, [employees, departments])

  return (
    <div dir={direction} className="space-y-6">
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

      <div className="no-print flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 rounded-full border bg-muted/40 px-3 py-1 text-xs font-medium">
            <Sparkles className="h-3.5 w-3.5" />
            {t.pageTitle}
          </div>

          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            {t.pageTitle}
          </h1>
          <p className="text-sm text-muted-foreground md:text-base">
            {t.pageDescription}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Dialog open={openCreateDialog} onOpenChange={setOpenCreateDialog}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <UserPlus className="h-4 w-4" />
                {t.addEmployee}
              </Button>
            </DialogTrigger>

            <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl" dir={direction}>
              <DialogHeader>
                <DialogTitle>{t.addCompanyUser}</DialogTitle>
                <DialogDescription>{t.addCompanyUserDescription}</DialogDescription>
              </DialogHeader>

              <div className="grid grid-cols-1 gap-6 py-2 lg:grid-cols-3">
                <div className="lg:col-span-2">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.fullName}</label>
                      <Input
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder={t.exampleFullName}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.arabicName}</label>
                      <Input
                        value={arabicName}
                        onChange={(e) => setArabicName(e.target.value)}
                        placeholder={t.exampleArabicName}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.employeeNumber}</label>
                      <Input
                        dir="ltr"
                        lang="en"
                        value={employeeNumber}
                        onChange={(e) => setEmployeeNumber(e.target.value)}
                        placeholder={t.exampleEmployeeNumber}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.username}</label>
                      <Input
                        dir="ltr"
                        lang="en"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder={t.exampleUsername}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.email}</label>
                      <Input
                        dir="ltr"
                        lang="en"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder={t.exampleEmail}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.phone}</label>
                      <Input
                        dir="ltr"
                        lang="en"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder={t.examplePhone}
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.role}</label>
                      <Select value={role} onValueChange={(value) => setRole(value as CompanyRole)}>
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
                      <label className="text-sm font-medium">{t.userStatus}</label>
                      <Select
                        value={status}
                        onValueChange={(value) => setStatus(value as UserStatus)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder={t.selectStatus} />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ACTIVE">{t.statusActive}</SelectItem>
                          <SelectItem value="INACTIVE">{t.statusInactive}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">{t.department}</label>
                      <Select value={selectedDepartmentId} onValueChange={setSelectedDepartmentId}>
                        <SelectTrigger>
                          <SelectValue
                            placeholder={
                              loadingLookups ? t.loadingDepartments : t.selectDepartment
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
                      <label className="text-sm font-medium">{t.jobTitle}</label>
                      <Select value={selectedJobTitleId} onValueChange={setSelectedJobTitleId}>
                        <SelectTrigger>
                          <SelectValue
                            placeholder={
                              loadingLookups ? t.loadingJobTitles : t.selectJobTitle
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
                      <label className="text-sm font-medium">{t.workSchedule}</label>
                      <Select
                        value={selectedWorkScheduleId}
                        onValueChange={setSelectedWorkScheduleId}
                      >
                        <SelectTrigger>
                          <SelectValue
                            placeholder={
                              loadingLookups ? t.loadingSchedules : t.selectWorkSchedule
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
                      <label className="text-sm font-medium">{t.branches}</label>

                      <div className="rounded-2xl border border-border/60 bg-muted/30 p-3">
                        <div className="mb-3 text-sm text-muted-foreground">
                          {selectedBranchNames || t.selectBranches}
                        </div>

                        <div className="max-h-44 space-y-2 overflow-y-auto">
                          {branchOptions.length === 0 ? (
                            <div className="text-sm text-muted-foreground">
                              {loadingLookups ? t.loadingBranches : t.noBranchesAvailable}
                            </div>
                          ) : (
                            branchOptions.map((branch) => {
                              const checked = selectedBranchIds.includes(branch.id)

                              return (
                                <div
                                  key={branch.id}
                                  className="flex items-center justify-between rounded-xl border border-border/60 bg-background px-3 py-2"
                                >
                                  <label
                                    htmlFor={`branch-${branch.id}`}
                                    className="flex flex-1 cursor-pointer items-center gap-3"
                                  >
                                    <Checkbox
                                      id={`branch-${branch.id}`}
                                      checked={checked}
                                      onCheckedChange={() => toggleBranch(branch.id)}
                                    />
                                    <span className="text-sm font-medium">{branch.name}</span>
                                  </label>

                                  {checked ? (
                                    <Check className="h-4 w-4 text-emerald-600" />
                                  ) : null}
                                </div>
                              )
                            })
                          )}
                        </div>
                      </div>
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
                      {getRoleLabel(role, lang)}
                    </span>

                    <Separator />

                    <div className="space-y-3 text-sm">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">{t.arabicName}</span>
                        <span className="font-medium text-end">{arabicName || "—"}</span>
                      </div>

                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">{t.employeeNumber}</span>
                        <span dir="ltr" className="font-medium">{employeeNumber || "—"}</span>
                      </div>

                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">{t.userStatus}</span>
                        <span className="font-medium">
                          {status === "ACTIVE" ? t.statusActive : t.statusInactive}
                        </span>
                      </div>

                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">{t.department}</span>
                        <span className="font-medium text-end">
                          {departmentOptions.find(
                            (item) => String(item.id) === selectedDepartmentId
                          )?.name || "—"}
                        </span>
                      </div>

                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">{t.jobTitle}</span>
                        <span className="font-medium text-end">
                          {jobTitleOptions.find(
                            (item) => String(item.id) === selectedJobTitleId
                          )?.name || "—"}
                        </span>
                      </div>

                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">{t.branches}</span>
                        <span dir="ltr" className="font-medium">
                          {formatEnglishNumber(selectedBranchIds.length)}
                        </span>
                      </div>

                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">{t.workSchedule}</span>
                        <span className="font-medium text-end">
                          {workScheduleOptions.find(
                            (item) => String(item.id) === selectedWorkScheduleId
                          )?.name || "—"}
                        </span>
                      </div>

                      <div className="flex items-center justify-between gap-3">
                        <span className="text-muted-foreground">{t.binding}</span>
                        <span className="font-medium text-emerald-600">
                          {t.companyBinding}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    resetCreateForm()
                    setOpenCreateDialog(false)
                  }}
                >
                  {t.cancel}
                </Button>

                <Button onClick={handleCreateUserFromEmployees} disabled={submitting} className="gap-2">
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

          <Button variant="outline" onClick={() => fetchEmployees(true)} disabled={refreshing} className="gap-2">
            {refreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {t.refresh}
          </Button>

          <Button variant="outline" onClick={downloadExcelFile.bind(null, filteredEmployees, lang)} className="gap-2">
            <FileSpreadsheet className="h-4 w-4" />
            {t.excel}
          </Button>

          <Button variant="outline" onClick={handlePrint} className="gap-2">
            <FileDown className="h-4 w-4" />
            {t.pdf}
          </Button>
        </div>
      </div>

      <div className="no-print grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title={t.totalEmployees}
          value={stats.total}
          description={t.allEmployeesDesc}
          icon={Users}
        />
        <StatCard
          title={t.activeEmployees}
          value={stats.active}
          description={t.activeEmployeesDesc}
          icon={UserCheck}
          valueClassName="text-emerald-600"
        />
        <StatCard
          title={t.inactiveEmployees}
          value={stats.inactive}
          description={t.inactiveEmployeesDesc}
          icon={UserX}
          valueClassName="text-red-600"
        />
        <StatCard
          title={t.departmentsCount}
          value={stats.departmentsCount}
          description={t.departmentsCountDesc}
          icon={Building2}
          valueClassName="text-blue-600"
        />
      </div>

      <Card className="no-print border-border/60">
        <CardHeader>
          <CardTitle>{t.filtersTitle}</CardTitle>
          <CardDescription>{t.filtersDescription}</CardDescription>
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
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t.searchPlaceholder}
                className={isArabic ? "pr-10" : "pl-10"}
              />
            </div>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={t.filterStatus} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">{t.allStatuses}</SelectItem>
                <SelectItem value="ACTIVE">{t.statusActive}</SelectItem>
                <SelectItem value="INACTIVE">{t.statusInactive}</SelectItem>
                <SelectItem value="ON_LEAVE">{t.statusOnLeave}</SelectItem>
              </SelectContent>
            </Select>

            <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={t.filterDepartment} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">{t.allDepartments}</SelectItem>
                {departments.map((department) => (
                  <SelectItem key={department} value={department}>
                    {department}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={branchFilter} onValueChange={setBranchFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder={t.filterBranch} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">{t.allBranches}</SelectItem>
                {branches.map((branch) => (
                  <SelectItem key={branch} value={branch}>
                    {branch}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              onClick={() => {
                setSearch("")
                setStatusFilter("ALL")
                setDepartmentFilter("ALL")
                setBranchFilter("ALL")
                toast.success(t.filtersReset)
              }}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              {t.reset}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="employees-print-area border-border/60">
        <CardHeader>
          <CardTitle>{t.employeesList}</CardTitle>
          <CardDescription>
            {t.totalResults}: <span dir="ltr">{formatEnglishNumber(filteredEmployees.length)}</span>
          </CardDescription>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-14 text-muted-foreground">
              <Loader2 className="me-2 h-5 w-5 animate-spin" />
              {t.loadingEmployees}
            </div>
          ) : (
            <>
              <div className="hidden lg:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="min-w-[280px]">{t.employee}</TableHead>
                      <TableHead>{t.employeeNo}</TableHead>
                      <TableHead>{t.department}</TableHead>
                      <TableHead>{t.jobTitle}</TableHead>
                      <TableHead className="min-w-[180px]">{t.employeeBranches}</TableHead>
                      <TableHead>{t.userStatus}</TableHead>
                      <TableHead>{t.joinDate}</TableHead>
                      <TableHead>{t.actions}</TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {filteredEmployees.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="py-12 text-center text-muted-foreground">
                          {t.noResults}
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredEmployees.map((employee) => (
                        <TableRow key={employee.id}>
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <Avatar className="h-10 w-10 shrink-0">
                                <AvatarImage src={employee.avatar || ""} alt={employee.full_name} />
                                <AvatarFallback>{getInitials(employee.full_name)}</AvatarFallback>
                              </Avatar>

                              <div className="min-w-0">
                                <div className="truncate font-medium">{employee.full_name}</div>

                                <div className="mt-1 flex flex-wrap items-center gap-2">
                                  {employee.role ? (
                                    <span
                                      className={cn(
                                        "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium gap-1",
                                        getRoleBadgeClass((employee.role.toUpperCase() as CompanyRole) || "EMPLOYEE")
                                      )}
                                    >
                                      {getRoleLabel(employee.role, lang)}
                                    </span>
                                  ) : null}
                                </div>

                                <div className="mt-2 space-y-1.5 text-xs text-muted-foreground">
                                  <div dir="ltr" className="flex items-center gap-1.5">
                                    <Mail className="h-3.5 w-3.5 shrink-0" />
                                    <span className="truncate">{employee.email || "—"}</span>
                                  </div>

                                  <div dir="ltr" className="flex items-center gap-1.5">
                                    <Phone className="h-3.5 w-3.5 shrink-0" />
                                    <span className="truncate">{employee.phone || "—"}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </TableCell>

                          <TableCell dir="ltr" className="tabular-nums">
                            {employee.employee_code || "—"}
                          </TableCell>

                          <TableCell>{employee.department || "—"}</TableCell>

                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Briefcase className="h-4 w-4 text-muted-foreground" />
                              <span>{employee.job_title || "—"}</span>
                            </div>
                          </TableCell>

                          <TableCell>
                            {employee.branches.length > 0 ? (
                              <div className="flex flex-col items-start gap-1.5">
                                {employee.branches.map((branch) => (
                                  <div
                                    key={branch.id}
                                    className="inline-flex items-center gap-1.5 rounded-full border border-border/60 bg-muted/30 px-2.5 py-1 text-xs"
                                  >
                                    <GitBranch className="h-3.5 w-3.5 text-muted-foreground" />
                                    <span>{branch.name}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <span className="text-sm text-muted-foreground">—</span>
                            )}
                          </TableCell>

                          <TableCell>
                            <StatusBadge status={employee.status} lang={lang} />
                          </TableCell>

                          <TableCell dir="ltr" className="tabular-nums">
                            {formatDateLabel(employee.join_date)}
                          </TableCell>

                          <TableCell>
                            <Button asChild size="sm" variant="outline" className="gap-2">
                              <Link href={`/company/employees/${employee.id}`}>
                                <Eye className="h-4 w-4" />
                                {t.view}
                              </Link>
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>

              <div className="grid gap-4 lg:hidden">
                {filteredEmployees.length === 0 ? (
                  <div className="py-10 text-center text-sm text-muted-foreground">
                    {t.noResultsDescription}
                  </div>
                ) : (
                  filteredEmployees.map((employee) => (
                    <div
                      key={employee.id}
                      className="rounded-2xl border border-border/60 bg-background p-4 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex min-w-0 flex-1 items-start gap-3">
                          <Avatar className="h-12 w-12 shrink-0">
                            <AvatarImage src={employee.avatar || ""} alt={employee.full_name} />
                            <AvatarFallback>{getInitials(employee.full_name)}</AvatarFallback>
                          </Avatar>

                          <div className="min-w-0 flex-1">
                            <div className="truncate font-semibold">{employee.full_name}</div>
                            <div className="mt-1 flex flex-wrap items-center gap-2">
                              {employee.role ? (
                                <span
                                  className={cn(
                                    "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium",
                                    getRoleBadgeClass((employee.role.toUpperCase() as CompanyRole) || "EMPLOYEE")
                                  )}
                                >
                                  {getRoleLabel(employee.role, lang)}
                                </span>
                              ) : null}
                              <StatusBadge status={employee.status} lang={lang} />
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.employeeNo}</p>
                          <p dir="ltr" className="mt-1 font-medium tabular-nums">
                            {employee.employee_code || "—"}
                          </p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">{t.joinDate}</p>
                          <p dir="ltr" className="mt-1 font-medium tabular-nums">
                            {formatDateLabel(employee.join_date)}
                          </p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3 col-span-2">
                          <p className="text-xs text-muted-foreground">{t.department}</p>
                          <p className="mt-1 font-medium">{employee.department || "—"}</p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3 col-span-2">
                          <p className="text-xs text-muted-foreground">{t.jobTitle}</p>
                          <p className="mt-1 font-medium">{employee.job_title || "—"}</p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3 col-span-2">
                          <p className="text-xs text-muted-foreground">{t.employeeBranches}</p>
                          {employee.branches.length > 0 ? (
                            <div className="mt-2 flex flex-col items-start gap-1.5">
                              {employee.branches.map((branch) => (
                                <div
                                  key={branch.id}
                                  className="inline-flex items-center gap-1.5 rounded-full border border-border/60 bg-background px-2.5 py-1 text-xs"
                                >
                                  <GitBranch className="h-3.5 w-3.5 text-muted-foreground" />
                                  <span>{branch.name}</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="mt-1 font-medium">—</p>
                          )}
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3 col-span-2">
                          <p className="text-xs text-muted-foreground">{t.email}</p>
                          <p dir="ltr" className="mt-1 truncate font-medium">
                            {employee.email || "—"}
                          </p>
                        </div>

                        <div className="rounded-xl border bg-muted/30 p-3 col-span-2">
                          <p className="text-xs text-muted-foreground">{t.phone}</p>
                          <p dir="ltr" className="mt-1 font-medium">
                            {employee.phone || "—"}
                          </p>
                        </div>
                      </div>

                      <Button asChild variant="outline" className="mt-4 w-full gap-2">
                        <Link href={`/company/employees/${employee.id}`}>
                          <Eye className="h-4 w-4" />
                          {t.view}
                        </Link>
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="no-print grid gap-4 xl:grid-cols-3">
        <MasterDataCard
          title={t.branchCardTitle}
          subtitle={t.branchCardSubtitle}
          count={branchOptions.length}
          icon={<GitBranch className="h-5 w-5" />}
          items={branchOptions}
          loading={loadingLookups}
          emptyText={t.noBranches}
          onRefresh={fetchLookups}
          open={openBranchDialog}
          onOpenChange={setOpenBranchDialog}
          createTitle={t.addBranchTitle}
          createDescription={t.addBranchDescription}
          createPlaceholder={t.addBranchPlaceholder}
          createValue={newBranchName}
          onCreateValueChange={setNewBranchName}
          onCreate={handleCreateBranch}
          creating={creatingBranch}
          itemIcon={<GitBranch className="h-4 w-4" />}
          lang={lang}
        />

        <MasterDataCard
          title={t.departmentCardTitle}
          subtitle={t.departmentCardSubtitle}
          count={departmentOptions.length}
          icon={<Building2 className="h-5 w-5" />}
          items={departmentOptions}
          loading={loadingLookups}
          emptyText={t.noDepartments}
          onRefresh={fetchLookups}
          open={openDepartmentDialog}
          onOpenChange={setOpenDepartmentDialog}
          createTitle={t.addDepartmentTitle}
          createDescription={t.addDepartmentDescription}
          createPlaceholder={t.addDepartmentPlaceholder}
          createValue={newDepartmentName}
          onCreateValueChange={setNewDepartmentName}
          onCreate={handleCreateDepartment}
          creating={creatingDepartment}
          itemIcon={<Building2 className="h-4 w-4" />}
          lang={lang}
        />

        <MasterDataCard
          title={t.jobTitleCardTitle}
          subtitle={t.jobTitleCardSubtitle}
          count={jobTitleOptions.length}
          icon={<Layers3 className="h-5 w-5" />}
          items={jobTitleOptions}
          loading={loadingLookups}
          emptyText={t.noJobTitles}
          onRefresh={fetchLookups}
          open={openJobTitleDialog}
          onOpenChange={setOpenJobTitleDialog}
          createTitle={t.addJobTitleTitle}
          createDescription={t.addJobTitleDescription}
          createPlaceholder={t.addJobTitlePlaceholder}
          createValue={newJobTitleName}
          onCreateValueChange={setNewJobTitleName}
          onCreate={handleCreateJobTitle}
          creating={creatingJobTitle}
          itemIcon={<Briefcase className="h-4 w-4" />}
          lang={lang}
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
          onToggleItem={handleToggleWorkSchedule}
          lang={lang}
        />
      </div>

      <Card className="no-print border-border/60">
        <CardContent className="flex flex-col gap-3 p-5 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <div className="text-sm font-medium">{t.quickSummary}</div>
            <div className="text-sm text-muted-foreground">
              {lang === "ar" ? (
                <>
                  لديك الآن <span dir="ltr">{formatEnglishNumber(filteredEmployees.length)}</span> نتيجة
                  معروضة، و <span dir="ltr">{formatEnglishNumber(workScheduleOptions.length)}</span> فترة
                  عمل، و <span dir="ltr">{formatEnglishNumber(branchOptions.length)}</span> فرع، و{" "}
                  <span dir="ltr">{formatEnglishNumber(departmentOptions.length)}</span> قسم.
                </>
              ) : (
                <>
                  You currently have <span dir="ltr">{formatEnglishNumber(filteredEmployees.length)}</span>{" "}
                  visible results, <span dir="ltr">{formatEnglishNumber(workScheduleOptions.length)}</span>{" "}
                  work schedules, <span dir="ltr">{formatEnglishNumber(branchOptions.length)}</span>{" "}
                  branches, and <span dir="ltr">{formatEnglishNumber(departmentOptions.length)}</span>{" "}
                  departments.
                </>
              )}
            </div>
          </div>

          <Link
            href="/company/profile"
            className="inline-flex items-center gap-2 text-sm font-medium text-primary transition hover:opacity-80"
          >
            {t.goToCompanyProfile}
            <ChevronRight className={cn("h-4 w-4", isArabic ? "rotate-180" : "")} />
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}