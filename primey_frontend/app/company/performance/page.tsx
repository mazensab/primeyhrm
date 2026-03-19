"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity,
  BarChart3,
  BadgeCheck,
  Briefcase,
  ClipboardCheck,
  Eye,
  FilePlus2,
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
  CalendarRange,
  FileText,
  ArrowRightLeft,
  CircleDot,
  CheckCircle2,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

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

function formatDate(value?: string | null) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString("en-CA")
}

function formatDateTime(value?: string | null) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${date.toLocaleDateString("en-CA")} ${date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  })}`
}

function formatScore(value?: number | null) {
  if (value === null || value === undefined) return "—"
  return Number(value).toFixed(2)
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

function getStatusLabel(status?: string) {
  switch (status) {
    case "SELF_PENDING":
      return "بانتظار الموظف"
    case "MANAGER_PENDING":
      return "بانتظار المدير"
    case "HR_PENDING":
      return "بانتظار الموارد البشرية"
    case "COMPLETED":
      return "مكتمل"
    default:
      return status || "غير معروف"
  }
}

function getPeriodLabel(period?: string) {
  switch (period) {
    case "YEARLY":
      return "سنوي"
    case "QUARTERLY":
      return "ربع سنوي"
    case "MONTHLY":
      return "شهري"
    default:
      return period || "—"
  }
}

function buildSuggestedPeriodLabel(period?: string) {
  const year = new Date().getFullYear()
  switch (period) {
    case "YEARLY":
      return `Annual ${year}`
    case "QUARTERLY":
      return `Q1 ${year}`
    case "MONTHLY":
      return `${year}-${String(new Date().getMonth() + 1).padStart(2, "0")}`
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
    throw new Error(data?.message || "حدث خطأ غير متوقع أثناء الاتصال بالخادم.")
  }

  return data as T
}

export default function CompanyPerformancePage() {
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

  const fetchDashboard = useCallback(async () => {
    setLoadingDashboard(true)
    try {
      const data = await apiFetch<{ status: string; summary: DashboardSummary }>(
        "/api/company/performance/dashboard/"
      )
      setDashboard(data.summary)
    } catch (error) {
      console.error("Dashboard load error:", error)
      toast.error(error instanceof Error ? error.message : "تعذر تحميل ملخص الأداء.")
    } finally {
      setLoadingDashboard(false)
    }
  }, [])

  const fetchTemplates = useCallback(async () => {
    setLoadingTemplates(true)
    try {
      const data = await apiFetch<{ status: string; templates: PerformanceTemplate[] }>(
        "/api/company/performance/templates/"
      )
      setTemplates(data.templates || [])
    } catch (error) {
      console.error("Templates load error:", error)
      toast.error(error instanceof Error ? error.message : "تعذر تحميل القوالب.")
    } finally {
      setLoadingTemplates(false)
    }
  }, [])

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
      toast.error(error instanceof Error ? error.message : "تعذر تحميل التقييمات.")
    } finally {
      setLoadingReviews(false)
    }
  }, [reviewSearch, reviewStatusFilter])

  const fetchEmployees = useCallback(async () => {
    setLoadingEmployees(true)
    try {
      const data = await apiFetch<{ status: string; employees: EmployeeLookup[] }>(
        "/api/company/performance/employees/lookup/"
      )
      setEmployees(data.employees || [])
    } catch (error) {
      console.error("Employees load error:", error)
      toast.error(error instanceof Error ? error.message : "تعذر تحميل الموظفين.")
    } finally {
      setLoadingEmployees(false)
    }
  }, [])

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
      const haystack = [
        template.name,
        template.description || "",
        template.period,
      ]
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
      toast.error(error instanceof Error ? error.message : "تعذر تحميل تفاصيل التقييم.")
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
      toast.error("يرجى إدخال اسم القالب.")
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
      toast.error("أضف فئة واحدة على الأقل داخل القالب.")
      return
    }

    if (validCategories.some((category) => category.items.length === 0)) {
      toast.error("كل فئة يجب أن تحتوي على عنصر واحد على الأقل.")
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

      toast.success("تم إنشاء قالب التقييم بنجاح.")
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
      toast.error(error instanceof Error ? error.message : "تعذر إنشاء قالب التقييم.")
    } finally {
      setSubmittingTemplate(false)
    }
  }

  const handleCreateReview = async () => {
    if (!reviewForm.employee_id) {
      toast.error("يرجى اختيار الموظف.")
      return
    }
    if (!reviewForm.template_id) {
      toast.error("يرجى اختيار القالب.")
      return
    }
    if (!reviewForm.period_label.trim()) {
      toast.error("يرجى إدخال الدورة التقييمية.")
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

      toast.success("تم إنشاء التقييم بنجاح.")
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
      toast.error(error instanceof Error ? error.message : "تعذر إنشاء التقييم.")
    } finally {
      setSubmittingReview(false)
    }
  }

  const statCards = [
    {
      title: "إجمالي القوالب",
      value: dashboard?.templates_count ?? 0,
      icon: Layers3,
      hint: "قوالب التقييم الجاهزة",
    },
    {
      title: "إجمالي التقييمات",
      value: dashboard?.reviews_count ?? 0,
      icon: ClipboardCheck,
      hint: "كل التقييمات المسجلة",
    },
    {
      title: "المكتملة",
      value: dashboard?.completed_reviews_count ?? 0,
      icon: BadgeCheck,
      hint: "تمت معالجتها بالكامل",
    },
    {
      title: "متوسط النتيجة",
      value:
        dashboard?.average_final_score != null
          ? formatScore(dashboard.average_final_score)
          : "—",
      icon: TrendingUp,
      hint: "متوسط الدرجة النهائية",
    },
  ]

  return (
    <div className="min-h-screen bg-muted/30">
      <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 p-4 md:p-6">
        <div className="relative overflow-hidden rounded-[28px] border bg-background shadow-sm">
          <div className="absolute inset-0 bg-gradient-to-l from-primary/10 via-transparent to-transparent" />
          <div className="relative flex flex-col gap-4 p-6 md:flex-row md:items-center md:justify-between md:p-8">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border bg-background/80 px-3 py-1 text-xs font-medium backdrop-blur">
                <Sparkles className="h-3.5 w-3.5" />
                Performance Center
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
                  إدارة الأداء والتقييم
                </h1>
                <p className="mt-2 max-w-3xl text-sm text-muted-foreground md:text-base">
                  صفحة تشغيل احترافية لإدارة قوالب التقييم، إنشاء دورات الأداء،
                  ومتابعة سير التقييم بين الموظف والمدير والموارد البشرية.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button
                variant="outline"
                className="rounded-2xl"
                onClick={() => void loadAll()}
                disabled={refreshing}
              >
                {refreshing ? (
                  <Loader2 className="ms-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="ms-2 h-4 w-4" />
                )}
                تحديث
              </Button>

              <Button
                variant="outline"
                className="rounded-2xl"
                onClick={() => setCreateTemplateOpen(true)}
              >
                <FilePlus2 className="ms-2 h-4 w-4" />
                قالب جديد
              </Button>

              <Button
                className="rounded-2xl"
                onClick={() => setCreateReviewOpen(true)}
              >
                <Plus className="ms-2 h-4 w-4" />
                إنشاء تقييم
              </Button>
            </div>
          </div>
        </div>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {statCards.map((card) => {
            const Icon = card.icon
            return (
              <Card key={card.title} className="rounded-[24px] border shadow-sm">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2">
                      <p className="text-sm text-muted-foreground">{card.title}</p>
                      <div className="text-3xl font-bold tracking-tight">{card.value}</div>
                      <p className="text-xs text-muted-foreground">{card.hint}</p>
                    </div>
                    <div className="rounded-2xl border bg-muted/60 p-3">
                      <Icon className="h-5 w-5" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </section>

        <section className="grid gap-4 xl:grid-cols-4">
          <Card className="rounded-[24px] border shadow-sm xl:col-span-3">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2 text-lg">
                <BarChart3 className="h-5 w-5" />
                نظرة تشغيلية
              </CardTitle>
              <CardDescription>
                توزيع الحالات الحالية داخل دورة تقييم الأداء.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingDashboard ? (
                <div className="flex min-h-[140px] items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-2xl border bg-muted/40 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-sm font-medium">بانتظار الموظف</span>
                      <Users className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">
                      {dashboard?.status_summary.self_pending ?? 0}
                    </div>
                  </div>

                  <div className="rounded-2xl border bg-muted/40 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-sm font-medium">بانتظار المدير</span>
                      <UserCog className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">
                      {dashboard?.status_summary.manager_pending ?? 0}
                    </div>
                  </div>

                  <div className="rounded-2xl border bg-muted/40 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-sm font-medium">بانتظار HR</span>
                      <ShieldCheck className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">
                      {dashboard?.status_summary.hr_pending ?? 0}
                    </div>
                  </div>

                  <div className="rounded-2xl border bg-muted/40 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-sm font-medium">مكتمل</span>
                      <BadgeCheck className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-2xl font-bold">
                      {dashboard?.status_summary.completed ?? 0}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="rounded-[24px] border shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Activity className="h-5 w-5" />
                تلميحات سريعة
              </CardTitle>
              <CardDescription>
                تسلسل العمل الموصى به داخل الموديول.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="rounded-2xl border bg-muted/40 p-4">
                <div className="mb-1 font-semibold">1) أنشئ القالب</div>
                <div className="text-muted-foreground">
                  حدد الفئات وعناصر القياس والأوزان.
                </div>
              </div>
              <div className="rounded-2xl border bg-muted/40 p-4">
                <div className="mb-1 font-semibold">2) أنشئ التقييم</div>
                <div className="text-muted-foreground">
                  اربط الموظف بالقالب والدورة التقييمية.
                </div>
              </div>
              <div className="rounded-2xl border bg-muted/40 p-4">
                <div className="mb-1 font-semibold">3) تابع الـ Workflow</div>
                <div className="text-muted-foreground">
                  الموظف ← المدير ← HR حتى الاكتمال النهائي.
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <Card className="rounded-[24px] border shadow-sm">
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-2xl border bg-muted/50 p-3">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">ابدأ بقالب جديد</div>
                  <div className="text-sm text-muted-foreground">
                    أنشئ هيكل التقييم أولًا.
                  </div>
                </div>
              </div>
              <Button
                variant="outline"
                className="w-full rounded-2xl"
                onClick={() => setCreateTemplateOpen(true)}
              >
                <FilePlus2 className="ms-2 h-4 w-4" />
                إنشاء قالب
              </Button>
            </CardContent>
          </Card>

          <Card className="rounded-[24px] border shadow-sm">
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-2xl border bg-muted/50 p-3">
                  <ClipboardCheck className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">أنشئ دورة تقييم</div>
                  <div className="text-sm text-muted-foreground">
                    اربط موظفًا بقالب تقييم.
                  </div>
                </div>
              </div>
              <Button
                className="w-full rounded-2xl"
                onClick={() => setCreateReviewOpen(true)}
              >
                <Plus className="ms-2 h-4 w-4" />
                إنشاء تقييم
              </Button>
            </CardContent>
          </Card>

          <Card className="rounded-[24px] border shadow-sm">
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-2xl border bg-muted/50 p-3">
                  <ArrowRightLeft className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold">تابع الدورة الحالية</div>
                  <div className="text-sm text-muted-foreground">
                    راقب سير الموظف → المدير → HR.
                  </div>
                </div>
              </div>
              <Button
                variant="outline"
                className="w-full rounded-2xl"
                onClick={() => setActiveTab("reviews")}
              >
                <Eye className="ms-2 h-4 w-4" />
                عرض التقييمات
              </Button>
            </CardContent>
          </Card>
        </section>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid h-auto w-full grid-cols-1 gap-2 rounded-[20px] border bg-background p-2 md:grid-cols-3">
            <TabsTrigger value="overview" className="rounded-2xl">
              النظرة العامة
            </TabsTrigger>
            <TabsTrigger value="templates" className="rounded-2xl">
              القوالب
            </TabsTrigger>
            <TabsTrigger value="reviews" className="rounded-2xl">
              التقييمات
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6 space-y-6">
            <Card className="rounded-[24px] border shadow-sm">
              <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <CardTitle>أحدث التقييمات</CardTitle>
                  <CardDescription>
                    آخر عناصر الأداء التي تم إنشاؤها أو تحديثها.
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  className="rounded-2xl"
                  onClick={() => setActiveTab("reviews")}
                >
                  عرض كل التقييمات
                </Button>
              </CardHeader>
              <CardContent>
                {loadingReviews ? (
                  <div className="flex min-h-[220px] items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : reviews.length === 0 ? (
                  <div className="rounded-2xl border border-dashed p-10 text-center text-sm text-muted-foreground">
                    لا توجد تقييمات بعد. ابدأ بإنشاء قالب ثم أضف تقييمًا جديدًا.
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-2xl border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>الموظف</TableHead>
                          <TableHead>القالب</TableHead>
                          <TableHead>الدورة</TableHead>
                          <TableHead>الحالة</TableHead>
                          <TableHead>الدرجة النهائية</TableHead>
                          <TableHead>تاريخ الإنشاء</TableHead>
                          <TableHead className="text-left">الإجراء</TableHead>
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
                                    {review.employee.email || "—"}
                                  </div>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>{review.template.name || "—"}</TableCell>
                            <TableCell>{review.period_label}</TableCell>
                            <TableCell>
                              <Badge variant={getStatusBadgeVariant(review.status)}>
                                {getStatusLabel(review.status)}
                              </Badge>
                            </TableCell>
                            <TableCell>{formatScore(review.final_score)}</TableCell>
                            <TableCell>{formatDate(review.created_at)}</TableCell>
                            <TableCell className="text-left">
                              <Button
                                size="sm"
                                variant="outline"
                                className="rounded-xl"
                                onClick={() => void openReviewDetails(review.id)}
                              >
                                <Eye className="ms-2 h-4 w-4" />
                                عرض
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
            <Card className="rounded-[24px] border shadow-sm">
              <CardHeader className="gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <CardTitle>قوالب التقييم</CardTitle>
                  <CardDescription>
                    إدارة القوالب والفئات وعناصر القياس داخل الشركة.
                  </CardDescription>
                </div>

                <div className="flex flex-col gap-3 md:w-[340px]">
                  <div className="relative">
                    <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      value={templateSearch}
                      onChange={(e) => setTemplateSearch(e.target.value)}
                      placeholder="بحث في القوالب..."
                      className="rounded-2xl pr-10"
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
                  <div className="rounded-2xl border border-dashed p-10 text-center text-sm text-muted-foreground">
                    لا توجد قوالب مطابقة حاليًا.
                  </div>
                ) : (
                  <div className="grid gap-4 xl:grid-cols-2">
                    {filteredTemplates.map((template) => (
                      <Card key={template.id} className="rounded-[24px] border shadow-none">
                        <CardHeader className="space-y-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="space-y-2">
                              <CardTitle className="text-lg">{template.name}</CardTitle>
                              <CardDescription>
                                {template.description || "بدون وصف"}
                              </CardDescription>
                            </div>
                            <Badge variant={template.is_active ? "default" : "secondary"}>
                              {template.is_active ? "نشط" : "غير نشط"}
                            </Badge>
                          </div>

                          <div className="flex flex-wrap gap-2">
                            <Badge variant="outline" className="rounded-xl">
                              <Target className="ms-1.5 h-3.5 w-3.5" />
                              {getPeriodLabel(template.period)}
                            </Badge>
                            <Badge variant="outline" className="rounded-xl">
                              <Layers3 className="ms-1.5 h-3.5 w-3.5" />
                              {template.categories_count} فئات
                            </Badge>
                            <Badge variant="outline" className="rounded-xl">
                              <CircleDot className="ms-1.5 h-3.5 w-3.5" />
                              {template.categories.reduce(
                                (sum, category) => sum + (category.items_count || 0),
                                0
                              )}{" "}
                              عناصر
                            </Badge>
                          </div>
                        </CardHeader>

                        <CardContent className="space-y-4">
                          <Separator />

                          <div className="space-y-3">
                            {template.categories.slice(0, 3).map((category) => (
                              <div
                                key={category.id}
                                className="rounded-2xl border bg-muted/40 p-4"
                              >
                                <div className="mb-2 flex items-center justify-between gap-3">
                                  <div className="font-medium">{category.name}</div>
                                  <Badge variant="secondary" className="rounded-xl">
                                    وزن {category.weight}
                                  </Badge>
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  {category.items_count} عنصر
                                </div>
                              </div>
                            ))}

                            {template.categories.length > 3 ? (
                              <div className="text-xs text-muted-foreground">
                                + {template.categories.length - 3} فئات إضافية
                              </div>
                            ) : null}
                          </div>

                          <div className="grid grid-cols-2 gap-3 text-xs text-muted-foreground">
                            <div>الإنشاء: {formatDate(template.created_at)}</div>
                            <div>التحديث: {formatDate(template.updated_at)}</div>
                          </div>

                          <div className="flex flex-wrap gap-2 pt-1">
                            <Button
                              className="rounded-2xl"
                              onClick={() => openCreateReviewWithTemplate(template)}
                            >
                              <Plus className="ms-2 h-4 w-4" />
                              إنشاء تقييم من هذا القالب
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
            <Card className="rounded-[24px] border shadow-sm">
              <CardHeader className="gap-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <CardTitle>التقييمات</CardTitle>
                    <CardDescription>
                      متابعة التقييمات، حالتها، ونتائجها النهائية.
                    </CardDescription>
                  </div>

                  <div className="flex flex-col gap-3 md:flex-row">
                    <div className="relative min-w-[260px]">
                      <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        value={reviewSearch}
                        onChange={(e) => setReviewSearch(e.target.value)}
                        placeholder="بحث باسم الموظف أو القالب أو الدورة..."
                        className="rounded-2xl pr-10"
                      />
                    </div>

                    <Select
                      value={reviewStatusFilter}
                      onValueChange={setReviewStatusFilter}
                    >
                      <SelectTrigger className="min-w-[220px] rounded-2xl">
                        <Filter className="ms-2 h-4 w-4 text-muted-foreground" />
                        <SelectValue placeholder="تصفية الحالة" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ALL">كل الحالات</SelectItem>
                        <SelectItem value="SELF_PENDING">بانتظار الموظف</SelectItem>
                        <SelectItem value="MANAGER_PENDING">بانتظار المدير</SelectItem>
                        <SelectItem value="HR_PENDING">بانتظار HR</SelectItem>
                        <SelectItem value="COMPLETED">مكتمل</SelectItem>
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
                  <div className="rounded-2xl border border-dashed p-10 text-center text-sm text-muted-foreground">
                    لا توجد تقييمات مطابقة حاليًا.
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-2xl border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>الموظف</TableHead>
                          <TableHead>القالب</TableHead>
                          <TableHead>الدورة</TableHead>
                          <TableHead>الحالة</TableHead>
                          <TableHead>الدرجة الذاتية</TableHead>
                          <TableHead>درجة المدير</TableHead>
                          <TableHead>درجة HR</TableHead>
                          <TableHead>النهائية</TableHead>
                          <TableHead>حالة الـ Workflow</TableHead>
                          <TableHead>آخر تحديث</TableHead>
                          <TableHead className="text-left">الإجراء</TableHead>
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
                                {getStatusLabel(review.status)}
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
                                <Badge variant={review.workflow.self_completed ? "default" : "outline"}>
                                  موظف
                                </Badge>
                                <Badge variant={review.workflow.manager_completed ? "default" : "outline"}>
                                  مدير
                                </Badge>
                                <Badge variant={review.workflow.hr_completed ? "default" : "outline"}>
                                  HR
                                </Badge>
                              </div>
                            </TableCell>
                            <TableCell>{formatDate(review.updated_at)}</TableCell>
                            <TableCell className="text-left">
                              <Button
                                size="sm"
                                variant="outline"
                                className="rounded-xl"
                                onClick={() => void openReviewDetails(review.id)}
                              >
                                <Eye className="ms-2 h-4 w-4" />
                                عرض
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
        <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-5xl">
          <DialogHeader>
            <DialogTitle>إنشاء قالب تقييم جديد</DialogTitle>
            <DialogDescription>
              أنشئ القالب مع الفئات والعناصر ليتم استخدامه لاحقًا في دورات الأداء.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-5 py-2">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>اسم القالب</Label>
                <Input
                  value={templateForm.name}
                  onChange={(e) =>
                    setTemplateForm((prev) => ({ ...prev, name: e.target.value }))
                  }
                  placeholder="مثال: التقييم السنوي للإدارة"
                  className="rounded-2xl"
                />
              </div>

              <div className="space-y-2">
                <Label>الفترة</Label>
                <Select
                  value={templateForm.period}
                  onValueChange={(value) =>
                    setTemplateForm((prev) => ({ ...prev, period: value }))
                  }
                >
                  <SelectTrigger className="rounded-2xl">
                    <SelectValue placeholder="اختر الفترة" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="YEARLY">سنوي</SelectItem>
                    <SelectItem value="QUARTERLY">ربع سنوي</SelectItem>
                    <SelectItem value="MONTHLY">شهري</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>الوصف</Label>
              <Textarea
                value={templateForm.description}
                onChange={(e) =>
                  setTemplateForm((prev) => ({ ...prev, description: e.target.value }))
                }
                placeholder="وصف مختصر عن استخدام القالب..."
                className="min-h-[96px] rounded-2xl"
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold">الفئات والعناصر</div>
                <div className="text-sm text-muted-foreground">
                  أنشئ هيكل التقييم بالكامل قبل الحفظ.
                </div>
              </div>
              <Button variant="outline" className="rounded-2xl" onClick={addCategory}>
                <Plus className="ms-2 h-4 w-4" />
                إضافة فئة
              </Button>
            </div>

            <div className="space-y-4">
              {templateForm.categories.map((category, categoryIndex) => (
                <div
                  key={`category-${categoryIndex}`}
                  className="rounded-[24px] border bg-muted/30 p-4"
                >
                  <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div className="grid flex-1 gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label>اسم الفئة</Label>
                        <Input
                          value={category.name}
                          onChange={(e) =>
                            setTemplateForm((prev) => ({
                              ...prev,
                              categories: prev.categories.map((item, idx) =>
                                idx === categoryIndex
                                  ? { ...item, name: e.target.value }
                                  : item
                              ),
                            }))
                          }
                          placeholder="مثال: الأداء الوظيفي"
                          className="rounded-2xl"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label>وزن الفئة</Label>
                        <Input
                          type="number"
                          min="0"
                          value={category.weight}
                          onChange={(e) =>
                            setTemplateForm((prev) => ({
                              ...prev,
                              categories: prev.categories.map((item, idx) =>
                                idx === categoryIndex
                                  ? { ...item, weight: e.target.value }
                                  : item
                              ),
                            }))
                          }
                          className="rounded-2xl"
                        />
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      className="rounded-2xl text-destructive hover:text-destructive"
                      onClick={() => removeCategory(categoryIndex)}
                    >
                      حذف الفئة
                    </Button>
                  </div>

                  <div className="space-y-3">
                    {category.items.map((item, itemIndex) => (
                      <div
                        key={`item-${categoryIndex}-${itemIndex}`}
                        className="rounded-2xl border bg-background p-4"
                      >
                        <div className="grid gap-4 xl:grid-cols-12">
                          <div className="space-y-2 xl:col-span-5">
                            <Label>السؤال / العنصر</Label>
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
                              placeholder="أدخل السؤال أو عنصر التقييم"
                              className="rounded-2xl"
                            />
                          </div>

                          <div className="space-y-2 xl:col-span-2">
                            <Label>النوع</Label>
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
                                <SelectItem value="SCORE">درجة</SelectItem>
                                <SelectItem value="TEXT">نصي</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>

                          <div className="space-y-2 xl:col-span-2">
                            <Label>أقصى درجة</Label>
                            <Input
                              type="number"
                              min="0"
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
                            />
                          </div>

                          <div className="space-y-2 xl:col-span-2">
                            <Label>الوزن</Label>
                            <Input
                              type="number"
                              min="0"
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
                            />
                          </div>

                          <div className="flex items-end xl:col-span-1">
                            <Button
                              variant="ghost"
                              className="w-full rounded-2xl text-destructive hover:text-destructive"
                              onClick={() => removeItem(categoryIndex, itemIndex)}
                            >
                              حذف
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
                      <Plus className="ms-2 h-4 w-4" />
                      إضافة عنصر
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
              إغلاق
            </Button>
            <Button
              className="rounded-2xl"
              onClick={() => void handleCreateTemplate()}
              disabled={submittingTemplate}
            >
              {submittingTemplate ? (
                <Loader2 className="ms-2 h-4 w-4 animate-spin" />
              ) : (
                <FilePlus2 className="ms-2 h-4 w-4" />
              )}
              حفظ القالب
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={createReviewOpen} onOpenChange={setCreateReviewOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>إنشاء تقييم جديد</DialogTitle>
            <DialogDescription>
              اختر الموظف والقالب وأدخل اسم الدورة التقييمية.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-5 py-2">
            <div className="space-y-2">
              <Label>الموظف</Label>
              <Select
                value={reviewForm.employee_id}
                onValueChange={(value) =>
                  setReviewForm((prev) => ({ ...prev, employee_id: value }))
                }
                disabled={loadingEmployees}
              >
                <SelectTrigger className="rounded-2xl">
                  <SelectValue placeholder="اختر الموظف" />
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
              <Label>القالب</Label>
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
                  <SelectValue placeholder="اختر القالب" />
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
              <div className="rounded-2xl border bg-muted/40 p-4 text-sm">
                <div className="mb-2 flex items-center gap-2 font-medium">
                  <CheckCircle2 className="h-4 w-4" />
                  القالب المختار
                </div>
                <div className="grid gap-2 text-muted-foreground md:grid-cols-3">
                  <div>الاسم: {selectedTemplateForReview.name}</div>
                  <div>الفترة: {getPeriodLabel(selectedTemplateForReview.period)}</div>
                  <div>الفئات: {selectedTemplateForReview.categories_count}</div>
                </div>
              </div>
            ) : null}

            <div className="space-y-2">
              <Label>الدورة التقييمية</Label>
              <div className="relative">
                <CalendarRange className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={reviewForm.period_label}
                  onChange={(e) =>
                    setReviewForm((prev) => ({ ...prev, period_label: e.target.value }))
                  }
                  placeholder="مثال: Q1 2026 أو Annual 2026"
                  className="rounded-2xl pr-10"
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
              إلغاء
            </Button>
            <Button
              className="rounded-2xl"
              onClick={() => void handleCreateReview()}
              disabled={submittingReview}
            >
              {submittingReview ? (
                <Loader2 className="ms-2 h-4 w-4 animate-spin" />
              ) : (
                <Plus className="ms-2 h-4 w-4" />
              )}
              إنشاء التقييم
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={reviewDetailsOpen} onOpenChange={setReviewDetailsOpen}>
        <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-6xl">
          <DialogHeader>
            <DialogTitle>تفاصيل التقييم</DialogTitle>
            <DialogDescription>
              عرض شامل لسير التقييم والإجابات والدرجات.
            </DialogDescription>
          </DialogHeader>

          {loadingReviewDetails ? (
            <div className="flex min-h-[260px] items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : !selectedReview ? (
            <div className="rounded-2xl border border-dashed p-10 text-center text-sm text-muted-foreground">
              لا توجد بيانات لعرضها.
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid gap-4 xl:grid-cols-4">
                <Card className="rounded-[24px] border shadow-none xl:col-span-2">
                  <CardContent className="p-5">
                    <div className="flex items-start gap-4">
                      <Avatar className="h-16 w-16 rounded-[20px]">
                        <AvatarImage src={selectedReview.employee.avatar || ""} />
                        <AvatarFallback className="rounded-[20px]">
                          {selectedReview.employee.name?.slice(0, 2) || "EM"}
                        </AvatarFallback>
                      </Avatar>

                      <div className="space-y-2">
                        <div className="text-lg font-semibold">
                          {selectedReview.employee.name}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {selectedReview.employee.email || "—"}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {selectedReview.employee.phone || "—"}
                        </div>
                        <div className="flex flex-wrap gap-2 pt-1">
                          <Badge variant={getStatusBadgeVariant(selectedReview.status)}>
                            {getStatusLabel(selectedReview.status)}
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

                <Card className="rounded-[24px] border shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                      <TrendingUp className="h-4 w-4" />
                      الدرجة النهائية
                    </div>
                    <div className="text-3xl font-bold">
                      {formatScore(selectedReview.final_score)}
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      القرار: {selectedReview.final_decision || "—"}
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-[24px] border shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                      <Briefcase className="h-4 w-4" />
                      حالة الـ Workflow
                    </div>
                    <div className="space-y-2 text-sm">
                      <div>الموظف: {selectedReview.workflow.self_completed ? "مكتمل" : "لا"}</div>
                      <div>المدير: {selectedReview.workflow.manager_completed ? "مكتمل" : "لا"}</div>
                      <div>HR: {selectedReview.workflow.hr_completed ? "مكتمل" : "لا"}</div>
                      <div className="text-xs text-muted-foreground">
                        آخر تحديث: {formatDateTime(selectedReview.workflow.last_update)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <Card className="rounded-[24px] border shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 text-sm text-muted-foreground">درجة الموظف</div>
                    <div className="text-2xl font-bold">
                      {formatScore(selectedReview.self_score)}
                    </div>
                  </CardContent>
                </Card>
                <Card className="rounded-[24px] border shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 text-sm text-muted-foreground">درجة المدير</div>
                    <div className="text-2xl font-bold">
                      {formatScore(selectedReview.manager_score)}
                    </div>
                  </CardContent>
                </Card>
                <Card className="rounded-[24px] border shadow-none">
                  <CardContent className="p-5">
                    <div className="mb-2 text-sm text-muted-foreground">درجة HR</div>
                    <div className="text-2xl font-bold">
                      {formatScore(selectedReview.hr_score)}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card className="rounded-[24px] border shadow-none">
                <CardHeader>
                  <CardTitle>العناصر والإجابات</CardTitle>
                  <CardDescription>
                    تفاصيل كل عنصر داخل القالب مع إجابات الأطراف المختلفة.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedReview.answers.length === 0 ? (
                    <div className="rounded-2xl border border-dashed p-10 text-center text-sm text-muted-foreground">
                      لا توجد إجابات بعد.
                    </div>
                  ) : (
                    <div className="overflow-x-auto rounded-2xl border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>الفئة</TableHead>
                            <TableHead>السؤال</TableHead>
                            <TableHead>النوع</TableHead>
                            <TableHead>درجة الموظف</TableHead>
                            <TableHead>درجة المدير</TableHead>
                            <TableHead>درجة HR</TableHead>
                            <TableHead>إجابة الموظف</TableHead>
                            <TableHead>إجابة المدير</TableHead>
                            <TableHead>إجابة HR</TableHead>
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