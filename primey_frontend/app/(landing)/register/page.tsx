"use client"

import Image from "next/image"
import { Suspense, useEffect, useMemo, useRef, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

import { toast } from "sonner"

import {
  ArrowLeft,
  ArrowRight,
  Building2,
  CheckCircle2,
  CreditCard,
  FileText,
  Landmark,
  Loader2,
  MapPin,
  QrCode,
  ReceiptText,
  ShieldCheck,
  User2,
  Wallet,
  Languages,
  Phone,
} from "lucide-react"

const API = process.env.NEXT_PUBLIC_API_URL

type AppLocale = "ar" | "en"
type BillingCycle = "monthly" | "yearly"
type PaymentMethod = "BANK_TRANSFER" | "CREDIT_CARD" | "TAMARA"

type Plan = {
  id: number
  name: string
  description?: string
  price_monthly: number | null
  price_yearly: number | null
  max_companies: number | null
  max_employees: number | null
  is_active: boolean
  apps: string[]
}

type PlansResponse = {
  plans: Plan[]
}

type BillingPreview = {
  price?: number | string
  discount?: number | string
  subtotal?: number | string
  vat?: number | string
  total?: number | string
  code?: string
  valid?: boolean
}

type StartPaymentResponse = {
  draft_id?: string | number
  checkout_url?: string
  payment_url?: string
  redirect_url?: string
  url?: string
  message?: string
  success?: boolean
  ok?: boolean
  status?: string
  tap_charge_id?: string
  tap_status?: string
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

const countries = [
  {
    name: "Saudi Arabia",
    currency: "SAR",
    label: { ar: "المملكة العربية السعودية", en: "Saudi Arabia" },
  },
  {
    name: "UAE",
    currency: "AED",
    label: { ar: "الإمارات العربية المتحدة", en: "UAE" },
  },
  {
    name: "Egypt",
    currency: "EGP",
    label: { ar: "مصر", en: "Egypt" },
  },
]

function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null
  }

  return null
}

async function ensureCsrf() {
  if (!API) return null

  try {
    await fetch(`${API}/api/auth/csrf/`, {
      credentials: "include",
    })
  } catch {
    return null
  }

  return getCookie("csrftoken")
}

function generatePassword(length = 12) {
  const chars =
    "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%"

  let pass = ""

  for (let i = 0; i < length; i++) {
    pass += chars.charAt(Math.floor(Math.random() * chars.length))
  }

  return pass
}

function passwordStrength(password: string, locale: AppLocale) {
  let score = 0

  if (password.length >= 8) score++
  if (/[A-Z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  if (score <= 1) {
    return {
      label: locale === "ar" ? "ضعيفة" : "Weak",
      color: "bg-red-500",
      width: "25%",
      textClass: "text-red-600",
    }
  }

  if (score === 2) {
    return {
      label: locale === "ar" ? "متوسطة" : "Medium",
      color: "bg-yellow-500",
      width: "50%",
      textClass: "text-yellow-600",
    }
  }

  if (score === 3) {
    return {
      label: locale === "ar" ? "قوية" : "Strong",
      color: "bg-green-500",
      width: "75%",
      textClass: "text-green-600",
    }
  }

  return {
    label: locale === "ar" ? "قوية جدًا" : "Very Strong",
    color: "bg-emerald-600",
    width: "100%",
    textClass: "text-emerald-600",
  }
}

function normalizeNumber(value: unknown): number {
  if (typeof value === "number" && !Number.isNaN(value)) return value

  const parsed = Number(value ?? 0)
  return Number.isNaN(parsed) ? 0 : parsed
}

function formatMoney(value: number, currency = "SAR", locale: AppLocale = "ar") {
  return `${new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)} ${currency}`
}

function getMethodLabel(value: PaymentMethod, locale: AppLocale) {
  switch (value) {
    case "BANK_TRANSFER":
      return locale === "ar" ? "تحويل بنكي" : "Bank Transfer"
    case "CREDIT_CARD":
      return locale === "ar" ? "بطاقة ائتمانية" : "Credit Card"
    case "TAMARA":
      return "Tamara"
    default:
      return value
  }
}

function getMethodDescription(value: PaymentMethod, locale: AppLocale) {
  switch (value) {
    case "TAMARA":
      return locale === "ar"
        ? "قسّم دفعتك بأمان عبر بوابة تمارا."
        : "Split your payment securely through Tamara checkout."
    case "CREDIT_CARD":
      return locale === "ar"
        ? "ادفع أونلاين عبر بوابة Tap الآمنة للبطاقات."
        : "Pay online using Tap secure card gateway."
    case "BANK_TRANSFER":
      return locale === "ar"
        ? "أنشئ الطلب أولًا ثم أكمل التحويل وفق تعليمات المالية."
        : "Create the request first, then complete transfer according to finance instructions."
    default:
      return ""
  }
}

function buildRegisterUrl(params: Record<string, string | null | undefined>) {
  const search = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value && value.trim()) {
      search.set(key, value)
    }
  })

  const qs = search.toString()
  return qs ? `/register?${qs}` : "/register"
}

function normalizeReturnedPaymentMethod(value: string | null): PaymentMethod | null {
  const normalized = (value || "").trim().toUpperCase()

  if (normalized === "BANK_TRANSFER") return "BANK_TRANSFER"
  if (normalized === "CREDIT_CARD" || normalized === "TAP") return "CREDIT_CARD"
  if (normalized === "TAMARA") return "TAMARA"

  return null
}

function buildGatewayConfirmationPayload(params: {
  returnedDraftId: string | null
  returnedPaymentMethod: string | null
  returnedGatewayStatus: string | null
  returnedGatewayTransactionId: string | null
  paymentStatus: string | null
}) {
  const {
    returnedDraftId,
    returnedPaymentMethod,
    returnedGatewayStatus,
    returnedGatewayTransactionId,
    paymentStatus,
  } = params

  if (!returnedDraftId) {
    return null
  }

  const normalizedPaymentMethod =
    normalizeReturnedPaymentMethod(returnedPaymentMethod) ||
    (returnedGatewayTransactionId ? "CREDIT_CARD" : null)

  if (!normalizedPaymentMethod) {
    return null
  }

  let effectiveGatewayStatus = (returnedGatewayStatus || "").trim().toUpperCase()

  if (!effectiveGatewayStatus && paymentStatus === "success") {
    if (normalizedPaymentMethod === "CREDIT_CARD") {
      effectiveGatewayStatus = "CAPTURED"
    } else if (normalizedPaymentMethod === "TAMARA") {
      effectiveGatewayStatus = "APPROVED"
    }
  }

  if (!effectiveGatewayStatus) {
    return null
  }

  return {
    draft_id: returnedDraftId,
    payment_method: normalizedPaymentMethod,
    gateway_status: effectiveGatewayStatus,
    gateway_transaction_id: returnedGatewayTransactionId || null,
  }
}

function RegisterCompanyPageFallback() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6" dir="rtl">
      <Card>
        <CardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          جارٍ تحميل صفحة التسجيل...
        </CardContent>
      </Card>
    </div>
  )
}

function RegisterCompanyPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [locale, setLocale] = useState<AppLocale>("ar")

  const initialPlanId = searchParams.get("plan_id") || ""
  const initialPlanName = searchParams.get("plan_name") || ""
  const initialDraftId = searchParams.get("draft_id") || ""
  const paymentToastShownRef = useRef(false)
  const gatewayConfirmRunRef = useRef(false)

  /* =========================================================
     COMPANY
  ========================================================= */
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [city, setCity] = useState("")
  const [country, setCountry] = useState("Saudi Arabia")
  const [currency, setCurrency] = useState("SAR")
  const [commercialNumber, setCommercialNumber] = useState("")
  const [vatNumber, setVatNumber] = useState("")
  const [buildingNumber, setBuildingNumber] = useState("")
  const [street, setStreet] = useState("")
  const [district, setDistrict] = useState("")
  const [postalCode, setPostalCode] = useState("")
  const [shortAddress, setShortAddress] = useState("")

  /* =========================================================
     PLAN
  ========================================================= */
  const [plans, setPlans] = useState<Plan[]>([])
  const [planId, setPlanId] = useState(initialPlanId)
  const [plansLoading, setPlansLoading] = useState(true)
  const [billingCycle, setBillingCycle] = useState<BillingCycle>("monthly")

  /* =========================================================
     DISCOUNT / PREVIEW
  ========================================================= */
  const [discountCode, setDiscountCode] = useState("")
  const [preview, setPreview] = useState<BillingPreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  /* =========================================================
     ADMIN
  ========================================================= */
  const [ownerFirstName, setOwnerFirstName] = useState("")
  const [ownerLastName, setOwnerLastName] = useState("")
  const [ownerEmail, setOwnerEmail] = useState("")
  const [ownerPhone, setOwnerPhone] = useState("")
  const [ownerPassword, setOwnerPassword] = useState("")
  const [ownerUsername, setOwnerUsername] = useState("")

  /* =========================================================
     PAYMENT
  ========================================================= */
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("CREDIT_CARD")

  /* =========================================================
     STATE
  ========================================================= */
  const [loading, setLoading] = useState(false)
  const [plansError, setPlansError] = useState("")
  const [draftId, setDraftId] = useState(initialDraftId)
  const [draftConfirmed, setDraftConfirmed] = useState(false)
  const [lastActionMessage, setLastActionMessage] = useState("")
  const [gatewayConfirming, setGatewayConfirming] = useState(false)

  const isArabic = locale === "ar"
  const strength = passwordStrength(ownerPassword, locale)
  const BackIcon = isArabic ? ArrowRight : ArrowLeft

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null

      const nextLocale: AppLocale = savedLocale === "en" ? "en" : "ar"
      setLocale(nextLocale)

      if (typeof document !== "undefined") {
        document.documentElement.lang = nextLocale
        document.documentElement.dir = nextLocale === "ar" ? "rtl" : "ltr"
        document.body.setAttribute("dir", nextLocale === "ar" ? "rtl" : "ltr")
      }
    } catch (error) {
      console.error("Register locale initialization error:", error)
    }
  }, [])

  const toggleLanguage = () => {
    try {
      const nextLocale: AppLocale = locale === "ar" ? "en" : "ar"
      setLocale(nextLocale)

      if (typeof window !== "undefined") {
        window.localStorage.setItem("primey-locale", nextLocale)
      }

      if (typeof document !== "undefined") {
        document.documentElement.lang = nextLocale
        document.documentElement.dir = nextLocale === "ar" ? "rtl" : "ltr"
        document.body.setAttribute("dir", nextLocale === "ar" ? "rtl" : "ltr")
      }
    } catch (error) {
      console.error("Register language toggle error:", error)
    }
  }

  /* =========================================================
     LOAD PLANS
  ========================================================= */
  useEffect(() => {
    async function loadPlans() {
      try {
        if (!API) throw new Error("NEXT_PUBLIC_API_URL is not configured")

        setPlansError("")

        const res = await fetch(`${API}/api/system/plans/`, {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
          cache: "no-store",
        })

        if (!res.ok) {
          throw new Error("Failed to load plans")
        }

        const data: PlansResponse = await res.json()

        const normalized = Array.isArray(data?.plans)
          ? data.plans
              .filter((plan) => plan?.is_active !== false)
              .map((plan) => ({
                ...plan,
                id: normalizeNumber(plan.id),
                price_monthly: normalizeNumber(plan.price_monthly),
                price_yearly: normalizeNumber(plan.price_yearly),
                max_companies: normalizeNumber(plan.max_companies),
                max_employees: normalizeNumber(plan.max_employees),
                apps: Array.isArray(plan.apps) ? plan.apps : [],
              }))
          : []

        setPlans(normalized)

        if (!initialPlanId && normalized.length > 0) {
          setPlanId(String(normalized[0].id))
        }
      } catch (error) {
        console.error(error)
        setPlansError(isArabic ? "فشل تحميل الباقات" : "Failed to load plans")
        toast.error(isArabic ? "فشل تحميل الباقات" : "Failed to load plans")
      } finally {
        setPlansLoading(false)
      }
    }

    loadPlans()
  }, [initialPlanId, isArabic])

  /* =========================================================
     COUNTRY
  ========================================================= */
  useEffect(() => {
    const found = countries.find((c) => c.name === country)
    if (found) {
      setCurrency(found.currency)
    }
  }, [country])

  /* =========================================================
     SELECTED PLAN
  ========================================================= */
  const selectedPlan = useMemo(
    () => plans.find((p) => String(p.id) === String(planId)),
    [plans, planId]
  )

  /* =========================================================
     PREVIEW
  ========================================================= */
  useEffect(() => {
    if (!planId || !API) return

    async function loadPreview() {
      setPreviewLoading(true)

      try {
        const params = new URLSearchParams({
          plan_id: String(planId),
          billing_cycle: billingCycle,
        })

        if (discountCode.trim()) {
          params.append("discount_code", discountCode.trim())
        }

        const res = await fetch(`${API}/api/system/billing/preview/?${params}`, {
          credentials: "include",
          cache: "no-store",
        })

        const data = await res.json().catch(() => null)

        if (res.ok && data) {
          setPreview(data)
        } else {
          setPreview(null)
        }
      } catch (error) {
        console.error("Preview error:", error)
        setPreview(null)
      } finally {
        setPreviewLoading(false)
      }
    }

    loadPreview()
  }, [planId, billingCycle, discountCode])

  const localBasePrice =
    billingCycle === "monthly"
      ? normalizeNumber(selectedPlan?.price_monthly)
      : normalizeNumber(selectedPlan?.price_yearly)

  const basePrice = normalizeNumber(preview?.price ?? localBasePrice)
  const discountAmountPreview = normalizeNumber(preview?.discount ?? 0)
  const subtotal = normalizeNumber(
    preview?.subtotal ?? Math.max(localBasePrice - discountAmountPreview, 0)
  )
  const vatAmount = normalizeNumber(preview?.vat ?? subtotal * 0.15)
  const totalWithVat = normalizeNumber(preview?.total ?? subtotal + vatAmount)

  /* =========================================================
     PAYMENT RESULT TOAST
  ========================================================= */
  useEffect(() => {
    const paymentStatus = searchParams.get("payment")
    if (!paymentStatus || paymentToastShownRef.current) return

    paymentToastShownRef.current = true

    if (paymentStatus === "success") {
      toast.success(
        isArabic ? "تمت عملية الدفع بنجاح" : "Payment completed successfully"
      )
      setLastActionMessage(
        isArabic
          ? "تم الدفع بنجاح. جارٍ التحقق النهائي من تأكيد العملية."
          : "Payment completed successfully. Final payment confirmation is being checked."
      )
      return
    }

    if (paymentStatus === "cancelled") {
      toast.error(isArabic ? "تم إلغاء عملية الدفع" : "Payment was cancelled")
      setLastActionMessage(
        isArabic
          ? "تم إلغاء الدفع قبل الإكمال."
          : "Payment was cancelled before completion."
      )
      return
    }

    if (paymentStatus === "failed") {
      toast.error(isArabic ? "فشلت عملية الدفع" : "Payment failed")
      setLastActionMessage(
        isArabic ? "فشلت عملية الدفع. حاول مرة أخرى." : "Payment failed. Please try again."
      )
    }
  }, [searchParams, isArabic])

  /* =========================================================
     GATEWAY RETURN -> CONFIRM PAYMENT
  ========================================================= */
  useEffect(() => {
    async function confirmGatewayReturn() {
      if (!API) return
      if (gatewayConfirmRunRef.current) return

      const paymentStatus = searchParams.get("payment")
      const returnedDraftId = searchParams.get("draft_id")
      const returnedPaymentMethod = searchParams.get("payment_method")
      const returnedGatewayStatus = searchParams.get("gateway_status")
      const returnedGatewayTransactionId =
        searchParams.get("gateway_transaction_id") ||
        searchParams.get("transaction_id") ||
        searchParams.get("checkout_id") ||
        searchParams.get("tap_charge_id") ||
        searchParams.get("tap_id") ||
        ""

      const confirmationPayload = buildGatewayConfirmationPayload({
        returnedDraftId,
        returnedPaymentMethod,
        returnedGatewayStatus,
        returnedGatewayTransactionId,
        paymentStatus,
      })

      if (!confirmationPayload) {
        return
      }

      gatewayConfirmRunRef.current = true
      setGatewayConfirming(true)

      try {
        const csrfToken = await ensureCsrf()

        const res = await fetch(`${API}/api/system/onboarding/confirm-payment/`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken || "",
          },
          body: JSON.stringify(confirmationPayload),
        })

        const data: ConfirmPaymentResponse | null = await res.json().catch(() => null)

        if (res.status === 409) {
          setDraftId(confirmationPayload.draft_id)
          setDraftConfirmed(true)

          toast.success(
            isArabic ? "تم اعتماد الدفع مسبقًا" : "Payment already confirmed"
          )

          setLastActionMessage(
            isArabic
              ? "تم اعتماد هذه العملية مسبقًا. يمكنك الآن تسجيل الدخول إلى حساب الشركة."
              : "This payment was already confirmed earlier. You can now log in to the company account."
          )

          router.replace(
            buildRegisterUrl({
              plan_id: planId || initialPlanId,
              plan_name: selectedPlan?.name || initialPlanName,
              draft_id: confirmationPayload.draft_id,
              payment: "success",
            })
          )
          return
        }

        if (!res.ok || !data) {
          toast.error(
            data?.details ||
              data?.error ||
              (isArabic
                ? "فشل تأكيد الدفع بعد العودة من البوابة"
                : "Failed to confirm payment after gateway return")
          )
          setLastActionMessage(
            data?.details ||
              data?.error ||
              (isArabic
                ? "فشل تأكيد الدفع بعد العودة من بوابة الدفع."
                : "Failed to confirm payment after returning from the gateway.")
          )
          gatewayConfirmRunRef.current = false
          return
        }

        setDraftId(confirmationPayload.draft_id)
        setDraftConfirmed(true)

        if (data.company_name) {
          toast.success(
            isArabic ? "تم تفعيل الشركة بنجاح" : "Company activated successfully"
          )
          setLastActionMessage(
            isArabic
              ? `تم تأكيد الدفع بنجاح وتم تفعيل الشركة "${data.company_name}". يمكنك الآن تسجيل الدخول بالحساب الذي أنشأته.`
              : `Payment confirmed successfully and company "${data.company_name}" has been activated. You can now sign in with the account you created.`
          )
        } else if (data.message) {
          toast.success(
            isArabic ? "تم تأكيد الدفع بنجاح" : "Payment confirmed successfully"
          )
          setLastActionMessage(data.message)
        } else {
          toast.success(
            isArabic ? "تم تأكيد الدفع بنجاح" : "Payment confirmed successfully"
          )
          setLastActionMessage(
            isArabic
              ? "تم تأكيد الدفع بنجاح واكتمل إعداد التسجيل."
              : "Payment confirmed successfully and onboarding has been completed."
          )
        }

        router.replace(
          buildRegisterUrl({
            plan_id: planId || initialPlanId,
            plan_name: selectedPlan?.name || initialPlanName,
            draft_id: confirmationPayload.draft_id,
            payment: "success",
          })
        )
      } catch (error) {
        console.error("Gateway confirmation error:", error)
        toast.error(
          isArabic
            ? "حدث خطأ غير متوقع أثناء تأكيد الدفع"
            : "Unexpected error while confirming payment"
        )
        setLastActionMessage(
          isArabic
            ? "حدث خطأ غير متوقع أثناء تأكيد الدفع."
            : "Unexpected error while confirming payment."
        )
        gatewayConfirmRunRef.current = false
      } finally {
        setGatewayConfirming(false)
      }
    }

    confirmGatewayReturn()
  }, [
    searchParams,
    router,
    planId,
    initialPlanId,
    selectedPlan?.name,
    initialPlanName,
    isArabic,
  ])

  /* =========================================================
     APPLY DISCOUNT
  ========================================================= */
  const applyDiscount = async () => {
    if (!discountCode.trim()) {
      toast.error(isArabic ? "أدخل كود الخصم" : "Enter discount code")
      return
    }

    if (!planId) {
      toast.error(isArabic ? "اختر الباقة أولًا" : "Select plan first")
      return
    }

    if (!API) {
      toast.error(isArabic ? "إعداد API غير موجود" : "API not configured")
      return
    }

    try {
      const params = new URLSearchParams({
        plan_id: String(planId),
        billing_cycle: billingCycle,
        discount_code: discountCode.trim(),
      })

      const res = await fetch(`${API}/api/system/billing/preview/?${params}`, {
        credentials: "include",
        cache: "no-store",
      })

      const data = await res.json().catch(() => null)

      if (!res.ok || !data) {
        toast.error(isArabic ? "كود الخصم غير صالح" : "Invalid discount code")
        return
      }

      setPreview(data)
      toast.success(isArabic ? "تم تطبيق الخصم" : "Discount applied")
    } catch (error) {
      console.error("Discount validation error:", error)
      toast.error(
        isArabic ? "فشل التحقق من كود الخصم" : "Failed to validate code"
      )
    }
  }

  /* =========================================================
     VALIDATION
  ========================================================= */
  function validateBeforeSubmit() {
    if (!API) {
      toast.error(isArabic ? "إعداد API غير موجود" : "API not configured")
      return false
    }

    if (!name.trim()) {
      toast.error(isArabic ? "اسم الشركة مطلوب" : "Company name required")
      return false
    }

    if (!planId) {
      toast.error(isArabic ? "اختر الباقة" : "Select plan")
      return false
    }

    if (!ownerFirstName.trim()) {
      toast.error(isArabic ? "الاسم الأول للمدير مطلوب" : "Owner first name required")
      return false
    }

    if (!ownerLastName.trim()) {
      toast.error(isArabic ? "اسم العائلة للمدير مطلوب" : "Owner last name required")
      return false
    }

    if (!ownerEmail.trim()) {
      toast.error(isArabic ? "بريد المدير مطلوب" : "Admin email required")
      return false
    }

    if (!ownerPhone.trim()) {
      toast.error(isArabic ? "رقم جوال المدير مطلوب" : "Admin phone required")
      return false
    }

    if (!ownerUsername.trim()) {
      toast.error(isArabic ? "اسم المستخدم مطلوب" : "Username required")
      return false
    }

    if (!ownerPassword.trim()) {
      toast.error(isArabic ? "كلمة المرور مطلوبة" : "Password required")
      return false
    }

    if (ownerPassword.trim().length < 8) {
      toast.error(
        isArabic
          ? "يجب أن تكون كلمة المرور 8 أحرف على الأقل"
          : "Password must be at least 8 characters"
      )
      return false
    }

    return true
  }

  /* =========================================================
     START PAYMENT ONLY
  ========================================================= */
  async function startPaymentAfterDraft(args: {
    currentDraftId: string
    selectedPaymentMethod: PaymentMethod
    csrfToken: string
  }) {
    if (!API) return false

    const { currentDraftId, selectedPaymentMethod, csrfToken } = args

    if (selectedPaymentMethod === "BANK_TRANSFER") {
      setLastActionMessage(
        isArabic
          ? "تم إنشاء طلب التسجيل بنجاح. سيبقى التحويل البنكي معلقًا حتى يتم التحقق المالي."
          : "Registration request created successfully. Bank transfer will remain pending until finance verification is completed."
      )
      toast.success(
        isArabic
          ? "تم إنشاء طلب التسجيل بنجاح"
          : "Registration request created successfully"
      )
      return true
    }

    if (selectedPaymentMethod === "CREDIT_CARD") {
      try {
        const res = await fetch(`${API}/api/system/payments/tap/create-checkout/`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken || "",
          },
          body: JSON.stringify({
            draft_id: currentDraftId,
            payment_method: "CREDIT_CARD",
            billing_cycle: billingCycle,
            discount_code: discountCode || null,
          }),
        })

        const data: StartPaymentResponse | null = await res.json().catch(() => null)

        if (!res.ok || !data) {
          toast.error(
            data?.message ||
              (isArabic
                ? "فشل إنشاء رابط الدفع عبر البطاقات"
                : "Failed to create card checkout URL")
          )
          return false
        }

        const checkoutUrl =
          data.checkout_url ||
          data.payment_url ||
          data.redirect_url ||
          data.url ||
          null

        const returnedDraftId = String(data.draft_id || currentDraftId)

        if (returnedDraftId) {
          setDraftId(returnedDraftId)
        }

        if (typeof data.message === "string" && data.message.trim()) {
          setLastActionMessage(data.message)
        }

        if (checkoutUrl && typeof window !== "undefined") {
          toast.success(
            isArabic
              ? "جارٍ تحويلك إلى بوابة الدفع..."
              : "Redirecting to payment gateway..."
          )
          window.location.href = checkoutUrl
          return true
        }

        toast.error(
          isArabic
            ? "لم يتم استلام رابط الدفع من الخادم"
            : "No checkout URL was returned from the server"
        )
        return false
      } catch (error) {
        console.error("Card payment start failed:", error)
        toast.error(
          isArabic
            ? "حدث خطأ أثناء بدء الدفع بالبطاقة"
            : "An error occurred while starting card payment"
        )
        return false
      }
    }

    if (selectedPaymentMethod === "TAMARA") {
      try {
        const res = await fetch(`${API}/api/system/payments/tamara/create-checkout/`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken || "",
          },
          body: JSON.stringify({
            draft_id: currentDraftId,
            payment_method: "TAMARA",
            billing_cycle: billingCycle,
            discount_code: discountCode || null,
          }),
        })

        const data: StartPaymentResponse | null = await res.json().catch(() => null)

        if (!res.ok || !data) {
          toast.error(
            data?.message ||
              (isArabic
                ? "فشل إنشاء رابط الدفع عبر تمارا"
                : "Failed to create Tamara checkout URL")
          )
          return false
        }

        const checkoutUrl =
          data.checkout_url ||
          data.payment_url ||
          data.redirect_url ||
          data.url ||
          null

        const returnedDraftId = String(data.draft_id || currentDraftId)

        if (returnedDraftId) {
          setDraftId(returnedDraftId)
        }

        if (typeof data.message === "string" && data.message.trim()) {
          setLastActionMessage(data.message)
        }

        if (checkoutUrl && typeof window !== "undefined") {
          toast.success(
            isArabic
              ? "جارٍ تحويلك إلى بوابة تمارا..."
              : "Redirecting to Tamara..."
          )
          window.location.href = checkoutUrl
          return true
        }

        toast.error(
          isArabic
            ? "لم يتم استلام رابط تمارا من الخادم"
            : "No Tamara checkout URL was returned from the server"
        )
        return false
      } catch (error) {
        console.error("Tamara payment start failed:", error)
        toast.error(
          isArabic
            ? "حدث خطأ أثناء بدء الدفع عبر تمارا"
            : "An error occurred while starting Tamara payment"
        )
        return false
      }
    }

    return false
  }

  /* =========================================================
     CREATE REGISTRATION DRAFT + PAYMENT START
  ========================================================= */
  const createRegistrationDraft = async () => {
    if (!validateBeforeSubmit()) return

    setLoading(true)

    try {
      const csrfToken = await ensureCsrf()

      const payload = {
        company_name: name.trim(),
        email: email.trim(),
        phone: phone.trim(),
        city: city.trim(),
        country,
        currency,
        commercial_number: commercialNumber.trim(),
        vat_number: vatNumber.trim(),
        national_address: {
          building_number: buildingNumber.trim(),
          street: street.trim(),
          district: district.trim(),
          city: city.trim(),
          postal_code: postalCode.trim(),
          short_address: shortAddress.trim(),
        },

        plan_id: planId,
        duration: billingCycle,
        discount_code: discountCode.trim() || null,
        payment_method: paymentMethod,

        admin_username: ownerUsername.trim(),
        admin_name: `${ownerFirstName} ${ownerLastName}`.trim(),
        admin_email: ownerEmail.trim(),
        admin_phone: ownerPhone.trim(),
        admin_password: ownerPassword,
      }

      const createRes = await fetch(`${API}/api/system/onboarding/create-draft/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || "",
        },
        body: JSON.stringify(payload),
      })

      const createData = await createRes.json().catch(() => null)

      if (!createRes.ok || !createData) {
        toast.error(
          createData?.details ||
            createData?.error ||
            (isArabic
              ? "فشل إنشاء مسودة التسجيل"
              : "Failed to create registration draft")
        )
        return
      }

      const newDraftId = String(createData.draft_id)
      setDraftId(newDraftId)

      const confirmRes = await fetch(`${API}/api/system/onboarding/confirm-draft/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || "",
        },
        body: JSON.stringify({
          draft_id: createData.draft_id,
        }),
      })

      const confirmData = await confirmRes.json().catch(() => null)

      if (!confirmRes.ok) {
        toast.error(
          confirmData?.error ||
            (isArabic ? "فشل تأكيد المسودة" : "Failed to confirm draft")
        )
        return
      }

      setDraftConfirmed(true)

      const directCheckoutUrl =
        createData?.checkout_url ||
        createData?.payment_url ||
        createData?.redirect_url ||
        confirmData?.checkout_url ||
        confirmData?.payment_url ||
        confirmData?.redirect_url ||
        null

      if (typeof confirmData?.message === "string" && confirmData.message.trim()) {
        setLastActionMessage(confirmData.message)
      } else {
        setLastActionMessage(
          paymentMethod === "BANK_TRANSFER"
            ? isArabic
              ? "تم إنشاء طلب التسجيل بنجاح. سيبقى الطلب معلقًا حتى يتم التحقق من التحويل البنكي."
              : "Registration request created successfully. It will remain pending until the bank transfer is verified."
            : isArabic
            ? "تم إنشاء طلب التسجيل بنجاح. أكمل الدفع لتفعيل شركتك."
            : "Registration request created successfully. Continue with payment to activate your company."
        )
      }

      router.replace(
        buildRegisterUrl({
          plan_id: planId,
          plan_name: selectedPlan?.name || initialPlanName,
          draft_id: createData.draft_id ? String(createData.draft_id) : newDraftId,
        })
      )

      toast.success(
        isArabic
          ? "تم إنشاء طلب التسجيل بنجاح"
          : "Registration request created successfully"
      )

      if (
        paymentMethod !== "BANK_TRANSFER" &&
        directCheckoutUrl &&
        typeof window !== "undefined"
      ) {
        toast.success(
          isArabic
            ? "جارٍ تحويلك إلى بوابة الدفع..."
            : "Redirecting to payment gateway..."
        )
        window.location.href = directCheckoutUrl
        return
      }

      const paymentStarted = await startPaymentAfterDraft({
        currentDraftId: newDraftId,
        selectedPaymentMethod: paymentMethod,
        csrfToken: csrfToken || "",
      })

      if (!paymentStarted) {
        if (
          paymentMethod === "TAMARA" ||
          paymentMethod === "CREDIT_CARD"
        ) {
          toast.info(
            isArabic
              ? "تم إنشاء المسودة بنجاح، لكن لم يتم إرجاع رابط الدفع من الخادم بعد."
              : "Draft created successfully, but no payment redirect URL was returned from the backend."
          )
          setLastActionMessage(
            isArabic
              ? "تم إنشاء المسودة بنجاح، لكن الخادم لم يُرجع رابط بوابة الدفع بعد."
              : "Draft created successfully, but the backend did not return a checkout URL yet."
          )
        } else {
          toast.info(
            isArabic
              ? "تم إنشاء المسودة بنجاح وهي الآن بانتظار التحقق من التحويل البنكي."
              : "Draft created successfully and is awaiting bank transfer verification."
          )
        }
      }
    } catch (error) {
      console.error(error)
      toast.error(isArabic ? "حدث خطأ غير متوقع" : "Unexpected error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="mx-auto max-w-7xl space-y-6 p-6"
      dir={isArabic ? "rtl" : "ltr"}
    >
      <div className="flex flex-col gap-4 rounded-3xl border bg-background p-6 shadow-sm lg:flex-row lg:items-center lg:justify-between">
        <div className={`space-y-2 ${isArabic ? "text-right" : "text-left"}`}>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <ReceiptText className="h-4 w-4" />
            {isArabic ? "التسجيل العام" : "Public Registration"}
          </div>

          <h1 className="text-3xl font-bold tracking-tight">
            {isArabic ? "سجل شركتك" : "Register Your Company"}
          </h1>

          <p className="text-sm text-muted-foreground">
            {isArabic
              ? "أنشئ طلب تسجيل شركتك، وراجع ملخص الفاتورة، واختر طريقة الدفع، ثم أكمل بأمان."
              : "Create your company registration request, review the invoice summary, choose your payment method, and continue securely."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={toggleLanguage}
            className="h-9 rounded-xl"
          >
            <Languages className="h-4 w-4" />
            <span>{isArabic ? "EN" : "عربي"}</span>
          </Button>

          {selectedPlan?.name || initialPlanName ? (
            <Badge className="rounded-full px-4 py-1.5 text-sm">
              {isArabic ? "الباقة:" : "Plan:"} {selectedPlan?.name || initialPlanName}
            </Badge>
          ) : null}

          <Button
            variant="outline"
            onClick={() => router.push("/#pricing")}
            className="gap-2"
          >
            <BackIcon className="h-4 w-4" />
            {isArabic ? "العودة إلى الأسعار" : "Back to Pricing"}
          </Button>
        </div>
      </div>

      {draftId ? (
        <Card className="border-emerald-200 bg-emerald-50/60">
          <CardContent className="flex flex-col gap-3 py-5 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-600" />
              <div className={isArabic ? "text-right" : "text-left"}>
                <p className="font-medium text-emerald-700">
                  {isArabic
                    ? "تم إنشاء مسودة التسجيل بنجاح"
                    : "Registration draft created successfully"}
                </p>
                <p className="text-sm text-emerald-700/80">
                  {isArabic ? "رقم المسودة:" : "Draft ID:"} {draftId}
                  {draftConfirmed
                    ? isArabic
                      ? " • الحالة: تم التأكيد"
                      : " • Status: CONFIRMED"
                    : ""}
                </p>
              </div>
            </div>

            <div className={`text-sm text-emerald-700/90 ${isArabic ? "text-right" : "text-left"}`}>
              {isArabic
                ? "لن يتم تفعيل الشركة إلا بعد نجاح تأكيد الدفع من البوابة."
                : "Company activation will happen only after successful gateway confirmation."}
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-12">
        <div className="space-y-6 xl:col-span-8">
          <Card className="overflow-hidden">
            <CardHeader className="border-b bg-muted/30 pb-6">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                <div className={`space-y-4 ${isArabic ? "text-right" : "text-left"}`}>
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
                    <Building2 className="h-7 w-7 text-primary" />
                  </div>

                  <div>
                    <CardTitle className="text-2xl font-bold">
                      {isArabic ? "طلب تسجيل شركة" : "Company Registration Request"}
                    </CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {isArabic
                        ? "أدخل بيانات الشركة وحساب المدير وإعدادات الاشتراك."
                        : "Enter the company details, admin account, and billing setup."}
                    </p>
                  </div>
                </div>

                <div className="grid gap-3 text-sm lg:min-w-[280px]">
                  <div className="flex items-center justify-between rounded-xl border bg-background px-4 py-3">
                    <span className="text-muted-foreground">
                      {isArabic ? "الباقة المختارة" : "Selected Plan"}
                    </span>
                    <span className="font-semibold">
                      {selectedPlan?.name || initialPlanName || "-"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between rounded-xl border bg-background px-4 py-3">
                    <span className="text-muted-foreground">
                      {isArabic ? "دورة الفوترة" : "Billing Cycle"}
                    </span>
                    <span className="font-medium capitalize">
                      {billingCycle === "monthly"
                        ? isArabic
                          ? "شهري"
                          : "monthly"
                        : isArabic
                        ? "سنوي"
                        : "yearly"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between rounded-xl border bg-background px-4 py-3">
                    <span className="text-muted-foreground">
                      {isArabic ? "طريقة الدفع" : "Payment Method"}
                    </span>
                    <span className="font-medium">
                      {getMethodLabel(paymentMethod, locale)}
                    </span>
                  </div>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6 p-6">
              <div className="rounded-2xl border">
                <div className="border-b bg-muted/30 px-5 py-4">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-primary" />
                    <h3 className="font-semibold">
                      {isArabic ? "معلومات الشركة" : "Company Information"}
                    </h3>
                  </div>
                </div>

                <div className="grid gap-4 p-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "اسم الشركة" : "Company Name"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "اسم الشركة" : "Company Name"}
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "بريد الشركة" : "Company Email"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "بريد الشركة" : "Company Email"}
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "رقم الجوال" : "Phone"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "رقم الجوال" : "Phone"}
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "المدينة" : "City"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "المدينة" : "City"}
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "الدولة" : "Country"}
                    </label>
                    <select
                      dir={isArabic ? "rtl" : "ltr"}
                      className={`flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ${
                        isArabic ? "text-right" : "text-left"
                      }`}
                      value={country}
                      onChange={(e) => setCountry(e.target.value)}
                    >
                      {countries.map((c) => (
                        <option key={c.name} value={c.name}>
                          {isArabic ? c.label.ar : c.label.en}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "العملة" : "Currency"}
                    </label>
                    <Input value={currency} readOnly className={isArabic ? "text-right" : "text-left"} />
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border">
                <div className="border-b bg-muted/30 px-5 py-4">
                  <div className="flex items-center gap-2">
                    <Landmark className="h-4 w-4 text-primary" />
                    <h3 className="font-semibold">
                      {isArabic ? "البيانات التجارية والضريبية" : "Commercial & Tax Information"}
                    </h3>
                  </div>
                </div>

                <div className="grid gap-4 p-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "السجل التجاري" : "Commercial Number"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "السجل التجاري" : "Commercial Number"}
                      value={commercialNumber}
                      onChange={(e) => setCommercialNumber(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "الرقم الضريبي" : "VAT Number"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "الرقم الضريبي" : "VAT Number"}
                      value={vatNumber}
                      onChange={(e) => setVatNumber(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border">
                <div className="border-b bg-muted/30 px-5 py-4">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-primary" />
                    <h3 className="font-semibold">
                      {isArabic ? "العنوان الوطني" : "National Address"}
                    </h3>
                  </div>
                </div>

                <div className="grid gap-4 p-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "رقم المبنى" : "Building Number"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "رقم المبنى" : "Building Number"}
                      value={buildingNumber}
                      onChange={(e) => setBuildingNumber(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "الشارع" : "Street"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "الشارع" : "Street"}
                      value={street}
                      onChange={(e) => setStreet(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "الحي" : "District"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "الحي" : "District"}
                      value={district}
                      onChange={(e) => setDistrict(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "الرمز البريدي" : "Postal Code"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "الرمز البريدي" : "Postal Code"}
                      value={postalCode}
                      onChange={(e) => setPostalCode(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "العنوان المختصر" : "Short Address"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "العنوان المختصر" : "Short Address"}
                      value={shortAddress}
                      onChange={(e) => setShortAddress(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border">
                <div className="border-b bg-muted/30 px-5 py-4">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary" />
                    <h3 className="font-semibold">
                      {isArabic ? "باقة الاشتراك" : "Subscription Plan"}
                    </h3>
                  </div>
                </div>

                <div className="p-5">
                  {plansLoading ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {isArabic ? "جارٍ تحميل الباقات..." : "Loading plans..."}
                    </div>
                  ) : plansError ? (
                    <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-600">
                      {plansError}
                    </div>
                  ) : (
                    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                      {plans.map((plan) => {
                        const planPrice =
                          billingCycle === "monthly"
                            ? normalizeNumber(plan.price_monthly)
                            : normalizeNumber(plan.price_yearly)

                        const isSelected = planId === String(plan.id)

                        return (
                          <button
                            key={plan.id}
                            type="button"
                            onClick={() => setPlanId(String(plan.id))}
                            className={`rounded-2xl border p-4 transition ${
                              isSelected
                                ? "border-primary bg-primary/5 shadow-sm"
                                : "hover:border-primary/40 hover:bg-muted/30"
                            } ${isArabic ? "text-right" : "text-left"}`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <div className="font-semibold">{plan.name}</div>
                                <div className="mt-1 text-sm text-muted-foreground">
                                  {formatMoney(planPrice, currency, locale)}
                                </div>
                              </div>

                              {isSelected ? (
                                <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                              ) : null}
                            </div>

                            {plan.description ? (
                              <div className="mt-3 text-xs text-muted-foreground">
                                {plan.description}
                              </div>
                            ) : null}

                            {plan.apps?.length > 0 ? (
                              <div className="mt-3 text-xs text-muted-foreground">
                                {isArabic ? "التطبيقات:" : "Apps:"} {plan.apps.join(", ")}
                              </div>
                            ) : null}

                            <div className="mt-4 flex flex-wrap gap-2">
                              <Badge variant="secondary" className="rounded-full">
                                {isArabic
                                  ? `الحد الأقصى للموظفين: ${normalizeNumber(plan.max_employees)}`
                                  : `Max Employees: ${normalizeNumber(plan.max_employees)}`}
                              </Badge>
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>

              <div className="rounded-2xl border">
                <div className="border-b bg-muted/30 px-5 py-4">
                  <div className="flex items-center gap-2">
                    <User2 className="h-4 w-4 text-primary" />
                    <h3 className="font-semibold">
                      {isArabic ? "مدير النظام الأساسي" : "Owner Admin"}
                    </h3>
                  </div>
                </div>

                <div className="grid gap-4 p-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "الاسم الأول" : "First Name"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "الاسم الأول" : "First Name"}
                      value={ownerFirstName}
                      onChange={(e) => setOwnerFirstName(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "اسم العائلة" : "Last Name"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "اسم العائلة" : "Last Name"}
                      value={ownerLastName}
                      onChange={(e) => setOwnerLastName(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "بريد المدير" : "Admin Email"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "بريد المدير" : "Admin Email"}
                      type="email"
                      value={ownerEmail}
                      onChange={(e) => setOwnerEmail(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Phone className="h-4 w-4" />
                      <span>{isArabic ? "جوال المدير" : "Admin Phone"}</span>
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "05xxxxxxxx" : "05xxxxxxxx"}
                      value={ownerPhone}
                      onChange={(e) => setOwnerPhone(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <div className="rounded-xl border border-primary/15 bg-primary/5 px-4 py-3 text-sm text-muted-foreground">
                      {isArabic
                        ? "سيُستخدم هذا الرقم لإشعارات واتساب الخاصة بصاحب الحساب أو الأدمن الأساسي."
                        : "This number will be used for WhatsApp notifications for the account owner / primary admin."}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "اسم المستخدم" : "Username"}
                    </label>
                    <Input
                      dir={isArabic ? "rtl" : "ltr"}
                      className={isArabic ? "text-right" : "text-left"}
                      placeholder={isArabic ? "اسم المستخدم" : "Username"}
                      value={ownerUsername}
                      onChange={(e) => setOwnerUsername(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <label className="text-sm text-muted-foreground">
                      {isArabic ? "كلمة المرور" : "Password"}
                    </label>

                    <div className="flex gap-2">
                      <Input
                        type="password"
                        dir={isArabic ? "rtl" : "ltr"}
                        className={isArabic ? "text-right" : "text-left"}
                        value={ownerPassword}
                        onChange={(e) => setOwnerPassword(e.target.value)}
                        placeholder={isArabic ? "كلمة المرور" : "Password"}
                      />

                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setOwnerPassword(generatePassword())}
                      >
                        {isArabic ? "توليد" : "Generate"}
                      </Button>
                    </div>

                    <div className="mt-3 h-2 overflow-hidden rounded bg-gray-200">
                      <div
                        className={`h-2 ${strength.color}`}
                        style={{ width: strength.width }}
                      />
                    </div>

                    <div className={`mt-2 text-xs ${strength.textClass}`}>
                      {isArabic ? "قوة كلمة المرور:" : "Strength:"} {strength.label}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6 xl:col-span-4">
          <Card>
            <CardHeader>
              <CardTitle>{isArabic ? "إعداد الفوترة" : "Billing Setup"}</CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <Button
                  type="button"
                  variant={billingCycle === "monthly" ? "default" : "outline"}
                  onClick={() => setBillingCycle("monthly")}
                  className={isArabic ? "justify-center" : "justify-start"}
                >
                  {isArabic ? "شهري" : "Monthly"}
                </Button>

                <Button
                  type="button"
                  variant={billingCycle === "yearly" ? "default" : "outline"}
                  onClick={() => setBillingCycle("yearly")}
                  className={isArabic ? "justify-center" : "justify-start"}
                >
                  {isArabic ? "سنوي" : "Yearly"}
                </Button>
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">
                  {isArabic ? "كود الخصم" : "Discount Code"}
                </label>
                <div className="flex gap-2">
                  <Input
                    dir={isArabic ? "rtl" : "ltr"}
                    className={isArabic ? "text-right" : "text-left"}
                    placeholder={isArabic ? "كود الخصم" : "Discount code"}
                    value={discountCode}
                    onChange={(e) => setDiscountCode(e.target.value)}
                  />
                  <Button type="button" variant="outline" onClick={applyDiscount}>
                    {isArabic ? "تطبيق" : "Apply"}
                  </Button>
                </div>
              </div>

              <div className="rounded-2xl border border-primary/15 bg-primary/5 p-4 text-sm text-muted-foreground">
                {isArabic
                  ? "سيبقى طلب التسجيل معلقًا حتى تؤكد بوابة الدفع نجاح العملية."
                  : "The registration request remains pending until the gateway confirms the payment successfully."}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{isArabic ? "اختر طريقة الدفع" : "Select Payment Method"}</CardTitle>
            </CardHeader>

            <CardContent className="space-y-3">
              <button
                type="button"
                onClick={() => setPaymentMethod("CREDIT_CARD")}
                className={`flex w-full items-center justify-between rounded-2xl border p-4 transition ${
                  paymentMethod === "CREDIT_CARD"
                    ? "border-primary bg-primary/5"
                    : "hover:bg-muted/40"
                } ${isArabic ? "text-right" : "text-left"}`}
              >
                <div className="flex items-center gap-3">
                  <CreditCard className="h-5 w-5" />
                  <div>
                    <div className="font-medium">
                      {isArabic ? "بطاقة ائتمانية" : "Credit Card"}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {isArabic
                        ? "دفع آمن عبر Tap"
                        : "Secure online payment via Tap"}
                    </div>
                  </div>
                </div>

                {paymentMethod === "CREDIT_CARD" ? (
                  <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                ) : null}
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("TAMARA")}
                className={`flex w-full items-center justify-between rounded-2xl border p-4 transition ${
                  paymentMethod === "TAMARA"
                    ? "border-primary bg-primary/5"
                    : "hover:bg-muted/40"
                } ${isArabic ? "text-right" : "text-left"}`}
              >
                <div className="flex items-center gap-3">
                  <Wallet className="h-5 w-5" />
                  <div>
                    <div className="font-medium">Tamara</div>
                    <div className="text-xs text-muted-foreground">
                      {isArabic ? "قسّم الدفع مع تمارا" : "Split payment with Tamara"}
                    </div>
                  </div>
                </div>

                {paymentMethod === "TAMARA" ? (
                  <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                ) : null}
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("BANK_TRANSFER")}
                className={`flex w-full items-center justify-between rounded-2xl border p-4 transition ${
                  paymentMethod === "BANK_TRANSFER"
                    ? "border-primary bg-primary/5"
                    : "hover:bg-muted/40"
                } ${isArabic ? "text-right" : "text-left"}`}
              >
                <div className="flex items-center gap-3">
                  <Landmark className="h-5 w-5" />
                  <div>
                    <div className="font-medium">
                      {isArabic ? "تحويل بنكي" : "Bank Transfer"}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {isArabic
                        ? "أنشئ الطلب ثم أكمل مع الإدارة المالية"
                        : "Create the request and continue with finance"}
                    </div>
                  </div>
                </div>

                {paymentMethod === "BANK_TRANSFER" ? (
                  <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                ) : null}
              </button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{isArabic ? "معاينة الفاتورة" : "Invoice Preview"}</CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
              {previewLoading || gatewayConfirming ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {gatewayConfirming
                    ? isArabic
                      ? "جارٍ إنهاء تأكيد الدفع..."
                      : "Finalizing payment confirmation..."
                    : isArabic
                    ? "جارٍ تحديث المعاينة..."
                    : "Updating preview..."}
                </div>
              ) : null}

              <div className="flex items-center gap-3 rounded-2xl border bg-muted/20 p-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-background">
                  <Image
                    src="/currency/sar.svg"
                    alt="SAR"
                    width={26}
                    height={26}
                    className="object-contain"
                  />
                </div>

                <div className={isArabic ? "text-right" : "text-left"}>
                  <div className="text-sm text-muted-foreground">
                    {isArabic ? "الإجمالي المستحق" : "Total Due"}
                  </div>
                  <div className="text-2xl font-bold">
                    {formatMoney(totalWithVat, currency, locale)}
                  </div>
                </div>
              </div>

              <div className="space-y-3 rounded-2xl border p-4">
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">{isArabic ? "الباقة" : "Plan"}</span>
                  <span className="font-medium">
                    {selectedPlan?.name || initialPlanName || "-"}
                  </span>
                </div>

                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">
                    {isArabic ? "دورة الفوترة" : "Billing Cycle"}
                  </span>
                  <span className="font-medium capitalize">
                    {billingCycle === "monthly"
                      ? isArabic
                        ? "شهري"
                        : "monthly"
                      : isArabic
                      ? "سنوي"
                      : "yearly"}
                  </span>
                </div>

                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">
                    {isArabic ? "طريقة الدفع" : "Payment Method"}
                  </span>
                  <span className="font-medium">{getMethodLabel(paymentMethod, locale)}</span>
                </div>

                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">{isArabic ? "السعر" : "Price"}</span>
                  <span className="font-medium">
                    {formatMoney(basePrice, currency, locale)}
                  </span>
                </div>

                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">{isArabic ? "الخصم" : "Discount"}</span>
                  <span className="font-medium">
                    - {formatMoney(discountAmountPreview, currency, locale)}
                  </span>
                </div>

                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">
                    {isArabic ? "الإجمالي قبل الضريبة" : "Subtotal"}
                  </span>
                  <span className="font-medium">
                    {formatMoney(subtotal, currency, locale)}
                  </span>
                </div>

                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground">
                    {isArabic ? "ضريبة القيمة المضافة 15%" : "VAT 15%"}
                  </span>
                  <span className="font-medium">
                    {formatMoney(vatAmount, currency, locale)}
                  </span>
                </div>

                <div className="border-t pt-3">
                  <div className="flex justify-between gap-4 text-lg font-bold">
                    <span>{isArabic ? "الإجمالي شامل الضريبة" : "Total + VAT"}</span>
                    <span>{formatMoney(totalWithVat, currency, locale)}</span>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-primary/15 bg-primary/5 p-4 text-sm text-muted-foreground">
                <div className="mb-1 flex items-center gap-2 font-medium text-foreground">
                  <ShieldCheck className="h-4 w-4" />
                  {isArabic
                    ? `الطريقة المختارة: ${getMethodLabel(paymentMethod, locale)}`
                    : `Selected Method: ${getMethodLabel(paymentMethod, locale)}`}
                </div>
                <div>{getMethodDescription(paymentMethod, locale)}</div>
              </div>

              <div className="grid gap-4 md:grid-cols-[1fr_110px]">
                <div className="rounded-2xl border p-4 text-sm text-muted-foreground">
                  {isArabic
                    ? "من المتوقع أن يرسل النظام إشعارات التسجيل والدفع عبر البريد الإلكتروني بعد نجاح إنشاء الطلب وتقدم حالة الدفع."
                    : "The backend flow is expected to send registration/payment notifications by email after successful request creation and gateway progress."}
                </div>

                <div className="flex flex-col items-center justify-center rounded-2xl border bg-white p-4">
                  <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
                    <QrCode className="h-4 w-4" />
                    QR
                  </div>

                  <div className="flex h-[70px] w-[70px] items-center justify-center rounded-xl border bg-muted/20">
                    <QrCode className="h-8 w-8 text-muted-foreground" />
                  </div>
                </div>
              </div>

              {lastActionMessage ? (
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                  {lastActionMessage}
                </div>
              ) : null}

              <div className="flex flex-col gap-3">
                <Button
                  onClick={createRegistrationDraft}
                  disabled={loading || plansLoading || gatewayConfirming}
                  className="w-full gap-2"
                >
                  {loading || gatewayConfirming ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : null}

                  {loading
                    ? isArabic
                      ? "جارٍ المعالجة..."
                      : "Processing..."
                    : gatewayConfirming
                    ? isArabic
                      ? "جارٍ تأكيد الدفع..."
                      : "Confirming Payment..."
                    : paymentMethod === "BANK_TRANSFER"
                    ? isArabic
                      ? "إنشاء الطلب"
                      : "Create Request"
                    : isArabic
                    ? `المتابعة إلى ${getMethodLabel(paymentMethod, locale)}`
                    : `Continue to ${getMethodLabel(paymentMethod, locale)}`}
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push("/#pricing")}
                  className="w-full"
                  disabled={loading || gatewayConfirming}
                >
                  {isArabic ? "إلغاء" : "Cancel"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default function RegisterCompanyPage() {
  return (
    <Suspense fallback={<RegisterCompanyPageFallback />}>
      <RegisterCompanyPageContent />
    </Suspense>
  )
}