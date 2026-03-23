"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity,
  ArrowRightLeft,
  BarChart3,
  BadgeCheck,
  Briefcase,
  CalendarRange,
  CheckCircle2,
  CircleDot,
  ClipboardCheck,
  Eye,
  FilePlus2,
  FileText,
  Filter,
  Layers3,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  UserCog,
  Users,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type Locale = "ar" | "en"
type Direction = "rtl" | "ltr"

type DashboardSummary = {
  templates_count: number
  reviews_count: number
  completed_reviews_count: number
  average_final_score: number | null
  status_summary: {
    self_pending: number
    manager_pending: number
    hr_pending: number
    completed: number
  }
}

type PerformanceItem = {
  id: number
  question: string
  item_type: "SCORE" | "TEXT" | string
  max_score: number
  weight: number
}

type PerformanceCategory = {
  id: number
  name: string
  weight: number
  items_count: number
  items: PerformanceItem[]
}

type PerformanceTemplate = {
  id: number
  name: string
  period: string
  description?: string | null
  is_active: boolean
  categories_count: number
  categories: PerformanceCategory[]
  created_at?: string
  updated_at?: string
}

type ReviewAnswer = {
  id: number
  item_id: number | null
  question: string | null
  item_type: string | null
  max_score: number | null
  item_weight: number | null
  category_id: number | null
  category_name: string | null
  self_answer: string | null
  manager_answer: string | null
  hr_answer: string | null
  self_score: number | null
  manager_score: number | null
  hr_score: number | null
}

type ReviewWorkflow = {
  self_completed: boolean
  manager_completed: boolean
  hr_completed: boolean
  last_update: string | null
}

type PerformanceReview = {
  id: number
  employee: {
    id: number
    name: string
    email?: string | null
    phone?: string | null
    avatar?: string | null
  }
  template: {
    id: number
    name: string | null
    period: string | null
  }
  period_label: string
  status: string
  self_score: number | null
  manager_score: number | null
  hr_score: number | null
  final_score: number | null
  final_decision: string | null
  workflow: ReviewWorkflow
  answers_count: number
  answers: ReviewAnswer[]
  created_at?: string
  updated_at?: string
}

type EmployeeLookup = {
  id: number
  name: string
  email?: string | null
  phone?: string | null
  avatar?: string | null
}

type CreateTemplateCategoryForm = {
  name: string
  weight: string
  items: {
    question: string
    item_type: "SCORE" | "TEXT"
    max_score: string
    weight: string
  }[]
}

const emptyTemplateCategory = (): CreateTemplateCategoryForm => ({
  name: "",
  weight: "20",
  items: [
    {
      question: "",
      item_type: "SCORE",
      max_score: "5",
      weight: "10",
    },
  ],
})

const messages = {
  ar: {
    moduleBadge: "Performance Center",
    pageTitle: "إدارة الأداء والتقييم",
    pageDescription:
      "صفحة تشغيل احترافية لإدارة قوالب التقييم، إنشاء دورات الأداء، ومتابعة سير التقييم بين الموظف والمدير والموارد البشرية.",

    refresh: "تحديث",
    createTemplate: "قالب جديد",
    createReview: "إنشاء تقييم",
    viewReviews: "عرض التقييمات",
    viewAllReviews: "عرض كل التقييمات",
    view: "عرض",
    close: "إغلاق",
    cancel: "إلغاء",
    saveTemplate: "حفظ القالب",

    totalTemplates: "إجمالي القوالب",
    totalReviews: "إجمالي التقييمات",
    completedReviews: "المكتملة",
    averageScore: "متوسط النتيجة",
    templatesHint: "قوالب التقييم الجاهزة",
    reviewsHint: "كل التقييمات المسجلة",
    completedHint: "تمت معالجتها بالكامل",
    averageHint: "متوسط الدرجة النهائية",

    operationalOverview: "نظرة تشغيلية",
    operationalOverviewDesc: "توزيع الحالات الحالية داخل دورة تقييم الأداء.",
    quickTips: "تلميحات سريعة",
    quickTipsDesc: "تسلسل العمل الموصى به داخل الموديول.",

    selfPending: "بانتظار الموظف",
    managerPending: "بانتظار المدير",
    hrPending: "بانتظار الموارد البشرية",
    completed: "مكتمل",

    tip1Title: "1) أنشئ القالب",
    tip1Desc: "حدد الفئات وعناصر القياس والأوزان.",
    tip2Title: "2) أنشئ التقييم",
    tip2Desc: "اربط الموظف بالقالب والدورة التقييمية.",
    tip3Title: "3) تابع الـ Workflow",
    tip3Desc: "الموظف ← المدير ← الموارد البشرية حتى الاكتمال النهائي.",

    startTemplateTitle: "ابدأ بقالب جديد",
    startTemplateDesc: "أنشئ هيكل التقييم أولًا.",
    createTemplateBtn: "إنشاء قالب",

    startReviewTitle: "أنشئ دورة تقييم",
    startReviewDesc: "اربط موظفًا بقالب تقييم.",
    createReviewBtn: "إنشاء تقييم",

    followWorkflowTitle: "تابع الدورة الحالية",
    followWorkflowDesc: "راقب سير الموظف → المدير → الموارد البشرية.",

    tabOverview: "النظرة العامة",
    tabTemplates: "القوالب",
    tabReviews: "التقييمات",

    latestReviews: "أحدث التقييمات",
    latestReviewsDesc: "آخر عناصر الأداء التي تم إنشاؤها أو تحديثها.",
    noReviewsYet: "لا توجد تقييمات بعد. ابدأ بإنشاء قالب ثم أضف تقييمًا جديدًا.",

    templatesTitle: "قوالب التقييم",
    templatesDesc: "إدارة القوالب والفئات وعناصر القياس داخل الشركة.",
    searchTemplates: "بحث في القوالب...",
    noTemplates: "لا توجد قوالب مطابقة حاليًا.",
    noDescription: "بدون وصف",
    active: "نشط",
    inactive: "غير نشط",
    categories: "فئات",
    items: "عناصر",
    weight: "وزن",
    createdAt: "الإنشاء",
    updatedAt: "التحديث",
    extraCategories: "فئات إضافية",
    createReviewFromTemplate: "إنشاء تقييم من هذا القالب",

    reviewsTitle: "التقييمات",
    reviewsDesc: "متابعة التقييمات، حالتها، ونتائجها النهائية.",
    searchReviews: "بحث باسم الموظف أو القالب أو الدورة...",
    statusFilter: "تصفية الحالة",
    allStatuses: "كل الحالات",
    noMatchingReviews: "لا توجد تقييمات مطابقة حاليًا.",

    employee: "الموظف",
    template: "القالب",
    cycle: "الدورة",
    status: "الحالة",
    finalScore: "الدرجة النهائية",
    createdDate: "تاريخ الإنشاء",
    selfScore: "الدرجة الذاتية",
    managerScore: "درجة المدير",
    hrScore: "درجة الموارد البشرية",
    workflowStatus: "حالة الـ Workflow",
    lastUpdate: "آخر تحديث",
    action: "الإجراء",
    emailFallback: "—",

    employeeLabel: "الموظف",
    templateLabel: "القالب",
    periodLabel: "الدورة التقييمية",
    description: "الوصف",
    period: "الفترة",
    chooseEmployee: "اختر الموظف",
    chooseTemplate: "اختر القالب",
    choosePeriod: "اختر الفترة",
    selectedTemplate: "القالب المختار",
    name: "الاسم",
    categoriesCount: "الفئات",

    createTemplateDialogTitle: "إنشاء قالب تقييم جديد",
    createTemplateDialogDesc:
      "أنشئ القالب مع الفئات والعناصر ليتم استخدامه لاحقًا في دورات الأداء.",
    templateName: "اسم القالب",
    templateNamePlaceholder: "مثال: التقييم السنوي للإدارة",
    descriptionPlaceholder: "وصف مختصر عن استخدام القالب...",
    sectionsAndItems: "الفئات والعناصر",
    sectionsAndItemsDesc: "أنشئ هيكل التقييم بالكامل قبل الحفظ.",
    addCategory: "إضافة فئة",
    deleteCategory: "حذف الفئة",
    categoryName: "اسم الفئة",
    categoryNamePlaceholder: "مثال: الأداء الوظيفي",
    categoryWeight: "وزن الفئة",
    questionLabel: "السؤال / العنصر",
    questionPlaceholder: "أدخل السؤال أو عنصر التقييم",
    type: "النوع",
    maxScore: "أقصى درجة",
    itemWeight: "الوزن",
    delete: "حذف",
    addItem: "إضافة عنصر",
    scoreType: "درجة",
    textType: "نصي",

    createReviewDialogTitle: "إنشاء تقييم جديد",
    createReviewDialogDesc: "اختر الموظف والقالب وأدخل اسم الدورة التقييمية.",
    periodLabelPlaceholder: "مثال: Q1 2026 أو Annual 2026",

    reviewDetailsTitle: "تفاصيل التقييم",
    reviewDetailsDesc: "عرض شامل لسير التقييم والإجابات والدرجات.",
    noDetails: "لا توجد بيانات لعرضها.",
    finalDecision: "القرار",
    workflowState: "حالة الـ Workflow",
    employeeDone: "الموظف",
    managerDone: "المدير",
    hrDone: "HR",
    yes: "مكتمل",
    no: "لا",
    answersAndItems: "العناصر والإجابات",
    answersAndItemsDesc: "تفاصيل كل عنصر داخل القالب مع إجابات الأطراف المختلفة.",
    noAnswers: "لا توجد إجابات بعد.",
    category: "الفئة",
    question: "السؤال",
    employeeAnswer: "إجابة الموظف",
    managerAnswer: "إجابة المدير",
    hrAnswer: "إجابة HR",

    yearly: "سنوي",
    quarterly: "ربع سنوي",
    monthly: "شهري",

    statusSelfPending: "بانتظار الموظف",
    statusManagerPending: "بانتظار المدير",
    statusHrPending: "بانتظار الموارد البشرية",
    statusCompleted: "مكتمل",
    unknown: "غير معروف",

    dashboardError: "تعذر تحميل ملخص الأداء.",
    templatesError: "تعذر تحميل القوالب.",
    reviewsError: "تعذر تحميل التقييمات.",
    employeesError: "تعذر تحميل الموظفين.",
    reviewDetailsError: "تعذر تحميل تفاصيل التقييم.",
    createTemplateSuccess: "تم إنشاء قالب التقييم بنجاح.",
    createTemplateError: "تعذر إنشاء قالب التقييم.",
    createReviewSuccess: "تم إنشاء التقييم بنجاح.",
    createReviewError: "تعذر إنشاء التقييم.",
    templateNameRequired: "يرجى إدخال اسم القالب.",
    oneCategoryRequired: "أضف فئة واحدة على الأقل داخل القالب.",
    categoryItemRequired: "كل فئة يجب أن تحتوي على عنصر واحد على الأقل.",
    employeeRequired: "يرجى اختيار الموظف.",
    templateRequired: "يرجى اختيار القالب.",
    cycleRequired: "يرجى إدخال الدورة التقييمية.",
    loading: "جاري التحميل...",
  },
  en: {
    moduleBadge: "Performance Center",
    pageTitle: "Performance Management",
    pageDescription:
      "A professional operations page to manage evaluation templates, create performance cycles, and track workflow across employee, manager, and HR.",

    refresh: "Refresh",
    createTemplate: "New Template",
    createReview: "Create Review",
    viewReviews: "View Reviews",
    viewAllReviews: "View All Reviews",
    view: "View",
    close: "Close",
    cancel: "Cancel",
    saveTemplate: "Save Template",

    totalTemplates: "Total Templates",
    totalReviews: "Total Reviews",
    completedReviews: "Completed",
    averageScore: "Average Score",
    templatesHint: "Ready-to-use evaluation templates",
    reviewsHint: "All recorded reviews",
    completedHint: "Fully processed reviews",
    averageHint: "Average final score",

    operationalOverview: "Operational Overview",
    operationalOverviewDesc: "Current status distribution inside the performance cycle.",
    quickTips: "Quick Tips",
    quickTipsDesc: "Recommended workflow inside this module.",

    selfPending: "Awaiting Employee",
    managerPending: "Awaiting Manager",
    hrPending: "Awaiting HR",
    completed: "Completed",

    tip1Title: "1) Create the Template",
    tip1Desc: "Define categories, measurement items, and weights.",
    tip2Title: "2) Create the Review",
    tip2Desc: "Link the employee to the template and review cycle.",
    tip3Title: "3) Track the Workflow",
    tip3Desc: "Employee → Manager → HR until final completion.",

    startTemplateTitle: "Start with a New Template",
    startTemplateDesc: "Build the evaluation structure first.",
    createTemplateBtn: "Create Template",

    startReviewTitle: "Create a Review Cycle",
    startReviewDesc: "Link an employee to an evaluation template.",
    createReviewBtn: "Create Review",

    followWorkflowTitle: "Track Current Cycle",
    followWorkflowDesc: "Monitor Employee → Manager → HR progress.",

    tabOverview: "Overview",
    tabTemplates: "Templates",
    tabReviews: "Reviews",

    latestReviews: "Latest Reviews",
    latestReviewsDesc: "Most recently created or updated performance items.",
    noReviewsYet: "No reviews yet. Start by creating a template, then add a new review.",

    templatesTitle: "Evaluation Templates",
    templatesDesc: "Manage templates, categories, and measurement items inside the company.",
    searchTemplates: "Search templates...",
    noTemplates: "No matching templates found.",
    noDescription: "No description",
    active: "Active",
    inactive: "Inactive",
    categories: "categories",
    items: "items",
    weight: "Weight",
    createdAt: "Created",
    updatedAt: "Updated",
    extraCategories: "additional categories",
    createReviewFromTemplate: "Create Review from This Template",

    reviewsTitle: "Reviews",
    reviewsDesc: "Track reviews, statuses, and final results.",
    searchReviews: "Search by employee, template, or cycle...",
    statusFilter: "Filter by status",
    allStatuses: "All Statuses",
    noMatchingReviews: "No matching reviews found.",

    employee: "Employee",
    template: "Template",
    cycle: "Cycle",
    status: "Status",
    finalScore: "Final Score",
    createdDate: "Created Date",
    selfScore: "Self Score",
    managerScore: "Manager Score",
    hrScore: "HR Score",
    workflowStatus: "Workflow Status",
    lastUpdate: "Last Update",
    action: "Action",
    emailFallback: "—",

    employeeLabel: "Employee",
    templateLabel: "Template",
    periodLabel: "Review Cycle",
    description: "Description",
    period: "Period",
    chooseEmployee: "Select employee",
    chooseTemplate: "Select template",
    choosePeriod: "Select period",
    selectedTemplate: "Selected Template",
    name: "Name",
    categoriesCount: "Categories",

    createTemplateDialogTitle: "Create New Evaluation Template",
    createTemplateDialogDesc:
      "Create the template with categories and items to use later in performance cycles.",
    templateName: "Template Name",
    templateNamePlaceholder: "Example: Annual Management Review",
    descriptionPlaceholder: "Short description about template usage...",
    sectionsAndItems: "Categories and Items",
    sectionsAndItemsDesc: "Build the full evaluation structure before saving.",
    addCategory: "Add Category",
    deleteCategory: "Delete Category",
    categoryName: "Category Name",
    categoryNamePlaceholder: "Example: Job Performance",
    categoryWeight: "Category Weight",
    questionLabel: "Question / Item",
    questionPlaceholder: "Enter the question or evaluation item",
    type: "Type",
    maxScore: "Max Score",
    itemWeight: "Weight",
    delete: "Delete",
    addItem: "Add Item",
    scoreType: "Score",
    textType: "Text",

    createReviewDialogTitle: "Create New Review",
    createReviewDialogDesc: "Select the employee and template, then enter the review cycle.",
    periodLabelPlaceholder: "Example: Q1 2026 or Annual 2026",

    reviewDetailsTitle: "Review Details",
    reviewDetailsDesc: "Full view of workflow, answers, and scores.",
    noDetails: "No data available to display.",
    finalDecision: "Decision",
    workflowState: "Workflow State",
    employeeDone: "Employee",
    managerDone: "Manager",
    hrDone: "HR",
    yes: "Completed",
    no: "No",
    answersAndItems: "Items and Answers",
    answersAndItemsDesc:
      "Detailed view of each template item with answers from all participants.",
    noAnswers: "No answers yet.",
    category: "Category",
    question: "Question",
    employeeAnswer: "Employee Answer",
    managerAnswer: "Manager Answer",
    hrAnswer: "HR Answer",

    yearly: "Yearly",
    quarterly: "Quarterly",
    monthly: "Monthly",

    statusSelfPending: "Awaiting Employee",
    statusManagerPending: "Awaiting Manager",
    statusHrPending: "Awaiting HR",
    statusCompleted: "Completed",
    unknown: "Unknown",

    dashboardError: "Failed to load performance summary.",
    templatesError: "Failed to load templates.",
    reviewsError: "Failed to load reviews.",
    employeesError: "Failed to load employees.",
    reviewDetailsError: "Failed to load review details.",
    createTemplateSuccess: "Evaluation template created successfully.",
    createTemplateError: "Failed to create evaluation template.",
    createReviewSuccess: "Review created successfully.",
    createReviewError: "Failed to create review.",
    templateNameRequired: "Please enter the template name.",
    oneCategoryRequired: "Add at least one category to the template.",
    categoryItemRequired: "Each category must contain at least one item.",
    employeeRequired: "Please select the employee.",
    templateRequired: "Please select the template.",
    cycleRequired: "Please enter the review cycle.",
    loading: "Loading...",
  },
} as const

function detectLocale(): Locale {
  if (typeof document === "undefined") return "ar"
  const lang = (document.documentElement.lang || "ar").toLowerCase()
  return lang.startsWith("ar") ? "ar" : "en"
}

function detectDirection(): Direction {
  if (typeof document === "undefined") return "rtl"
  const dir = (document.documentElement.dir || "rtl").toLowerCase()
  return dir === "rtl" ? "rtl" : "ltr"
}

function formatDate(value?: string | null) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat("en-CA-u-nu-latn", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date)
}

function formatDateTime(value?: string | null) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  const datePart = new Intl.DateTimeFormat("en-CA-u-nu-latn", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date)

  const timePart = new Intl.DateTimeFormat("en-GB-u-nu-latn", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date)

  return `${datePart} ${timePart}`
}

function formatScore(value?: number | null) {
  if (value === null || value === undefined) return "—"
  return new Intl.NumberFormat("en-US", {
    numberingSystem: "latn",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value))
}

function formatCount(value?: number | null) {
  if (value === null || value === undefined) return "0"
  return new Intl.NumberFormat("en-US", {
    numberingSystem: "latn",
    maximumFractionDigits: 0,
  }).format(value)
}

function getStatusBadgeVariant(status?: string) {
  switch (status) {
    case "COMPLETED":
      return "default"
    case "HR_PENDING":
      return "secondary"
    case "MANAGER_PENDING":
      return "outline"
    case "SELF_PENDING":
      return "destructive"
    default:
      return "secondary"
  }
}

function getStatusLabel(status: string | undefined, localeText: (typeof messages)["ar"]) {
  switch (status) {
    case "SELF_PENDING":
      return localeText.statusSelfPending
    case "MANAGER_PENDING":
      return localeText.statusManagerPending
    case "HR_PENDING":
      return localeText.statusHrPending
    case "COMPLETED":
      return localeText.statusCompleted
    default:
      return status || localeText.unknown
  }
}

function getPeriodLabel(period: string | undefined, localeText: (typeof messages)["ar"]) {
  switch (period) {
    case "YEARLY":
      return localeText.yearly
    case "QUARTERLY":
      return localeText.quarterly
    case "MONTHLY":
      return localeText.monthly
    default:
      return period || "—"
  }
}

function buildSuggestedPeriodLabel(period?: string) {
  const now = new Date()
  const year = now.getFullYear()
  switch (period) {
    case "YEARLY":
      return `Annual ${year}`
    case "QUARTERLY":
      return `Q1 ${year}`
    case "MONTHLY":
      return `${year}-${String(now.getMonth() + 1).padStart(2, "0")}`
    default:
      return `${year}`
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok || data?.status === "error") {
    throw new Error(data?.message || "Unexpected request error.")
  }

  return data as T
}

export default function CompanyPerformancePage() {
  const [locale, setLocale] = useState<Locale>("ar")
  const [direction, setDirection] = useState<Direction>("rtl")

  const t = messages[locale]

  const [activeTab, setActiveTab] = useState("overview")

  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null)
  const [templates, setTemplates] = useState<PerformanceTemplate[]>([])
  const [reviews, setReviews] = useState<PerformanceReview[]>([])
  const [employees, setEmployees] = useState<EmployeeLookup[]>([])

  const [loadingDashboard, setLoadingDashboard] = useState(true)
  const [loadingTemplates, setLoadingTemplates] = useState(true)
  const [loadingReviews, setLoadingReviews] = useState(true)
  const [loadingEmployees, setLoadingEmployees] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const [templateSearch, setTemplateSearch] = useState("")
  const [reviewSearch, setReviewSearch] = useState("")
  const [reviewStatusFilter, setReviewStatusFilter] = useState("ALL")

  const [createTemplateOpen, setCreateTemplateOpen] = useState(false)
  const [createReviewOpen, setCreateReviewOpen] = useState(false)
  const [reviewDetailsOpen, setReviewDetailsOpen] = useState(false)

  const [submittingTemplate, setSubmittingTemplate] = useState(false)
  const [submittingReview, setSubmittingReview] = useState(false)
  const [loadingReviewDetails, setLoadingReviewDetails] = useState(false)

  const [selectedReview, setSelectedReview] = useState<PerformanceReview | null>(null)

  const [templateForm, setTemplateForm] = useState({
    name: "",
    period: "YEARLY",
    description: "",
    is_active: true,
    categories: [emptyTemplateCategory()],
  })

  const [reviewForm, setReviewForm] = useState({
    employee_id: "",
    template_id: "",
    period_label: "",
  })

  useEffect(() => {
    const applyLocaleState = () => {
      setLocale(detectLocale())
      setDirection(detectDirection())
    }

    applyLocaleState()

    if (typeof document === "undefined") return

    const observer = new MutationObserver(() => {
      applyLocaleState()
    })

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["lang", "dir"],
    })

    window.addEventListener("languagechange", applyLocaleState)

    return () => {
      observer.disconnect()
      window.removeEventListener("languagechange", applyLocaleState)
    }
  }, [])

  const fetchDashboard = useCallback(async () => {
    setLoadingDashboard(true)
    try {
      const data = await apiFetch<{ status: string; summary: DashboardSummary }>(
        "/api/company/performance/dashboard/"
      )
      setDashboard(data.summary)
    } catch (error) {
      console.error("Dashboard load error:", error)
      toast.error(error instanceof Error ? error.message : t.dashboardError)
    } finally {
      setLoadingDashboard(false)
    }
  }, [t.dashboardError])

  const fetchTemplates = useCallback(async () => {
    setLoadingTemplates(true)
    try {
      const data = await apiFetch<{ status: string; templates: PerformanceTemplate[] }>(
        "/api/company/performance/templates/"
      )
      setTemplates(data.templates || [])
    } catch (error) {
      console.error("Templates load error:", error)
      toast.error(error instanceof Error ? error.message : t.templatesError)
    } finally {
      setLoadingTemplates(false)
    }
  }, [t.templatesError])

  const fetchReviews = useCallback(async () => {
    setLoadingReviews(true)
    try {
      const params = new URLSearchParams()
      if (reviewSearch.trim()) params.set("search", reviewSearch.trim())
      if (reviewStatusFilter !== "ALL") params.set("status", reviewStatusFilter)

      const query = params.toString() ? `?${params.toString()}` : ""

      const data = await apiFetch<{ status: string; reviews: PerformanceReview[] }>(
        `/api/company/performance/reviews/${query}`
      )
      setReviews(data.reviews || [])
    } catch (error) {
      console.error("Reviews load error:", error)
      toast.error(error instanceof Error ? error.message : t.reviewsError)
    } finally {
      setLoadingReviews(false)
    }
  }, [reviewSearch, reviewStatusFilter, t.reviewsError])

  const fetchEmployees = useCallback(async () => {
    setLoadingEmployees(true)
    try {
      const data = await apiFetch<{ status: string; employees: EmployeeLookup[] }>(
        "/api/company/performance/employees/lookup/"
      )
      setEmployees(data.employees || [])
    } catch (error) {
      console.error("Employees load error:", error)
      toast.error(error instanceof Error ? error.message : t.employeesError)
    } finally {
      setLoadingEmployees(false)
    }
  }, [t.employeesError])

  const loadAll = useCallback(async () => {
    setRefreshing(true)
    try {
      await Promise.all([
        fetchDashboard(),
        fetchTemplates(),
        fetchReviews(),
        fetchEmployees(),
      ])
    } finally {
      setRefreshing(false)
    }
  }, [fetchDashboard, fetchTemplates, fetchReviews, fetchEmployees])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  useEffect(() => {
    const timer = setTimeout(() => {
      void fetchReviews()
    }, 350)

    return () => clearTimeout(timer)
  }, [reviewSearch, reviewStatusFilter, fetchReviews])

  const filteredTemplates = useMemo(() => {
    const q = templateSearch.trim().toLowerCase()
    if (!q) return templates

    return templates.filter((template) => {
      const haystack = [template.name, template.description || "", template.period]
        .join(" ")
        .toLowerCase()

      return haystack.includes(q)
    })
  }, [templates, templateSearch])

  const selectedTemplateForReview = useMemo(
    () => templates.find((template) => String(template.id) === reviewForm.template_id) || null,
    [templates, reviewForm.template_id]
  )

  const addCategory = () => {
    setTemplateForm((prev) => ({
      ...prev,
      categories: [...prev.categories, emptyTemplateCategory()],
    }))
  }

  const removeCategory = (index: number) => {
    setTemplateForm((prev) => ({
      ...prev,
      categories:
        prev.categories.length === 1
          ? prev.categories
          : prev.categories.filter((_, i) => i !== index),
    }))
  }

  const addItem = (categoryIndex: number) => {
    setTemplateForm((prev) => ({
      ...prev,
      categories: prev.categories.map((category, idx) =>
        idx === categoryIndex
          ? {
              ...category,
              items: [
                ...category.items,
                {
                  question: "",
                  item_type: "SCORE",
                  max_score: "5",
                  weight: "10",
                },
              ],
            }
          : category
      ),
    }))
  }

  const removeItem = (categoryIndex: number, itemIndex: number) => {
    setTemplateForm((prev) => ({
      ...prev,
      categories: prev.categories.map((category, idx) =>
        idx === categoryIndex
          ? {
              ...category,
              items:
                category.items.length === 1
                  ? category.items
                  : category.items.filter((_, i) => i !== itemIndex),
            }
          : category
      ),
    }))
  }

  const openReviewDetails = async (reviewId: number) => {
    setReviewDetailsOpen(true)
    setLoadingReviewDetails(true)
    setSelectedReview(null)

    try {
      const data = await apiFetch<{ status: string; review: PerformanceReview }>(
        `/api/company/performance/reviews/${reviewId}/`
      )
      setSelectedReview(data.review)
    } catch (error) {
      console.error("Review details error:", error)
      toast.error(error instanceof Error ? error.message : t.reviewDetailsError)
      setReviewDetailsOpen(false)
    } finally {
      setLoadingReviewDetails(false)
    }
  }

  const openCreateReviewWithTemplate = (template: PerformanceTemplate) => {
    setReviewForm((prev) => ({
      ...prev,
      template_id: String(template.id),
      period_label: prev.period_label || buildSuggestedPeriodLabel(template.period),
    }))
    setCreateReviewOpen(true)
  }

  const handleCreateTemplate = async () => {
    if (!templateForm.name.trim()) {
      toast.error(t.templateNameRequired)
      return
    }

    const validCategories = templateForm.categories
      .map((category) => ({
        name: category.name.trim(),
        weight: Number(category.weight || "0"),
        items: category.items
          .map((item) => ({
            question: item.question.trim(),
            item_type: item.item_type,
            max_score: Number(item.max_score || "0"),
            weight: Number(item.weight || "0"),
          }))
          .filter((item) => item.question),
      }))
      .filter((category) => category.name)

    if (!validCategories.length) {
      toast.error(t.oneCategoryRequired)
      return
    }

    if (validCategories.some((category) => category.items.length === 0)) {
      toast.error(t.categoryItemRequired)
      return
    }

    setSubmittingTemplate(true)
    try {
      await apiFetch("/api/company/performance/templates/create/", {
        method: "POST",
        body: JSON.stringify({
          name: templateForm.name.trim(),
          period: templateForm.period,
          description: templateForm.description.trim(),
          is_active: templateForm.is_active,
          categories: validCategories,
        }),
      })

      toast.success(t.createTemplateSuccess)
      setCreateTemplateOpen(false)
      setTemplateForm({
        name: "",
        period: "YEARLY",
        description: "",
        is_active: true,
        categories: [emptyTemplateCategory()],
      })

      await Promise.all([fetchTemplates(), fetchDashboard()])
      setActiveTab("templates")
    } catch (error) {
      console.error("Create template error:", error)
      toast.error(error instanceof Error ? error.message : t.createTemplateError)
    } finally {
      setSubmittingTemplate(false)
    }
  }

  const handleCreateReview = async () => {
    if (!reviewForm.employee_id) {
      toast.error(t.employeeRequired)
      return
    }
    if (!reviewForm.template_id) {
      toast.error(t.templateRequired)
      return
    }
    if (!reviewForm.period_label.trim()) {
      toast.error(t.cycleRequired)
      return
    }

    setSubmittingReview(true)
    try {
      await apiFetch("/api/company/performance/reviews/create/", {
        method: "POST",
        body: JSON.stringify({
          employee_id: Number(reviewForm.employee_id),
          template_id: Number(reviewForm.template_id),
          period_label: reviewForm.period_label.trim(),
        }),
      })

      toast.success(t.createReviewSuccess)
      setCreateReviewOpen(false)
      setReviewForm({
        employee_id: "",
        template_id: "",
        period_label: "",
      })

      await Promise.all([fetchReviews(), fetchDashboard()])
      setActiveTab("reviews")
    } catch (error) {
      console.error("Create review error:", error)
      toast.error(error instanceof Error ? error.message : t.createReviewError)
    } finally {
      setSubmittingReview(false)
    }
  }

  const statCards = [
    {
      title: t.totalTemplates,
      value: formatCount(dashboard?.templates_count ?? 0),
      icon: Layers3,
      hint: t.templatesHint,
    },
    {
      title: t.totalReviews,
      value: formatCount(dashboard?.reviews_count ?? 0),
      icon: ClipboardCheck,
      hint: t.reviewsHint,
    },
    {
      title: t.completedReviews,
      value: formatCount(dashboard?.completed_reviews_count ?? 0),
      icon: BadgeCheck,
      hint: t.completedHint,
    },
    {
      title: t.averageScore,
      value:
        dashboard?.average_final_score != null
          ? formatScore(dashboard.average_final_score)
          : "—",
      icon: TrendingUp,
      hint: t.averageHint,
    },
  ]

  const searchIconClass =
    direction === "rtl"
      ? "pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
      : "pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"

  const searchInputClass = direction === "rtl" ? "rounded-2xl pr-10" : "rounded-2xl pl-10"
  const actionAlignClass = direction === "rtl" ? "text-left" : "text-right"

  return (
    <div dir={direction} className="min-h-screen bg-muted/30">
      <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 p-4 md:p-6">
        <div className="relative overflow-hidden rounded-3xl border border-border/60 bg-background shadow-sm">
          <div className="absolute inset-0 bg-gradient-to-l from-primary/10 via-transparent to-transparent" />
          <div className="relative flex flex-col gap-5 p-6 md:p-8 xl:flex-row xl:items-center xl:justify-between">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/80 px-3 py-1 text-xs font-medium backdrop-blur">
                <Sparkles className="h-3.5 w-3.5" />
                {t.moduleBadge}
              </div>

              <div>
                <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{t.pageTitle}</h1>
                <p className="mt-2 max-w-3xl text-sm text-muted-foreground md:text-base">
                  {t.pageDescription}
                </p>
              </div>
            </div>

            <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row sm:flex-wrap">
              <Button
                variant="outline"
                className="rounded-2xl"
                onClick={() => void loadAll()}
                disabled={refreshing}
              >
                {refreshing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                <span>{t.refresh}</span>
              </Button>

              <Button
                variant="outline"
                className="rounded-2xl"
                onClick={() => setCreateTemplateOpen(true)}
              >
                <FilePlus2 className="h-4 w-4" />
                <span>{t.createTemplate}</span>
              </Button>

              <Button className="rounded-2xl" onClick={() => setCreateReviewOpen(true)}>
                <Plus className="h-4 w-4" />
                <span>{t.createReview}</span>
              </Button>
            </div>
          </div>
        </div>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {statCards.map((card) => {
            const Icon = card.icon
            return (
              <Card key={card.title} className="rounded-3xl border-border/60 shadow-sm">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2">
                      <p className="text-sm text-muted-foreground">{card.title}</p>
                      <div className="text-3xl font-bold tracking-tight">{card.value}</div>
                      <p className="text-xs text-muted-foreground">{card.hint}</p>
                    </div>
                    <div className="rounded-2xl border border-border/60 bg-muted/60 p-3">
                      <Icon className="h-5 w-5" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </section>

        <section className="grid gap-4 xl:grid-cols-4">
          <Card className="rounded-3xl border-border/60 shadow-sm xl:col-span-3">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <BarChart3 className="h-5 w-5" />
                {t.operationalOverview}
              </CardTitle>
              <CardDescription>{t.operationalOverviewDesc}</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingDashboard ? (
                <div className="flex min-h-[140px] items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-2xl border border-border/60 bg-muted/40 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-sm font-medium">{t.selfPending}</span>
                      <Users className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">
                      {formatCount(dashboard?.status_summary.self_pending ?? 0)}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border/60 bg-muted/40 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-sm font-medium">{t.managerPending}</span>
                      <UserCog className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">
                      {formatCount(dashboard?.status_summary.manager_pending ?? 0)}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border/60 bg-muted/40 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-sm font-medium">{t.hrPending}</span>
                      <ShieldCheck className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">
                      {formatCount(dashboard?.status_summary.hr_pending ?? 0)}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border/60 bg-muted/40 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-sm font-medium">{t.completed}</span>
                      <BadgeCheck className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">
                      {formatCount(dashboard?.status_summary.completed ?? 0)}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Activity className="h-5 w-5" />
                {t.quickTips}
              </CardTitle>
              <CardDescription>{t.quickTipsDesc}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="rounded-2xl border border-border/60 bg-muted/40 p-4">
                <div className="mb-1 font-semibold">{t.tip1Title}</div>
                <div className="text-muted-foreground">{t.tip1Desc}</div>
              </div>
              <div className="rounded-2xl border border-border/60 bg-muted/40 p-4">
                <div className="mb-1 font-semibold">{t.tip2Title}</div>
                <div className="text-muted-foreground">{t.tip2Desc}</div>
              </div>
              <div className="rounded-2xl border border-border/60 bg-muted/40 p-4">
                <div className="mb-1 font-semibold">{t.tip3Title}</div>
                <div className="text-muted-foreground">{t.tip3Desc}</div>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <Card className="rounded-3xl border-border/60 shadow-sm">
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-2xl border border-border/60 bg-muted/50 p-3">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">{t.startTemplateTitle}</div>
                  <div className="text-sm text-muted-foreground">{t.startTemplateDesc}</div>
                </div>
              </div>
              <Button
                variant="outline"
                className="w-full rounded-2xl"
                onClick={() => setCreateTemplateOpen(true)}
              >
                <FilePlus2 className="h-4 w-4" />
                <span>{t.createTemplateBtn}</span>
              </Button>
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60 shadow-sm">
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-2xl border border-border/60 bg-muted/50 p-3">
                  <ClipboardCheck className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">{t.startReviewTitle}</div>
                  <div className="text-sm text-muted-foreground">{t.startReviewDesc}</div>
                </div>
              </div>
              <Button className="w-full rounded-2xl" onClick={() => setCreateReviewOpen(true)}>
                <Plus className="h-4 w-4" />
                <span>{t.createReviewBtn}</span>
              </Button>
            </CardContent>
          </Card>

          <Card className="rounded-3xl border-border/60 shadow-sm">
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-2xl border border-border/60 bg-muted/50 p-3">
                  <ArrowRightLeft className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">{t.followWorkflowTitle}</div>
                  <div className="text-sm text-muted-foreground">{t.followWorkflowDesc}</div>
                </div>
              </div>
              <Button
                variant="outline"
                className="w-full rounded-2xl"
                onClick={() => setActiveTab("reviews")}
              >
                <Eye className="h-4 w-4" />
                <span>{t.viewReviews}</span>
              </Button>
            </CardContent>
          </Card>
        </section>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid h-auto w-full grid-cols-1 gap-2 rounded-3xl border border-border/60 bg-background p-2 md:grid-cols-3">
            <TabsTrigger value="overview" className="rounded-2xl">
              {t.tabOverview}
            </TabsTrigger>
            <TabsTrigger value="templates" className="rounded-2xl">
              {t.tabTemplates}
            </TabsTrigger>
            <TabsTrigger value="reviews" className="rounded-2xl">
              {t.tabReviews}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6 space-y-6">
            <Card className="rounded-3xl border-border/60 shadow-sm">
              <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <CardTitle>{t.latestReviews}</CardTitle>
                  <CardDescription>{t.latestReviewsDesc}</CardDescription>
                </div>
                <Button
                  variant="outline"
                  className="rounded-2xl"
                  onClick={() => setActiveTab("reviews")}
                >
                  {t.viewAllReviews}
                </Button>
              </CardHeader>
              <CardContent>
                {loadingReviews ? (
                  <div className="flex min-h-[220px] items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : reviews.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-border/60 p-10 text-center text-sm text-muted-foreground">
                    {t.noReviewsYet}
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-2xl border border-border/60">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t.employee}</TableHead>
                          <TableHead>{t.template}</TableHead>
                          <TableHead>{t.cycle}</TableHead>
                          <TableHead>{t.status}</TableHead>
                          <TableHead>{t.finalScore}</TableHead>
                          <TableHead>{t.createdDate}</TableHead>
                          <TableHead className={actionAlignClass}>{t.action}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {reviews.slice(0, 6).map((review) => (
                          <TableRow key={review.id}>
                            <TableCell>
                              <div className="flex items-center gap-3">
                                <Avatar className="h-10 w-10 rounded-2xl">
                                  <AvatarImage src={review.employee.avatar || ""} />
                                  <AvatarFallback className="rounded-2xl">
                                    {review.employee.name?.slice(0, 2) || "EM"}
                                  </AvatarFallback>
                                </Avatar>
                                <div>
                                  <div className="font-medium">{review.employee.name}</div>
                                  <div className="text-xs text-muted-foreground">
                                    {review.employee.email || t.emailFallback}
                                  </div>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>{review.template.name || "—"}</TableCell>
                            <TableCell>{review.period_label}</TableCell>
                            <TableCell>
                              <Badge variant={getStatusBadgeVariant(review.status)}>
                                {getStatusLabel(review.status, t)}
                              </Badge>
                            </TableCell>
                            <TableCell>{formatScore(review.final_score)}</TableCell>
                            <TableCell>{formatDate(review.created_at)}</TableCell>
                            <TableCell className={actionAlignClass}>
                              <Button
                                size="sm"
                                variant="outline"
                                className="rounded-xl"
                                onClick={() => void openReviewDetails(review.id)}
                              >
                                <Eye className="h-4 w-4" />
                                <span>{t.view}</span>
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
          </TabsContent>

          <TabsContent value="templates" className="mt-6 space-y-6">
            <Card className="rounded-3xl border-border/60 shadow-sm">
              <CardHeader className="gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <CardTitle>{t.templatesTitle}</CardTitle>
                  <CardDescription>{t.templatesDesc}</CardDescription>
                </div>

                <div className="flex w-full flex-col gap-3 md:w-[340px]">
                  <div className="relative">
                    <Search className={searchIconClass} />
                    <Input
                      value={templateSearch}
                      onChange={(e) => setTemplateSearch(e.target.value)}
                      placeholder={t.searchTemplates}
                      className={searchInputClass}
                    />
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                {loadingTemplates ? (
                  <div className="flex min-h-[260px] items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : filteredTemplates.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-border/60 p-10 text-center text-sm text-muted-foreground">
                    {t.noTemplates}
                  </div>
                ) : (
                  <div className="grid gap-4 xl:grid-cols-2">
                    {filteredTemplates.map((template) => (
                      <Card key={template.id} className="rounded-3xl border-border/60 shadow-none">
                        <CardHeader className="space-y-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="space-y-2">
                              <CardTitle className="text-lg">{template.name}</CardTitle>
                              <CardDescription>
                                {template.description || t.noDescription}
                              </CardDescription>
                            </div>
                            <Badge variant={template.is_active ? "default" : "secondary"}>
                              {template.is_active ? t.active : t.inactive}
                            </Badge>
                          </div>

                          <div className="flex flex-wrap gap-2">
                            <Badge variant="outline" className="rounded-xl">
                              <Target className="h-3.5 w-3.5" />
                              <span>{getPeriodLabel(template.period, t)}</span>
                            </Badge>
                            <Badge variant="outline" className="rounded-xl">
                              <Layers3 className="h-3.5 w-3.5" />
                              <span>
                                {formatCount(template.categories_count)} {t.categories}
                              </span>
                            </Badge>
                            <Badge variant="outline" className="rounded-xl">
                              <CircleDot className="h-3.5 w-3.5" />
                              <span>
                                {formatCount(
                                  template.categories.reduce(
                                    (sum, category) => sum + (category.items_count || 0),
                                    0
                                  )
                                )}{" "}
                                {t.items}
                              </span>
                            </Badge>
                          </div>
                        </CardHeader>

                        <CardContent className="space-y-4">
                          <Separator />

                          <div className="space-y-3">
                            {template.categories.slice(0, 3).map((category) => (
                              <div
                                key={category.id}
                                className="rounded-2xl border border-border/60 bg-muted/40 p-4"
                              >
                                <div className="mb-2 flex items-center justify-between gap-3">
                                  <div className="font-medium">{category.name}</div>
                                  <Badge variant="secondary" className="rounded-xl">
                                    {t.weight} {formatCount(category.weight)}
                                  </Badge>
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  {formatCount(category.items_count)} {t.items}
                                </div>
                              </div>
                            ))}

                            {template.categories.length > 3 ? (
                              <div className="text-xs text-muted-foreground">
                                + {formatCount(template.categories.length - 3)} {t.extraCategories}
                              </div>
                            ) : null}
                          </div>

                          <div className="grid grid-cols-1 gap-3 text-xs text-muted-foreground sm:grid-cols-2">
                            <div>
                              {t.createdAt}: {formatDate(template.created_at)}
                            </div>
                            <div>
                              {t.updatedAt}: {formatDate(template.updated_at)}
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-2 pt-1">
                            <Button
                              className="rounded-2xl"
                              onClick={() => openCreateReviewWithTemplate(template)}
                            >
                              <Plus className="h-4 w-4" />
                              <span>{t.createReviewFromTemplate}</span>
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reviews" className="mt-6 space-y-6">
            <Card className="rounded-3xl border-border/60 shadow-sm">
              <CardHeader className="gap-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <CardTitle>{t.reviewsTitle}</CardTitle>
                    <CardDescription>{t.reviewsDesc}</CardDescription>
                  </div>

                  <div className="flex w-full flex-col gap-3 md:flex-row lg:w-auto">
                    <div className="relative min-w-[260px]">
                      <Search className={searchIconClass} />
                      <Input
                        value={reviewSearch}
                        onChange={(e) => setReviewSearch(e.target.value)}
                        placeholder={t.searchReviews}
                        className={searchInputClass}
                      />
                    </div>

                    <Select value={reviewStatusFilter} onValueChange={setReviewStatusFilter}>
                      <SelectTrigger className="min-w-[220px] rounded-2xl">
                        <Filter className="h-4 w-4 text-muted-foreground" />
                        <SelectValue placeholder={t.statusFilter} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ALL">{t.allStatuses}</SelectItem>
                        <SelectItem value="SELF_PENDING">{t.statusSelfPending}</SelectItem>
                        <SelectItem value="MANAGER_PENDING">{t.statusManagerPending}</SelectItem>
                        <SelectItem value="HR_PENDING">{t.statusHrPending}</SelectItem>
                        <SelectItem value="COMPLETED">{t.statusCompleted}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                {loadingReviews ? (
                  <div className="flex min-h-[300px] items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : reviews.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-border/60 p-10 text-center text-sm text-muted-foreground">
                    {t.noMatchingReviews}
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-2xl border border-border/60">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t.employee}</TableHead>
                          <TableHead>{t.template}</TableHead>
                          <TableHead>{t.cycle}</TableHead>
                          <TableHead>{t.status}</TableHead>
                          <TableHead>{t.selfScore}</TableHead>
                          <TableHead>{t.managerScore}</TableHead>
                          <TableHead>{t.hrScore}</TableHead>
                          <TableHead>{t.finalScore}</TableHead>
                          <TableHead>{t.workflowStatus}</TableHead>
                          <TableHead>{t.lastUpdate}</TableHead>
                          <TableHead className={actionAlignClass}>{t.action}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {reviews.map((review) => (
                          <TableRow key={review.id}>
                            <TableCell>
                              <div className="flex items-center gap-3">
                                <Avatar className="h-10 w-10 rounded-2xl">
                                  <AvatarImage src={review.employee.avatar || ""} />
                                  <AvatarFallback className="rounded-2xl">
                                    {review.employee.name?.slice(0, 2) || "EM"}
                                  </AvatarFallback>
                                </Avatar>
                                <div>
                                  <div className="font-medium">{review.employee.name}</div>
                                  <div className="text-xs text-muted-foreground">
                                    {review.employee.email || "—"}
                                  </div>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>{review.template.name || "—"}</TableCell>
                            <TableCell>{review.period_label}</TableCell>
                            <TableCell>
                              <Badge variant={getStatusBadgeVariant(review.status)}>
                                {getStatusLabel(review.status, t)}
                              </Badge>
                            </TableCell>
                            <TableCell>{formatScore(review.self_score)}</TableCell>
                            <TableCell>{formatScore(review.manager_score)}</TableCell>
                            <TableCell>{formatScore(review.hr_score)}</TableCell>
                            <TableCell className="font-semibold">
                              {formatScore(review.final_score)}
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-wrap gap-1.5">
                                <Badge
                                  variant={review.workflow.self_completed ? "default" : "outline"}
                                >
                                  {t.employeeDone}
                                </Badge>
                                <Badge
                                  variant={review.workflow.manager_completed ? "default" : "outline"}
                                >
                                  {t.managerDone}
                                </Badge>
                                <Badge
                                  variant={review.workflow.hr_completed ? "default" : "outline"}
                                >
                                  {t.hrDone}
                                </Badge>
                              </div>
                            </TableCell>
                            <TableCell>{formatDate(review.updated_at)}</TableCell>
                            <TableCell className={actionAlignClass}>
                              <Button
                                size="sm"
                                variant="outline"
                                className="rounded-xl"
                                onClick={() => void openReviewDetails(review.id)}
                              >
                                <Eye className="h-4 w-4" />
                                <span>{t.view}</span>
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
          </TabsContent>
        </Tabs>
      </div>

      <Dialog open={createTemplateOpen} onOpenChange={setCreateTemplateOpen}>
        <DialogContent dir={direction} className="max-h-[92vh] overflow-y-auto sm:max-w-5xl">
          <DialogHeader>
            <DialogTitle>{t.createTemplateDialogTitle}</DialogTitle>
            <DialogDescription>{t.createTemplateDialogDesc}</DialogDescription>
          </DialogHeader>

          <div className="grid gap-5 py-2">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>{t.templateName}</Label>
                <Input
                  value={templateForm.name}
                  onChange={(e) =>
                    setTemplateForm((prev) => ({ ...prev, name: e.target.value }))
                  }
                  placeholder={t.templateNamePlaceholder}
                  className="rounded-2xl"
                />
              </div>

              <div className="space-y-2">
                <Label>{t.period}</Label>
                <Select
                  value={templateForm.period}
                  onValueChange={(value) =>
                    setTemplateForm((prev) => ({ ...prev, period: value }))
                  }
                >
                  <SelectTrigger className="rounded-2xl">
                    <SelectValue placeholder={t.choosePeriod} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="YEARLY">{t.yearly}</SelectItem>
                    <SelectItem value="QUARTERLY">{t.quarterly}</SelectItem>
                    <SelectItem value="MONTHLY">{t.monthly}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>{t.description}</Label>
              <Textarea
                value={templateForm.description}
                onChange={(e) =>
                  setTemplateForm((prev) => ({ ...prev, description: e.target.value }))
                }
                placeholder={t.descriptionPlaceholder}
                className="min-h-[96px] rounded-2xl"
              />
            </div>

            <Separator />

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="font-semibold">{t.sectionsAndItems}</div>
                <div className="text-sm text-muted-foreground">{t.sectionsAndItemsDesc}</div>
              </div>
              <Button variant="outline" className="rounded-2xl" onClick={addCategory}>
                <Plus className="h-4 w-4" />
                <span>{t.addCategory}</span>
              </Button>
            </div>

            <div className="space-y-4">
              {templateForm.categories.map((category, categoryIndex) => (
                <div
                  key={`category-${categoryIndex}`}
                  className="rounded-3xl border border-border/60 bg-muted/30 p-4"
                >
                  <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div className="grid flex-1 gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label>{t.categoryName}</Label>
                        <Input
                          value={category.name}
                          onChange={(e) =>
                            setTemplateForm((prev) => ({
                              ...prev,
                              categories: prev.categories.map((item, idx) =>
                                idx === categoryIndex ? { ...item, name: e.target.value } : item
                              ),
                            }))
                          }
                          placeholder={t.categoryNamePlaceholder}
                          className="rounded-2xl"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>{t.categoryWeight}</Label>
                        <Input
                          type="number"
                          min="0"
                          inputMode="numeric"
                          value={category.weight}
                          onChange={(e) =>
                            setTemplateForm((prev) => ({
                              ...prev,
                              categories: prev.categories.map((item, idx) =>
                                idx === categoryIndex ? { ...item, weight: e.target.value } : item
                              ),
                            }))
                          }
                          className="rounded-2xl"
                          dir="ltr"
                        />
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      className="rounded-2xl text-destructive hover:text-destructive"
                      onClick={() => removeCategory(categoryIndex)}
                    >
                      {t.deleteCategory}
                    </Button>
                  </div>

                  <div className="space-y-3">
                    {category.items.map((item, itemIndex) => (
                      <div
                        key={`item-${categoryIndex}-${itemIndex}`}
                        className="rounded-2xl border border-border/60 bg-background p-4"
                      >
                        <div className="grid gap-4 xl:grid-cols-12">
                          <div className="space-y-2 xl:col-span-5">
                            <Label>{t.questionLabel}</Label>
                            <Input
                              value={item.question}
                              onChange={(e) =>
                                setTemplateForm((prev) => ({
                                  ...prev,
                                  categories: prev.categories.map((cat, catIdx) =>
                                    catIdx === categoryIndex
                                      ? {
                                          ...cat,
                                          items: cat.items.map((row, rowIdx) =>
                                            rowIdx === itemIndex
                                              ? { ...row, question: e.target.value }
                                              : row
                                          ),
                                        }
                                      : cat
                                  ),
                                }))
                              }
                              placeholder={t.questionPlaceholder}
                              className="rounded-2xl"
                            />
                          </div>

                          <div className="space-y-2 xl:col-span-2">
                            <Label>{t.type}</Label>
                            <Select
                              value={item.item_type}
                              onValueChange={(value: "SCORE" | "TEXT") =>
                                setTemplateForm((prev) => ({
                                  ...prev,
                                  categories: prev.categories.map((cat, catIdx) =>
                                    catIdx === categoryIndex
                                      ? {
                                          ...cat,
                                          items: cat.items.map((row, rowIdx) =>
                                            rowIdx === itemIndex
                                              ? { ...row, item_type: value }
                                              : row
                                          ),
                                        }
                                      : cat
                                  ),
                                }))
                              }
                            >
                              <SelectTrigger className="rounded-2xl">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="SCORE">{t.scoreType}</SelectItem>
                                <SelectItem value="TEXT">{t.textType}</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>

                          <div className="space-y-2 xl:col-span-2">
                            <Label>{t.maxScore}</Label>
                            <Input
                              type="number"
                              min="0"
                              inputMode="numeric"
                              value={item.max_score}
                              onChange={(e) =>
                                setTemplateForm((prev) => ({
                                  ...prev,
                                  categories: prev.categories.map((cat, catIdx) =>
                                    catIdx === categoryIndex
                                      ? {
                                          ...cat,
                                          items: cat.items.map((row, rowIdx) =>
                                            rowIdx === itemIndex
                                              ? { ...row, max_score: e.target.value }
                                              : row
                                          ),
                                        }
                                      : cat
                                  ),
                                }))
                              }
                              className="rounded-2xl"
                              dir="ltr"
                            />
                          </div>

                          <div className="space-y-2 xl:col-span-2">
                            <Label>{t.itemWeight}</Label>
                            <Input
                              type="number"
                              min="0"
                              inputMode="numeric"
                              value={item.weight}
                              onChange={(e) =>
                                setTemplateForm((prev) => ({
                                  ...prev,
                                  categories: prev.categories.map((cat, catIdx) =>
                                    catIdx === categoryIndex
                                      ? {
                                          ...cat,
                                          items: cat.items.map((row, rowIdx) =>
                                            rowIdx === itemIndex
                                              ? { ...row, weight: e.target.value }
                                              : row
                                          ),
                                        }
                                      : cat
                                  ),
                                }))
                              }
                              className="rounded-2xl"
                              dir="ltr"
                            />
                          </div>

                          <div className="flex items-end xl:col-span-1">
                            <Button
                              variant="ghost"
                              className="w-full rounded-2xl text-destructive hover:text-destructive"
                              onClick={() => removeItem(categoryIndex, itemIndex)}
                            >
                              {t.delete}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}

                    <Button
                      variant="outline"
                      className="rounded-2xl"
                      onClick={() => addItem(categoryIndex)}
                    >
                      <Plus className="h-4 w-4" />
                      <span>{t.addItem}</span>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              className="rounded-2xl"
              onClick={() => setCreateTemplateOpen(false)}
            >
              {t.close}
            </Button>
            <Button
              className="rounded-2xl"
              onClick={() => void handleCreateTemplate()}
              disabled={submittingTemplate}
            >
              {submittingTemplate ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FilePlus2 className="h-4 w-4" />
              )}
              <span>{t.saveTemplate}</span>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={createReviewOpen} onOpenChange={setCreateReviewOpen}>
        <DialogContent dir={direction} className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{t.createReviewDialogTitle}</DialogTitle>
            <DialogDescription>{t.createReviewDialogDesc}</DialogDescription>
          </DialogHeader>

          <div className="grid gap-5 py-2">
            <div className="space-y-2">
              <Label>{t.employeeLabel}</Label>
              <Select
                value={reviewForm.employee_id}
                onValueChange={(value) =>
                  setReviewForm((prev) => ({ ...prev, employee_id: value }))
                }
                disabled={loadingEmployees}
              >
                <SelectTrigger className="rounded-2xl">
                  <SelectValue placeholder={t.chooseEmployee} />
                </SelectTrigger>
                <SelectContent>
                  {employees.map((employee) => (
                    <SelectItem key={employee.id} value={String(employee.id)}>
                      {employee.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>{t.templateLabel}</Label>
              <Select
                value={reviewForm.template_id}
                onValueChange={(value) => {
                  const selected = templates.find((template) => String(template.id) === value)
                  setReviewForm((prev) => ({
                    ...prev,
                    template_id: value,
                    period_label:
                      prev.period_label || buildSuggestedPeriodLabel(selected?.period),
                  }))
                }}
              >
                <SelectTrigger className="rounded-2xl">
                  <SelectValue placeholder={t.chooseTemplate} />
                </SelectTrigger>
                <SelectContent>
                  {templates.map((template) => (
                    <SelectItem key={template.id} value={String(template.id)}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedTemplateForReview ? (
              <div className="rounded-2xl border border-border/60 bg-muted/40 p-4 text-sm">
                <div className="mb-2 flex items-center gap-2 font-medium">
                  <CheckCircle2 className="h-4 w-4" />
                  {t.selectedTemplate}
                </div>
                <div className="grid gap-2 text-muted-foreground md:grid-cols-3">
                  <div>
                    {t.name}: {selectedTemplateForReview.name}
                  </div>
                  <div>
                    {t.period}: {getPeriodLabel(selectedTemplateForReview.period, t)}
                  </div>
                  <div>
                    {t.categoriesCount}: {formatCount(selectedTemplateForReview.categories_count)}
                  </div>
                </div>
              </div>
            ) : null}

            <div className="space-y-2">
              <Label>{t.periodLabel}</Label>
              <div className="relative">
                <CalendarRange className={searchIconClass} />
                <Input
                  value={reviewForm.period_label}
                  onChange={(e) =>
                    setReviewForm((prev) => ({ ...prev, period_label: e.target.value }))
                  }
                  placeholder={t.periodLabelPlaceholder}
                  className={searchInputClass}
                  dir="ltr"
                />
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              className="rounded-2xl"
              onClick={() => setCreateReviewOpen(false)}
            >
              {t.cancel}
            </Button>
            <Button
              className="rounded-2xl"
              onClick={() => void handleCreateReview()}
              disabled={submittingReview}
            >
              {submittingReview ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              <span>{t.createReview}</span>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={reviewDetailsOpen} onOpenChange={setReviewDetailsOpen}>
        <DialogContent dir={direction} className="max-h-[92vh] overflow-y-auto sm:max-w-6xl">
          <DialogHeader>
            <DialogTitle>{t.reviewDetailsTitle}</DialogTitle>
            <DialogDescription>{t.reviewDetailsDesc}</DialogDescription>
          </DialogHeader>

          {loadingReviewDetails ? (
            <div className="flex min-h-[260px] items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !selectedReview ? (
            <div className="rounded-2xl border border-dashed border-border/60 p-10 text-center text-sm text-muted-foreground">
              {t.noDetails}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid gap-4 xl:grid-cols-4">
                <Card className="rounded-3xl border-border/60 shadow-none xl:col-span-2">
                  <CardContent className="p-5">
                    <div className="flex items-start gap-4">
                      <Avatar className="h-16 w-16 rounded-[20px]">
                        <AvatarImage src={selectedReview.employee.avatar || ""} />
                        <AvatarFallback className="rounded-[20px]">
                          {selectedReview.employee.name?.slice(0, 2) || "EM"}
                        </AvatarFallback>
                      </Avatar>

                      <div className="space-y-2">
                        <div className="text-lg font-semibold">{selectedReview.employee.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {selectedReview.employee.email || "—"}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {selectedReview.employee.phone || "—"}
                        </div>
                        <div className="flex flex-wrap gap-2 pt-1">
                          <Badge variant={getStatusBadgeVariant(selectedReview.status)}>
                            {getStatusLabel(selectedReview.status, t)}
                          </Badge>
                          <Badge variant="outline">
                            {selectedReview.template.name || "—"}
                          </Badge>
                          <Badge variant="outline">{selectedReview.period_label}</Badge>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-3xl border-border/60 shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                      <TrendingUp className="h-4 w-4" />
                      {t.finalScore}
                    </div>
                    <div className="text-3xl font-bold">
                      {formatScore(selectedReview.final_score)}
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      {t.finalDecision}: {selectedReview.final_decision || "—"}
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-3xl border-border/60 shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                      <Briefcase className="h-4 w-4" />
                      {t.workflowState}
                    </div>
                    <div className="space-y-2 text-sm">
                      <div>
                        {t.employeeDone}:{" "}
                        {selectedReview.workflow.self_completed ? t.yes : t.no}
                      </div>
                      <div>
                        {t.managerDone}:{" "}
                        {selectedReview.workflow.manager_completed ? t.yes : t.no}
                      </div>
                      <div>
                        {t.hrDone}: {selectedReview.workflow.hr_completed ? t.yes : t.no}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {t.lastUpdate}: {formatDateTime(selectedReview.workflow.last_update)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <Card className="rounded-3xl border-border/60 shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 text-sm text-muted-foreground">{t.selfScore}</div>
                    <div className="text-2xl font-bold">
                      {formatScore(selectedReview.self_score)}
                    </div>
                  </CardContent>
                </Card>
                <Card className="rounded-3xl border-border/60 shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 text-sm text-muted-foreground">{t.managerScore}</div>
                    <div className="text-2xl font-bold">
                      {formatScore(selectedReview.manager_score)}
                    </div>
                  </CardContent>
                </Card>
                <Card className="rounded-3xl border-border/60 shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 text-sm text-muted-foreground">{t.hrScore}</div>
                    <div className="text-2xl font-bold">
                      {formatScore(selectedReview.hr_score)}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card className="rounded-3xl border-border/60 shadow-none">
                <CardHeader>
                  <CardTitle>{t.answersAndItems}</CardTitle>
                  <CardDescription>{t.answersAndItemsDesc}</CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedReview.answers.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-border/60 p-10 text-center text-sm text-muted-foreground">
                      {t.noAnswers}
                    </div>
                  ) : (
                    <div className="overflow-x-auto rounded-2xl border border-border/60">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>{t.category}</TableHead>
                            <TableHead>{t.question}</TableHead>
                            <TableHead>{t.type}</TableHead>
                            <TableHead>{t.selfScore}</TableHead>
                            <TableHead>{t.managerScore}</TableHead>
                            <TableHead>{t.hrScore}</TableHead>
                            <TableHead>{t.employeeAnswer}</TableHead>
                            <TableHead>{t.managerAnswer}</TableHead>
                            <TableHead>{t.hrAnswer}</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {selectedReview.answers.map((answer) => (
                            <TableRow key={answer.id}>
                              <TableCell>{answer.category_name || "—"}</TableCell>
                              <TableCell className="min-w-[240px]">
                                {answer.question || "—"}
                              </TableCell>
                              <TableCell>{answer.item_type || "—"}</TableCell>
                              <TableCell>{formatScore(answer.self_score)}</TableCell>
                              <TableCell>{formatScore(answer.manager_score)}</TableCell>
                              <TableCell>{formatScore(answer.hr_score)}</TableCell>
                              <TableCell className="max-w-[220px] whitespace-pre-wrap text-sm">
                                {answer.self_answer || "—"}
                              </TableCell>
                              <TableCell className="max-w-[220px] whitespace-pre-wrap text-sm">
                                {answer.manager_answer || "—"}
                              </TableCell>
                              <TableCell className="max-w-[220px] whitespace-pre-wrap text-sm">
                                {answer.hr_answer || "—"}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}