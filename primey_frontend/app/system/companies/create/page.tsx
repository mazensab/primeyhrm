"use client"

import Image from "next/image"
import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import { toast } from "sonner"

import {
  Building2,
  MapPin,
  Landmark,
  FileText,
  CreditCard,
  ShieldCheck,
  Phone,
  Wallet,
  Loader2,
  ReceiptText,
  CheckCircle2,
} from "lucide-react"

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://mhamcloud.com"

const API = API_BASE.endsWith("/api") ? API_BASE : `${API_BASE}/api`

type BillingCycle = "monthly" | "yearly"
type PaymentMethod =
  | "CASH"
  | "BANK_TRANSFER"
  | "CREDIT_CARD"
  | "TAMARA"

type Plan = {
  id: number | string
  name?: string
  description?: string
  price_monthly?: number | string | null
  price_yearly?: number | string | null
  apps?: string[]
}

type BillingPreview = {
  price?: number | string
  discount?: number | string
  subtotal?: number | string
  vat?: number | string
  total?: number | string
}

type DraftCreateResponse = {
  draft_id?: number | string
  checkout_url?: string
  payment_url?: string
  redirect_url?: string
  details?: string
  error?: string
  message?: string
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

async function ensureCsrf() {
  try {
    await fetch(`${API}/auth/csrf/`, {
      method: "GET",
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

function passwordStrength(password: string) {
  let score = 0

  if (password.length >= 8) score++
  if (/[A-Z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  if (score <= 1) {
    return { label: "Weak", color: "bg-red-500", width: "25%" }
  }

  if (score === 2) {
    return { label: "Medium", color: "bg-yellow-500", width: "50%" }
  }

  if (score === 3) {
    return { label: "Strong", color: "bg-green-500", width: "75%" }
  }

  return { label: "Very Strong", color: "bg-emerald-600", width: "100%" }
}

function normalizeNumber(value: unknown): number {
  if (typeof value === "number" && !Number.isNaN(value)) return value
  const parsed = Number(value ?? 0)
  return Number.isNaN(parsed) ? 0 : parsed
}

function formatMoney(value: unknown, currency = "SAR") {
  const amount = normalizeNumber(value)

  return `${new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)} ${currency}`
}

function getMethodLabel(method: PaymentMethod) {
  switch (method) {
    case "CASH":
      return "Cash"
    case "BANK_TRANSFER":
      return "Bank Transfer"
    case "CREDIT_CARD":
      return "Credit Card"
    case "TAMARA":
      return "Tamara"
    default:
      return method
  }
}

function getMethodDescription(method: PaymentMethod) {
  switch (method) {
    case "CASH":
      return "Manual cash payment flow."
    case "BANK_TRANSFER":
      return "Manual bank transfer verification flow."
    case "CREDIT_CARD":
      return "Secure online card payment via Tap."
    case "TAMARA":
      return "Split payment with Tamara."
    default:
      return ""
  }
}

const countries = [
  { name: "Saudi Arabia", currency: "SAR" },
  { name: "UAE", currency: "AED" },
  { name: "Egypt", currency: "EGP" },
]

export default function CreateCompanyPage() {
  const router = useRouter()

  /* ============================
     COMPANY
  ============================ */
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [phone, setPhone] = useState("")
  const [city, setCity] = useState("")
  const [country, setCountry] = useState("")
  const [currency, setCurrency] = useState("SAR")
  const [commercialNumber, setCommercialNumber] = useState("")
  const [vatNumber, setVatNumber] = useState("")
  const [buildingNumber, setBuildingNumber] = useState("")
  const [street, setStreet] = useState("")
  const [district, setDistrict] = useState("")
  const [postalCode, setPostalCode] = useState("")
  const [shortAddress, setShortAddress] = useState("")

  /* ============================
     PLAN
  ============================ */
  const [plans, setPlans] = useState<Plan[]>([])
  const [planId, setPlanId] = useState("")
  const [plansLoading, setPlansLoading] = useState(true)
  const [billingCycle, setBillingCycle] = useState<BillingCycle>("monthly")

  /* ============================
     DISCOUNT
  ============================ */
  const [discountCode, setDiscountCode] = useState("")
  const [preview, setPreview] = useState<BillingPreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  /* ============================
     ADMIN
  ============================ */
  const [ownerFirstName, setOwnerFirstName] = useState("")
  const [ownerLastName, setOwnerLastName] = useState("")
  const [ownerEmail, setOwnerEmail] = useState("")
  const [ownerPhone, setOwnerPhone] = useState("")
  const [ownerPassword, setOwnerPassword] = useState("")
  const [ownerUsername, setOwnerUsername] = useState("")

  /* ============================
     STATE
  ============================ */
  const [loading, setLoading] = useState(false)

  const strength = passwordStrength(ownerPassword)

  /* ============================
     PAYMENT
  ============================ */
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("CASH")

  /* ============================
     LOAD PLANS
  ============================ */
  useEffect(() => {
    async function loadPlans() {
      try {
        const res = await fetch(`${API}/system/plans/admin/`, {
          credentials: "include",
        })

        const data = await res.json()

        setPlans(Array.isArray(data) ? data : data.plans || data.results || [])
      } catch {
        toast.error("Failed to load plans")
      } finally {
        setPlansLoading(false)
      }
    }

    loadPlans()
  }, [])

  /* ============================
     COUNTRY
  ============================ */
  const handleCountryChange = (value: string) => {
    setCountry(value)

    const found = countries.find((c) => c.name === value)

    if (found) {
      setCurrency(found.currency)
    }
  }

  /* ============================
     PLAN
  ============================ */
  const selectedPlan = useMemo(
    () => plans.find((p) => String(p.id) === planId),
    [plans, planId]
  )

  /* ============================
     PREVIEW API
  ============================ */
  useEffect(() => {
    if (!planId) return

    async function loadPreview() {
      try {
        setPreviewLoading(true)

        const params = new URLSearchParams({
          plan_id: planId,
          billing_cycle: billingCycle,
        })

        if (discountCode) {
          params.append("discount_code", discountCode)
        }

        const res = await fetch(`${API}/system/billing/preview/?${params}`, {
          credentials: "include",
        })

        const data = await res.json()
        setPreview(data)
      } catch {
        console.error("Preview failed")
      } finally {
        setPreviewLoading(false)
      }
    }

    loadPreview()
  }, [planId, billingCycle, discountCode])

  const basePrice = normalizeNumber(preview?.price ?? 0)
  const discountAmountPreview = normalizeNumber(preview?.discount ?? 0)
  const finalPrice = normalizeNumber(preview?.subtotal ?? 0)
  const vatAmount = normalizeNumber(preview?.vat ?? 0)
  const totalWithVat = normalizeNumber(preview?.total ?? 0)

  /* ============================
     CHECK DISCOUNT
  ============================ */
  const applyDiscount = async () => {
    if (!discountCode) {
      toast.error("Enter discount code")
      return
    }

    if (!planId) {
      toast.error("Select plan first")
      return
    }

    try {
      const params = new URLSearchParams({
        plan_id: planId,
        billing_cycle: billingCycle,
        discount_code: discountCode,
      })

      const res = await fetch(`${API}/system/billing/preview/?${params}`, {
        credentials: "include",
      })

      const data = await res.json()

      if (!res.ok) {
        toast.error("Invalid discount code")
        return
      }

      setPreview(data)
      toast.success("Discount applied")
    } catch {
      toast.error("Failed to validate code")
    }
  }

  /* ============================
     START PAYMENT AFTER DRAFT
  ============================ */
  const startPaymentAfterDraft = async (args: {
    currentDraftId: string
    selectedPaymentMethod: PaymentMethod
    csrfToken: string
  }) => {
    const { currentDraftId, selectedPaymentMethod, csrfToken } = args

    if (
      selectedPaymentMethod === "CASH" ||
      selectedPaymentMethod === "BANK_TRANSFER"
    ) {
      toast.success("Draft ready for manual payment review")
      router.push(`/system/payments/${currentDraftId}`)
      return true
    }

    if (selectedPaymentMethod === "CREDIT_CARD") {
      try {
        const res = await fetch(`${API}/system/payments/tap/create-checkout/`, {
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

        const data: StartPaymentResponse | null = await res
          .json()
          .catch(() => null)

        if (!res.ok || !data) {
          toast.error(data?.message || "Failed to create Tap checkout")
          return false
        }

        const checkoutUrl =
          data.checkout_url ||
          data.payment_url ||
          data.redirect_url ||
          data.url ||
          null

        if (checkoutUrl && typeof window !== "undefined") {
          toast.success("Redirecting to Tap payment gateway...")
          window.location.href = checkoutUrl
          return true
        }

        toast.error("No Tap checkout URL returned")
        return false
      } catch (error) {
        console.error("Tap checkout start error:", error)
        toast.error("Failed to start Tap payment")
        return false
      }
    }

    try {
      const res = await fetch(`${API}/system/onboarding/start-payment/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || "",
        },
        body: JSON.stringify({
          draft_id: currentDraftId,
          payment_method: selectedPaymentMethod,
          billing_cycle: billingCycle,
          discount_code: discountCode || null,
        }),
      })

      const data: StartPaymentResponse | null = await res.json().catch(() => null)

      if (!res.ok || !data) {
        toast.error("Failed to start payment")
        return false
      }

      const checkoutUrl =
        data.checkout_url ||
        data.payment_url ||
        data.redirect_url ||
        data.url ||
        null

      if (checkoutUrl && typeof window !== "undefined") {
        toast.success("Redirecting to payment gateway...")
        window.location.href = checkoutUrl
        return true
      }

      toast.success("Draft ready for payment")
      router.push(`/system/payments/${currentDraftId}`)
      return true
    } catch (error) {
      console.error("Generic payment start error:", error)
      toast.error("Unexpected error while starting payment")
      return false
    }
  }

  /* ============================
     CREATE DRAFT
  ============================ */
  const createCompany = async () => {
    if (!name.trim()) {
      toast.error("Company name required")
      return
    }

    if (!planId) {
      toast.error("Select plan")
      return
    }

    if (!ownerEmail.trim() || !ownerPassword.trim()) {
      toast.error("Admin email/password required")
      return
    }

    if (!ownerPhone.trim()) {
      toast.error("Admin phone required")
      return
    }

    if (!ownerUsername.trim()) {
      toast.error("Username required")
      return
    }

    setLoading(true)

    try {
      const csrftoken = (await ensureCsrf()) || getCookie("csrftoken")

      if (!csrftoken) {
        toast.error("CSRF token not found")
        setLoading(false)
        return
      }

      const payload = {
        company_name: name,
        email,
        phone,
        city,
        country,
        currency,
        commercial_number: commercialNumber,
        vat_number: vatNumber,
        national_address: {
          building_number: buildingNumber,
          street,
          district,
          city,
          postal_code: postalCode,
          short_address: shortAddress,
        },

        plan_id: planId,
        duration: billingCycle,
        discount_code: discountCode || null,
        payment_method: paymentMethod,

        admin_username: ownerUsername,
        admin_name: `${ownerFirstName} ${ownerLastName}`.trim(),
        admin_email: ownerEmail,
        admin_phone: ownerPhone,
        admin_password: ownerPassword,
      }

      const res = await fetch(`${API}/system/onboarding/create-draft/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify(payload),
      })

      const data: DraftCreateResponse = await res.json()

      if (!res.ok || !data?.draft_id) {
        toast.error(data.details || data.error || "Failed")
        setLoading(false)
        return
      }

      toast.success("Draft created")

      const confirmRes = await fetch(`${API}/system/onboarding/confirm-draft/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({
          draft_id: data.draft_id,
        }),
      })

      const confirmData = await confirmRes.json().catch(() => null)

      if (!confirmRes.ok) {
        toast.error(confirmData?.error || "Failed to confirm draft")
        setLoading(false)
        return
      }

      toast.success("Draft ready")

      const paymentStarted = await startPaymentAfterDraft({
        currentDraftId: String(data.draft_id),
        selectedPaymentMethod: paymentMethod,
        csrfToken: csrftoken,
      })

      if (!paymentStarted) {
        router.push(`/system/payments/${data.draft_id}`)
      }
    } catch (error) {
      console.error(error)
      toast.error("Unexpected error")
    } finally {
      setLoading(false)
    }
  }

  /* ============================
     UI
  ============================ */
  return (
    <div className="max-w-6xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold tracking-tight">
          Create Company
        </h1>
        <p className="text-sm text-muted-foreground">
          Create a new company with commercial data, national address, plan, billing setup, and owner admin.
        </p>
      </div>

      <Card className="border shadow-sm">
        <CardHeader className="border-b bg-muted/20">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Building2 className="h-5 w-5" />
            Company Information
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-8 pt-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
              <Building2 className="h-4 w-4" />
              Basic Information
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Company Name</label>
                <Input
                  placeholder="Company Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Company Email</label>
                <Input
                  placeholder="Company Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Phone</label>
                <Input
                  placeholder="Phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">City</label>
                <Input
                  placeholder="City"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Country</label>
                <select
                  className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  value={country}
                  onChange={(e) => handleCountryChange(e.target.value)}
                >
                  <option value="">Select Country</option>
                  {countries.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Currency</label>
                <Input value={currency} readOnly />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
              <Landmark className="h-4 w-4" />
              Commercial & Tax Information
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Commercial Number</label>
                <Input
                  placeholder="Commercial Number"
                  value={commercialNumber}
                  onChange={(e) => setCommercialNumber(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">VAT Number</label>
                <Input
                  placeholder="VAT Number"
                  value={vatNumber}
                  onChange={(e) => setVatNumber(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
              <MapPin className="h-4 w-4" />
              National Address
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Building Number</label>
                <Input
                  placeholder="Building Number"
                  value={buildingNumber}
                  onChange={(e) => setBuildingNumber(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Street</label>
                <Input
                  placeholder="Street"
                  value={street}
                  onChange={(e) => setStreet(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">District</label>
                <Input
                  placeholder="District"
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Postal Code</label>
                <Input
                  placeholder="Postal Code"
                  value={postalCode}
                  onChange={(e) => setPostalCode(e.target.value)}
                />
              </div>

              <div className="space-y-2 md:col-span-2">
                <label className="text-sm text-muted-foreground">Short Address</label>
                <Input
                  placeholder="Short Address"
                  value={shortAddress}
                  onChange={(e) => setShortAddress(e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border shadow-sm">
        <CardHeader className="border-b bg-muted/20">
          <CardTitle className="flex items-center gap-2 text-lg">
            <CreditCard className="h-5 w-5" />
            Subscription Plan
          </CardTitle>
        </CardHeader>

        <CardContent className="pt-6">
          {plansLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading plans...
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {plans.map((plan) => (
                <div
                  key={String(plan.id)}
                  onClick={() => setPlanId(String(plan.id))}
                  className={`cursor-pointer rounded-xl border p-4 transition ${
                    planId === String(plan.id)
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "hover:border-gray-400"
                  }`}
                >
                  <div className="font-semibold">{plan.name}</div>

                  <div className="mt-1 text-sm text-muted-foreground">
                    {billingCycle === "monthly"
                      ? formatMoney(plan.price_monthly ?? 0, currency)
                      : formatMoney(plan.price_yearly ?? 0, currency)}
                  </div>

                  {plan.apps && (
                    <div className="mt-3 text-xs text-muted-foreground">
                      Apps: {plan.apps.join(", ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border shadow-sm">
        <CardHeader className="border-b bg-muted/20">
          <CardTitle className="flex items-center gap-2 text-lg">
            <ReceiptText className="h-5 w-5" />
            Billing
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4 pt-6">
          <div className="flex flex-wrap gap-2">
            <Button
              variant={billingCycle === "monthly" ? "default" : "outline"}
              onClick={() => setBillingCycle("monthly")}
            >
              Monthly
            </Button>

            <Button
              variant={billingCycle === "yearly" ? "default" : "outline"}
              onClick={() => setBillingCycle("yearly")}
            >
              Yearly
            </Button>
          </div>

          <div className="flex flex-col gap-3 md:flex-row">
            <Input
              placeholder="Discount code"
              value={discountCode}
              onChange={(e) => setDiscountCode(e.target.value)}
            />

            <Button
              variant="outline"
              onClick={applyDiscount}
              className="md:w-fit"
            >
              Apply Discount
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="border shadow-sm">
        <CardHeader className="border-b bg-muted/20">
          <CardTitle className="flex items-center gap-2 text-lg">
            <CreditCard className="h-5 w-5" />
            Payment Method
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-5 pt-6">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            <div
              onClick={() => setPaymentMethod("CASH")}
              className={`cursor-pointer rounded-xl border p-4 transition ${
                paymentMethod === "CASH"
                  ? "border-primary bg-primary/5"
                  : "hover:border-gray-400"
              }`}
            >
              <div className="font-medium">Cash</div>
              <div className="mt-1 text-xs text-muted-foreground">
                Manual cash payment flow
              </div>
            </div>

            <div
              onClick={() => setPaymentMethod("BANK_TRANSFER")}
              className={`cursor-pointer rounded-xl border p-4 transition ${
                paymentMethod === "BANK_TRANSFER"
                  ? "border-primary bg-primary/5"
                  : "hover:border-gray-400"
              }`}
            >
              <div className="font-medium">Bank Transfer</div>
              <div className="mt-1 text-xs text-muted-foreground">
                Manual bank transfer verification
              </div>
            </div>

            <div
              onClick={() => setPaymentMethod("CREDIT_CARD")}
              className={`cursor-pointer rounded-xl border p-4 transition ${
                paymentMethod === "CREDIT_CARD"
                  ? "border-primary bg-primary/5"
                  : "hover:border-gray-400"
              }`}
            >
              <div className="font-medium">Credit Card</div>
              <div className="mt-1 text-xs text-muted-foreground">
                Powered by Tap
              </div>
            </div>

            <div
              onClick={() => setPaymentMethod("TAMARA")}
              className={`cursor-pointer rounded-xl border p-4 transition ${
                paymentMethod === "TAMARA"
                  ? "border-primary bg-primary/5"
                  : "hover:border-gray-400"
              }`}
            >
              <div className="flex items-center gap-2 font-medium">
                <Wallet className="h-4 w-4" />
                Tamara
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                Split payment via Tamara
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-primary/15 bg-primary/5 p-4 text-sm text-muted-foreground">
            <div className="mb-1 flex items-center gap-2 font-medium text-foreground">
              <CheckCircle2 className="h-4 w-4" />
              Selected Method: {getMethodLabel(paymentMethod)}
            </div>
            <div>{getMethodDescription(paymentMethod)}</div>
          </div>
        </CardContent>
      </Card>

      <Card className="border shadow-sm">
        <CardHeader className="border-b bg-muted/20">
          <CardTitle className="flex items-center gap-2 text-lg">
            <FileText className="h-5 w-5" />
            Invoice Preview
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4 pt-6">
          {previewLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Updating invoice preview...
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

            <div>
              <div className="text-sm text-muted-foreground">Total Due</div>
              <div className="text-2xl font-bold">
                {formatMoney(totalWithVat, currency)}
              </div>
            </div>
          </div>

          <div className="space-y-3 rounded-2xl border p-4">
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Plan</span>
              <span className="font-medium">{selectedPlan?.name || "-"}</span>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Billing Cycle</span>
              <span className="font-medium">{billingCycle}</span>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Payment Method</span>
              <span className="font-medium">{getMethodLabel(paymentMethod)}</span>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Price</span>
              <span className="font-medium">{formatMoney(basePrice, currency)}</span>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Discount</span>
              <span className="font-medium">- {formatMoney(discountAmountPreview, currency)}</span>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Subtotal</span>
              <span className="font-medium">{formatMoney(finalPrice, currency)}</span>
            </div>

            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">VAT 15%</span>
              <span className="font-medium">{formatMoney(vatAmount, currency)}</span>
            </div>

            <div className="flex justify-between gap-4 border-t pt-3 text-lg font-bold">
              <span>Total + VAT</span>
              <span>{formatMoney(totalWithVat, currency)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border shadow-sm">
        <CardHeader className="border-b bg-muted/20">
          <CardTitle className="flex items-center gap-2 text-lg">
            <ShieldCheck className="h-5 w-5" />
            Owner Admin
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6 pt-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">First Name</label>
              <Input
                placeholder="First Name"
                value={ownerFirstName}
                onChange={(e) => setOwnerFirstName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Last Name</label>
              <Input
                placeholder="Last Name"
                value={ownerLastName}
                onChange={(e) => setOwnerLastName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Admin Email</label>
              <Input
                placeholder="Admin Email"
                type="email"
                value={ownerEmail}
                onChange={(e) => setOwnerEmail(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Phone className="h-4 w-4" />
                <span>Admin Phone</span>
              </label>
              <Input
                placeholder="05xxxxxxxx"
                value={ownerPhone}
                onChange={(e) => setOwnerPhone(e.target.value)}
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <div className="rounded-xl border border-primary/15 bg-primary/5 px-4 py-3 text-sm text-muted-foreground">
                This number will be used for WhatsApp notifications for the company admin.
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Username</label>
              <Input
                placeholder="Username"
                value={ownerUsername}
                onChange={(e) => setOwnerUsername(e.target.value)}
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <label className="text-sm text-muted-foreground">Password</label>

              <div className="flex gap-2">
                <Input
                  type="password"
                  value={ownerPassword}
                  onChange={(e) => setOwnerPassword(e.target.value)}
                  placeholder="Password"
                />

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setOwnerPassword(generatePassword())}
                >
                  Generate
                </Button>
              </div>

              <div className="mt-3 h-2 overflow-hidden rounded bg-gray-200">
                <div
                  className={`h-2 ${strength.color}`}
                  style={{ width: strength.width }}
                />
              </div>

              <div className="mt-2 text-xs text-muted-foreground">
                Strength: {strength.label}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 pt-2">
            <Button onClick={createCompany} disabled={loading}>
              {loading ? "Creating..." : "Create Company"}
            </Button>

            <Button variant="outline" onClick={() => router.back()}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}