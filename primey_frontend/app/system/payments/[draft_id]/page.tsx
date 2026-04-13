"use client"

import Image from "next/image"
import { useEffect, useMemo, useState } from "react"
import { useParams, useRouter } from "next/navigation"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

import { toast } from "sonner"

import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  Landmark,
  Loader2,
  ShieldCheck,
  User2,
  FileText,
  ReceiptText,
  MapPin,
  Wallet,
  CreditCard,
} from "lucide-react"

/* =========================================================
   🌐 API Helpers
========================================================= */
function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "")
}

function resolveApiBase() {
  const envApi = process.env.NEXT_PUBLIC_API_URL?.trim()

  if (envApi) {
    return trimTrailingSlash(envApi)
  }

  if (typeof window !== "undefined") {
    return trimTrailingSlash(window.location.origin)
  }

  return ""
}

type DraftStatus = "DRAFT" | "CONFIRMED" | "PAID" | string
type PaymentMethod =
  | "BANK_TRANSFER"
  | "CREDIT_CARD"
  | "TAMARA"
  | null

type DraftDetailResponse = {
  draft_id: number
  status: DraftStatus
  company_name?: string
  duration?: string
  payment_method?: PaymentMethod
  is_public_flow?: boolean

  plan?: {
    id?: number | null
    name?: string | null
  }

  pricing?: {
    base_price?: number
    discount_amount?: number
    vat?: number
    total?: number
  }

  dates?: {
    start_date?: string | null
    end_date?: string | null
  }

  admin?: {
    username?: string | null
    name?: string | null
    email?: string | null
  }

  company?: {
    commercial_number?: string | null
    tax_number?: string | null
    phone?: string | null
    email?: string | null
    city?: string | null
    national_address?: {
      building_no?: string | null
      street?: string | null
      district?: string | null
      postal_code?: string | null
      short_address?: string | null
    }
  }

  error?: string
}

type ConfirmPaymentResponse = {
  company_id?: number
  company_name?: string
  admin_username?: string
  payment_method?: string
  gateway_status?: string
  gateway_transaction_id?: string | null
  invoice_id?: number
  error?: string
  details?: string
  message?: string
  status?: string
}

/* =========================================================
   🛡️ CSRF Helper
========================================================= */
function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null
  }

  return null
}

async function ensureCsrf(apiBase: string) {
  if (!apiBase) return null

  try {
    await fetch(`${apiBase}/api/auth/csrf/`, {
      credentials: "include",
    })
  } catch {
    return null
  }

  return getCookie("csrftoken")
}

/* =========================================================
   🧩 Helpers
========================================================= */
function normalizeNumber(value: unknown): number {
  if (typeof value === "number" && !Number.isNaN(value)) return value

  const parsed = Number(value ?? 0)
  return Number.isNaN(parsed) ? 0 : parsed
}

function formatMoney(value: unknown, currency = "SAR") {
  const amount = normalizeNumber(value)

  return `${new Intl.NumberFormat("ar-SA", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)} ${currency}`
}

function formatDate(value?: string | null) {
  if (!value) return "-"

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return "-"

  return parsed.toLocaleDateString("ar-SA")
}

function getStatusBadgeVariant(status: DraftStatus) {
  if (status === "PAID") return "default"
  if (status === "CONFIRMED") return "secondary"
  if (status === "DRAFT") return "outline"
  return "destructive"
}

function getStatusLabel(status: DraftStatus) {
  switch (status) {
    case "DRAFT":
      return "مسودة"
    case "CONFIRMED":
      return "مؤكد"
    case "PAID":
      return "مدفوع"
    default:
      return status || "-"
  }
}

function getMethodLabel(method?: PaymentMethod) {
  switch (method) {
    case "BANK_TRANSFER":
      return "تحويل بنكي"
    case "CREDIT_CARD":
      return "بطاقة ائتمانية (Tap)"
    case "TAMARA":
      return "Tamara"
    default:
      return "-"
  }
}

function getMethodDescription(method?: PaymentMethod) {
  switch (method) {
    case "BANK_TRANSFER":
      return "هذا الطلب يعتمد يدويًا من خلال الإدارة المالية بعد التحقق من التحويل البنكي."
    case "CREDIT_CARD":
      return "هذا الطلب مسجل كدفع إلكتروني بالبطاقة عبر بوابة Tap."
    case "TAMARA":
      return "هذا الطلب مسجل كدفع إلكتروني عبر Tamara."
    default:
      return "طريقة الدفع غير محددة لهذا الطلب."
  }
}

function getDurationLabel(duration?: string) {
  if (duration === "monthly") return "شهري"
  if (duration === "yearly") return "سنوي"
  return duration || "-"
}

function getMethodIcon(method?: PaymentMethod) {
  switch (method) {
    case "BANK_TRANSFER":
      return Landmark
    case "CREDIT_CARD":
      return CreditCard
    case "TAMARA":
      return Wallet
    default:
      return ShieldCheck
  }
}

/* =========================================================
   📄 Page
========================================================= */
export default function PaymentPage() {
  const API = useMemo(() => resolveApiBase(), [])
  const params = useParams()
  const router = useRouter()

  const draftId = Array.isArray(params.draft_id)
    ? params.draft_id[0]
    : params.draft_id

  const [draft, setDraft] = useState<DraftDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    if (!draftId) {
      setLoading(false)
      setDraft(null)
      return
    }

    if (!API) {
      setLoading(false)
      setDraft(null)
      return
    }

    async function loadDraft() {
      try {
        setLoading(true)

        const res = await fetch(
          `${API}/api/system/onboarding/draft/${draftId}/`,
          {
            credentials: "include",
            cache: "no-store",
          }
        )

        const data: DraftDetailResponse | null = await res.json().catch(() => null)

        if (!res.ok || !data) {
          toast.error(data?.error || "تعذر تحميل بيانات الطلب")
          setDraft(null)
          return
        }

        setDraft(data)
      } catch (error) {
        console.error("Load draft preview error:", error)
        toast.error("حدث خطأ أثناء تحميل بيانات الطلب")
        setDraft(null)
      } finally {
        setLoading(false)
      }
    }

    void loadDraft()
  }, [API, draftId])

  const planName = draft?.plan?.name || "-"
  const basePrice = normalizeNumber(draft?.pricing?.base_price)
  const discountAmount = normalizeNumber(draft?.pricing?.discount_amount)
  const vatAmount = normalizeNumber(draft?.pricing?.vat)
  const totalAmount = normalizeNumber(draft?.pricing?.total)

  const selectedMethod = draft?.payment_method || "BANK_TRANSFER"
  const MethodIcon = getMethodIcon(selectedMethod)

  const canVerifyBankTransfer =
    !!draft &&
    draft.status !== "PAID" &&
    (draft.payment_method === "BANK_TRANSFER" || !draft.payment_method)

  const isBankTransferMethod =
    selectedMethod === "BANK_TRANSFER" || selectedMethod === null

  const address = useMemo(() => {
    const national = draft?.company?.national_address || {}

    return {
      buildingNo: national.building_no || "-",
      street: national.street || "-",
      district: national.district || "-",
      postalCode: national.postal_code || "-",
      shortAddress: national.short_address || "-",
    }
  }, [draft])

  const confirmBankTransfer = async () => {
    if (!draftId) {
      toast.error("رقم الطلب غير موجود")
      return
    }

    if (!draft) {
      toast.error("بيانات الطلب غير متوفرة")
      return
    }

    if (draft.status === "PAID") {
      toast.success("تم اعتماد هذا الطلب سابقًا")
      return
    }

    if (!canVerifyBankTransfer) {
      toast.error("هذا الطلب ليس تحويلًا بنكيًا قابلًا للاعتماد من هذه الصفحة")
      return
    }

    if (!API) {
      toast.error("تعذر الوصول إلى الخادم")
      return
    }

    try {
      setConfirming(true)

      const csrfToken = await ensureCsrf(API)

      const res = await fetch(`${API}/api/system/onboarding/confirm-payment/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || "",
        },
        body: JSON.stringify({
          draft_id: draftId,
          payment_method: "BANK_TRANSFER",
          gateway_status: "VERIFIED",
        }),
      })

      const data: ConfirmPaymentResponse | null = await res.json().catch(() => null)

      if (!res.ok || !data) {
        toast.error(
          data?.details ||
            data?.error ||
            "فشل اعتماد التحويل البنكي"
        )
        return
      }

      toast.success("تم اعتماد التحويل البنكي وتفعيل الشركة بنجاح")

      if (data.company_id) {
        router.push(`/system/companies/${data.company_id}`)
        return
      }

      if (data.invoice_id) {
        router.push(`/system/invoices`)
        return
      }

      router.push("/system/companies")
    } catch (error) {
      console.error("Confirm bank transfer error:", error)
      toast.error("حدث خطأ غير متوقع أثناء اعتماد التحويل البنكي")
    } finally {
      setConfirming(false)
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <Card>
          <CardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            جارٍ تحميل بيانات طلب التسجيل...
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!draft) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 p-6">
        <Card>
          <CardContent className="py-8 text-center">
            <div className="text-lg font-semibold">الطلب غير موجود</div>
            <div className="mt-2 text-sm text-muted-foreground">
              تعذر العثور على طلب التسجيل المطلوب.
            </div>
          </CardContent>
        </Card>

        <Button
          variant="outline"
          onClick={() => router.push("/system/payments")}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          العودة
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6" dir="rtl">
      <div className="flex flex-col gap-4 rounded-3xl border bg-background p-6 shadow-sm lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-2 text-right">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <ReceiptText className="h-4 w-4" />
            مراجعة طلب تسجيل شركة
          </div>

          <h1 className="text-3xl font-bold tracking-tight">
            {isBankTransferMethod
              ? "مراجعة واعتماد التحويل البنكي"
              : "مراجعة حالة طلب الدفع"}
          </h1>

          <p className="text-sm text-muted-foreground">
            {isBankTransferMethod
              ? "راجع بيانات الطلب ثم اعتمد التحويل البنكي لتفعيل الشركة وإنشاء الفاتورة والدفعة."
              : "راجع بيانات الطلب وطريقة الدفع المسجلة. هذه الصفحة مخصصة لاعتماد التحويل البنكي فقط."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Badge variant={getStatusBadgeVariant(draft.status)} className="px-4 py-1.5 text-sm">
            الحالة: {getStatusLabel(draft.status)}
          </Badge>

          <Badge variant="outline" className="px-4 py-1.5 text-sm">
            رقم الطلب: {draft.draft_id}
          </Badge>

          <Button
            variant="outline"
            onClick={() => router.back()}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            رجوع
          </Button>
        </div>
      </div>

      <Card
        className={
          draft.status === "PAID"
            ? "border-emerald-200 bg-emerald-50/70"
            : isBankTransferMethod
            ? "border-amber-200 bg-amber-50/70"
            : "border-sky-200 bg-sky-50/70"
        }
      >
        <CardContent className="flex flex-col gap-3 py-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-3">
            {draft.status === "PAID" ? (
              <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-600" />
            ) : isBankTransferMethod ? (
              <Landmark className="mt-0.5 h-5 w-5 text-amber-600" />
            ) : (
              <MethodIcon className="mt-0.5 h-5 w-5 text-sky-600" />
            )}

            <div className="text-right">
              <p
                className={`font-medium ${
                  draft.status === "PAID"
                    ? "text-emerald-700"
                    : isBankTransferMethod
                    ? "text-amber-700"
                    : "text-sky-700"
                }`}
              >
                {draft.status === "PAID"
                  ? "تم اعتماد الطلب سابقًا"
                  : isBankTransferMethod
                  ? "الطلب بانتظار الاعتماد المالي"
                  : "الطلب مسجل كدفع إلكتروني"}
              </p>

              <p
                className={`text-sm ${
                  draft.status === "PAID"
                    ? "text-emerald-700/80"
                    : isBankTransferMethod
                    ? "text-amber-700/80"
                    : "text-sky-700/80"
                }`}
              >
                طريقة الدفع المسجلة: {getMethodLabel(selectedMethod)}
              </p>
            </div>
          </div>

          <div className="text-sm text-right text-muted-foreground">
            {draft.status === "PAID"
              ? "تم إنشاء الشركة والاشتراك والفاتورة والدفعة لهذا الطلب."
              : isBankTransferMethod
              ? "عند اعتماد التحويل البنكي سيتم تفعيل الشركة مباشرة داخل النظام."
              : "يتم اعتماد المدفوعات الإلكترونية من خلال البوابة والويبهوك، وليس من هذه الصفحة."}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-12">
        <div className="space-y-6 xl:col-span-8">
          <Card className="overflow-hidden">
            <CardHeader className="border-b bg-muted/30">
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" />
                <CardTitle>بيانات الشركة</CardTitle>
              </div>
            </CardHeader>

            <CardContent className="grid gap-4 p-6 md:grid-cols-2">
              <div>
                <div className="mb-1 text-sm text-muted-foreground">اسم الشركة</div>
                <div className="font-medium">{draft.company_name || "-"}</div>
              </div>

              <div>
                <div className="mb-1 text-sm text-muted-foreground">البريد الإلكتروني</div>
                <div className="font-medium">{draft.company?.email || "-"}</div>
              </div>

              <div>
                <div className="mb-1 text-sm text-muted-foreground">رقم الجوال</div>
                <div className="font-medium">{draft.company?.phone || "-"}</div>
              </div>

              <div>
                <div className="mb-1 text-sm text-muted-foreground">المدينة</div>
                <div className="font-medium">{draft.company?.city || "-"}</div>
              </div>

              <div>
                <div className="mb-1 text-sm text-muted-foreground">السجل التجاري</div>
                <div className="font-medium">{draft.company?.commercial_number || "-"}</div>
              </div>

              <div>
                <div className="mb-1 text-sm text-muted-foreground">الرقم الضريبي</div>
                <div className="font-medium">{draft.company?.tax_number || "-"}</div>
              </div>
            </CardContent>
          </Card>

          <Card className="overflow-hidden">
            <CardHeader className="border-b bg-muted/30">
              <div className="flex items-center gap-2">
                <MapPin className="h-5 w-5 text-primary" />
                <CardTitle>العنوان الوطني</CardTitle>
              </div>
            </CardHeader>

            <CardContent className="grid gap-4 p-6 md:grid-cols-2">
              <div>
                <div className="mb-1 text-sm text-muted-foreground">رقم المبنى</div>
                <div className="font-medium">{address.buildingNo}</div>
              </div>

              <div>
                <div className="mb-1 text-sm text-muted-foreground">الشارع</div>
                <div className="font-medium">{address.street}</div>
              </div>

              <div>
                <div className="mb-1 text-sm text-muted-foreground">الحي</div>
                <div className="font-medium">{address.district}</div>
              </div>

              <div>
                <div className="mb-1 text-sm text-muted-foreground">الرمز البريدي</div>
                <div className="font-medium">{address.postalCode}</div>
              </div>

              <div className="md:col-span-2">
                <div className="mb-1 text-sm text-muted-foreground">العنوان المختصر</div>
                <div className="font-medium">{address.shortAddress}</div>
              </div>
            </CardContent>
          </Card>

          <Card className="overflow-hidden">
            <CardHeader className="border-b bg-muted/30">
              <div className="flex items-center gap-2">
                <User2 className="h-5 w-5 text-primary" />
                <CardTitle>بيانات الأدمن الأساسي</CardTitle>
              </div>
            </CardHeader>

            <CardContent className="grid gap-4 p-6 md:grid-cols-2">
              <div>
                <div className="mb-1 text-sm text-muted-foreground">الاسم</div>
                <div className="font-medium">{draft.admin?.name || "-"}</div>
              </div>

              <div>
                <div className="mb-1 text-sm text-muted-foreground">اسم المستخدم</div>
                <div className="font-medium">{draft.admin?.username || "-"}</div>
              </div>

              <div className="md:col-span-2">
                <div className="mb-1 text-sm text-muted-foreground">البريد الإلكتروني</div>
                <div className="font-medium">{draft.admin?.email || "-"}</div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6 xl:col-span-4">
          <Card>
            <CardHeader>
              <CardTitle>ملخص الاشتراك</CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="rounded-2xl border bg-muted/20 p-4">
                <div className="mb-3 flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-background">
                    <Image
                      src="/currency/sar.svg"
                      alt="SAR"
                      width={26}
                      height={26}
                      className="object-contain"
                    />
                  </div>

                  <div className="text-right">
                    <div className="text-sm text-muted-foreground">الإجمالي المستحق</div>
                    <div className="text-2xl font-bold">
                      {formatMoney(totalAmount)}
                    </div>
                  </div>
                </div>

                <div className="space-y-3 rounded-2xl border bg-background p-4">
                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">الباقة</span>
                    <span className="font-medium">{planName}</span>
                  </div>

                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">دورة الفوترة</span>
                    <span className="font-medium">{getDurationLabel(draft.duration)}</span>
                  </div>

                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">تاريخ البداية</span>
                    <span className="font-medium">{formatDate(draft.dates?.start_date)}</span>
                  </div>

                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">تاريخ النهاية</span>
                    <span className="font-medium">{formatDate(draft.dates?.end_date)}</span>
                  </div>

                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">السعر الأساسي</span>
                    <span className="font-medium">{formatMoney(basePrice)}</span>
                  </div>

                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">الخصم</span>
                    <span className="font-medium">- {formatMoney(discountAmount)}</span>
                  </div>

                  <div className="flex justify-between gap-4">
                    <span className="text-muted-foreground">الضريبة</span>
                    <span className="font-medium">{formatMoney(vatAmount)}</span>
                  </div>

                  <div className="border-t pt-3">
                    <div className="flex justify-between gap-4 text-lg font-bold">
                      <span>الإجمالي</span>
                      <span>{formatMoney(totalAmount)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>
                {isBankTransferMethod ? "اعتماد الدفع" : "مراجعة طريقة الدفع"}
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="rounded-2xl border border-primary/15 bg-primary/5 p-4 text-sm text-muted-foreground">
                <div className="mb-2 flex items-center gap-2 font-medium text-foreground">
                  <MethodIcon className="h-4 w-4" />
                  طريقة الدفع المسجلة
                </div>

                <div className="font-medium">
                  {getMethodLabel(selectedMethod)}
                </div>

                <div className="mt-2 text-xs text-muted-foreground">
                  {getMethodDescription(selectedMethod)}
                </div>
              </div>

              {!isBankTransferMethod && (
                <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-700">
                  هذا الطلب مسجل كدفع إلكتروني عبر <strong>{getMethodLabel(selectedMethod)}</strong>.
                  لا يتم اعتماده يدويًا من هذه الصفحة، وإنما عبر تأكيد البوابة والويبهوك.
                </div>
              )}

              {selectedMethod !== "BANK_TRANSFER" && (
                <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
                  هذه الصفحة مخصصة لاعتماد التحويل البنكي فقط. للمدفوعات الإلكترونية مثل
                  Tap أو Tamara أو البطاقات، يتم التفعيل بعد تأكيد البوابة.
                </div>
              )}

              {draft.status === "PAID" ? (
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
                  تم اعتماد هذا الطلب سابقًا ولا يمكن تكرار العملية.
                </div>
              ) : (
                <Button
                  onClick={() => void confirmBankTransfer()}
                  disabled={confirming || !canVerifyBankTransfer}
                  className="w-full gap-2"
                >
                  {confirming ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4" />
                  )}

                  {confirming
                    ? "جارٍ اعتماد التحويل البنكي..."
                    : "تأكيد التحويل البنكي"}
                </Button>
              )}

              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
                className="w-full"
                disabled={confirming}
              >
                رجوع
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-start gap-3 text-sm text-muted-foreground">
                <FileText className="mt-0.5 h-4 w-4 text-primary" />
                <div className="text-right">
                  {isBankTransferMethod ? (
                    <>
                      عند الضغط على <strong>تأكيد التحويل البنكي</strong> سيقوم النظام بإنشاء
                      الشركة والاشتراك والفاتورة وسجل الدفعة، ثم تفعيل الطلب نهائيًا.
                    </>
                  ) : (
                    <>
                      هذا الطلب يستخدم <strong>{getMethodLabel(selectedMethod)}</strong>.
                      لا حاجة لاعتماد يدوي من هذه الصفحة طالما أن البوابة ستقوم بإرسال
                      التأكيد النهائي إلى النظام.
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}