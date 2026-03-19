"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import {
  CheckCircle2,
  Loader2,
  ReceiptText,
  RefreshCw,
  AlertTriangle,
} from "lucide-react"
import { toast } from "sonner"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

const API_BASE = "http://localhost:8000/api"

type LookupSuccessPayload = {
  success: true
  status: "resolved"
  source?: string
  tap_id?: string
  invoice_id?: number
  invoice_number?: string
  invoice_status?: string
  company_id?: number | null
  company_name?: string | null
  redirect_url?: string
}

type LookupPendingPayload = {
  success: true
  status: "pending"
  source?: string
  tap_id?: string
  draft_id?: number
  draft_status?: string
  message?: string
  retry_after_ms?: number
}

type LookupNotFoundPayload = {
  success: false
  status: "not_found"
  tap_id?: string
  message?: string
}

type LookupErrorPayload = {
  success: false
  status: "error"
  message?: string
}

type LookupPayload =
  | LookupSuccessPayload
  | LookupPendingPayload
  | LookupNotFoundPayload
  | LookupErrorPayload

export default function TapPaymentSuccessPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const tapId = useMemo(() => {
    return (searchParams.get("tap_id") || "").trim()
  }, [searchParams])

  const [loading, setLoading] = useState(true)
  const [attempt, setAttempt] = useState(0)
  const [message, setMessage] = useState("جارِ التحقق من عملية الدفع...")
  const [resolvedInvoiceNumber, setResolvedInvoiceNumber] = useState("")
  const [debugSource, setDebugSource] = useState("")
  const [errorState, setErrorState] = useState("")
  const redirectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const hasShownSuccessToastRef = useRef(false)

  useEffect(() => {
    return () => {
      if (redirectTimerRef.current) {
        clearTimeout(redirectTimerRef.current)
      }
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (!tapId) {
      setLoading(false)
      setErrorState("لم يتم العثور على tap_id في رابط نجاح الدفع.")
      setMessage("تعذر التحقق من العملية لأن معرف الدفع غير موجود.")
      return
    }

    let isMounted = true

    async function resolvePayment(currentAttempt: number) {
      try {
        if (!isMounted) return

        setLoading(true)
        setErrorState("")
        setMessage(
          currentAttempt === 0
            ? "جارِ التحقق من عملية الدفع..."
            : `جارِ إعادة التحقق من العملية... (${currentAttempt + 1})`
        )

        const response = await fetch(
          `${API_BASE}/system/payments/tap/success-lookup/?tap_id=${encodeURIComponent(tapId)}`,
          {
            method: "GET",
            credentials: "include",
            cache: "no-store",
          }
        )

        const data: LookupPayload = await response.json()

        if (!isMounted) return

        if (response.status === 200 && data.status === "resolved" && data.success) {
          const redirectUrl = data.redirect_url || ""
          const invoiceNumber = data.invoice_number || ""

          setResolvedInvoiceNumber(invoiceNumber)
          setDebugSource(data.source || "")
          setMessage("تم التحقق من الدفع بنجاح. جارِ تحويلك إلى الفاتورة...")
          setLoading(false)

          if (!hasShownSuccessToastRef.current) {
            hasShownSuccessToastRef.current = true
            toast.success("تم تأكيد الدفع بنجاح")
          }

          if (redirectUrl) {
            redirectTimerRef.current = setTimeout(() => {
              router.replace(redirectUrl)
            }, 1200)
            return
          }

          setErrorState("تم العثور على الفاتورة لكن رابط التحويل غير متوفر.")
          return
        }

        if (response.status === 202 && data.status === "pending" && data.success) {
          const retryAfterMs =
            typeof data.retry_after_ms === "number" && data.retry_after_ms > 0
              ? data.retry_after_ms
              : 2500

          setDebugSource(data.source || "")
          setMessage(
            data.message || "تم استلام عملية الدفع، وما زال النظام يربط الفاتورة. سيتم إعادة المحاولة تلقائيًا..."
          )
          setLoading(true)

          retryTimerRef.current = setTimeout(() => {
            setAttempt((prev) => prev + 1)
          }, retryAfterMs)

          return
        }

        if (response.status === 404 && data.status === "not_found") {
          setLoading(false)
          setErrorState(data.message || "لم يتم العثور على فاتورة مرتبطة بهذه العملية.")
          setMessage("لم يتمكن النظام من ربط tap_id بفاتورة حتى الآن.")
          return
        }

        setLoading(false)
        setErrorState(data.message || "حدث خطأ أثناء التحقق من عملية الدفع.")
        setMessage("تعذر إكمال التحقق من الدفع.")
      } catch (error) {
        console.error("Tap success lookup error:", error)
        if (!isMounted) return

        setLoading(false)
        setErrorState("فشل الاتصال بخدمة التحقق من نجاح الدفع.")
        setMessage("تعذر الاتصال بالخادم أثناء التحقق من العملية.")
        toast.error("فشل التحقق من نجاح الدفع")
      }
    }

    resolvePayment(attempt)

    return () => {
      isMounted = false
    }
  }, [attempt, router, tapId])

  function handleRetryNow() {
    if (!tapId) {
      toast.error("tap_id غير موجود")
      return
    }

    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current)
    }

    setAttempt((prev) => prev + 1)
  }

  function handleGoInvoices() {
    router.push("/system/invoices")
  }

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-3xl items-center justify-center p-6">
      <Card className="w-full rounded-3xl border shadow-sm">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            {loading ? (
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            ) : errorState ? (
              <AlertTriangle className="h-8 w-8 text-amber-600" />
            ) : (
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            )}
          </div>

          <div className="space-y-2">
            <CardTitle className="text-2xl font-bold">
              {loading
                ? "جاري التحقق من الدفع"
                : errorState
                ? "تعذر إكمال التحقق"
                : "تم الدفع بنجاح"}
            </CardTitle>

            <p className="text-sm text-muted-foreground">
              {message}
            </p>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="rounded-2xl border bg-muted/20 p-4 text-sm">
            <div className="flex items-center justify-between gap-3 border-b pb-3">
              <span className="text-muted-foreground">Tap ID</span>
              <span className="break-all font-medium">{tapId || "-"}</span>
            </div>

            <div className="mt-3 flex items-center justify-between gap-3">
              <span className="text-muted-foreground">الحالة</span>
              <span className="font-medium">
                {loading ? "PROCESSING" : errorState ? "ERROR" : "RESOLVED"}
              </span>
            </div>

            {resolvedInvoiceNumber ? (
              <div className="mt-3 flex items-center justify-between gap-3">
                <span className="text-muted-foreground">رقم الفاتورة</span>
                <span className="font-medium">{resolvedInvoiceNumber}</span>
              </div>
            ) : null}

            {debugSource ? (
              <div className="mt-3 flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Source</span>
                <span className="font-medium">{debugSource}</span>
              </div>
            ) : null}
          </div>

          {loading ? (
            <div className="rounded-2xl border border-blue-200 bg-blue-50/70 p-4 text-sm text-blue-900">
              يتم الآن مطابقة العملية مع الفاتورة داخل النظام. سيتم تحويلك تلقائيًا فور اكتمال الربط.
            </div>
          ) : null}

          {errorState ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-4 text-sm text-amber-900">
              {errorState}
            </div>
          ) : null}

          <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Button
              onClick={handleRetryNow}
              variant="outline"
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              إعادة التحقق الآن
            </Button>

            {resolvedInvoiceNumber ? (
              <Button
                onClick={() => router.push(`/system/invoices/${resolvedInvoiceNumber}`)}
                className="gap-2"
              >
                <ReceiptText className="h-4 w-4" />
                فتح الفاتورة
              </Button>
            ) : (
              <Button
                onClick={handleGoInvoices}
                className="gap-2"
              >
                <ReceiptText className="h-4 w-4" />
                الذهاب إلى الفواتير
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}