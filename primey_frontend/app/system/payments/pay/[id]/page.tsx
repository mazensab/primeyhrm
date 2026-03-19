"use client"

import Image from "next/image"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import QRCode from "react-qr-code"

import {
  Card,
  CardContent,
} from "@/components/ui/card"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface PaymentDetail {
  id: number
  amount: number
  currency: string
  method: string
  status: string
  paid_at: string
  reference?: string

  company?: {
    id: number
    name: string
  }

  invoice?: {
    id: number
    number: string
    status: string
  }
}

export default function PaymentDetailsPage() {
  const params = useParams()
  const paymentId = Array.isArray(params.id) ? params.id[0] : params.id

  const [payment, setPayment] = useState<PaymentDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchPayment() {
      try {
        const res = await fetch(
          `http://localhost:8000/api/system/payments/${paymentId}/`,
          { credentials: "include" }
        )

        if (!res.ok) {
          setPayment(null)
          return
        }

        const data = await res.json()
        setPayment(data)
      } catch (error) {
        console.error("Failed to fetch payment details:", error)
        setPayment(null)
      } finally {
        setLoading(false)
      }
    }

    if (paymentId) {
      fetchPayment()
    } else {
      setLoading(false)
    }
  }, [paymentId])

  if (loading) {
    return <div className="p-6">Loading receipt...</div>
  }

  if (!payment) {
    return <div className="p-6">Receipt not found</div>
  }

  return (
    <div className="receipt-area mx-auto max-w-3xl space-y-8">
      {/* =========================
      LOGO CENTER
      ========================= */}

      <div className="flex justify-center">
        <Image
          src="/logo/primey.svg"
          alt="Primey Logo"
          width={200}
          height={60}
          className="logo-large"
          priority
        />
      </div>

      <div className="text-center">
        <h2 className="text-xl font-semibold">
          Payment Receipt
        </h2>

        <p className="text-sm text-muted-foreground">
          Receipt #{payment.id}
        </p>
      </div>

      {/* =========================
      Receipt Body
      ========================= */}

      <Card>
        <CardContent className="space-y-6 p-8">
          <div className="flex justify-between">
            <span className="text-muted-foreground">
              Company
            </span>

            <span className="font-medium">
              {payment.company?.name || "-"}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-muted-foreground">
              Invoice
            </span>

            <span>
              {payment.invoice?.number || "-"}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-muted-foreground">
              Payment Method
            </span>

            <span>
              {payment.method}
            </span>
          </div>

          <div className="flex justify-between text-lg font-semibold">
            <span>
              Amount
            </span>

            <div className="flex items-center gap-2">
              <Image
                src="/currency/sar.svg"
                alt="Saudi Riyal"
                width={20}
                height={20}
                className="h-5 w-5"
              />

              <span>
                {payment.amount} {payment.currency || "SAR"}
              </span>
            </div>
          </div>

          <div className="flex justify-between">
            <span className="text-muted-foreground">
              Payment Date
            </span>

            <span>
              {payment.paid_at ? new Date(payment.paid_at).toLocaleString() : "-"}
            </span>
          </div>

          {payment.reference && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">
                Reference
              </span>

              <span>
                {payment.reference}
              </span>
            </div>
          )}

          <div className="flex justify-between">
            <span className="text-muted-foreground">
              Status
            </span>

            <Badge
              variant={payment.status === "PAID" ? "default" : "destructive"}
            >
              {payment.status}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* =========================
      QR Code
      ========================= */}

      <div className="flex justify-center">
        <QRCode
          value={`Invoice:${payment.invoice?.number || "-"}|Amount:${payment.amount}|Payment:${payment.id}`}
          size={120}
        />
      </div>

      {/* =========================
      Actions
      ========================= */}

      <div className="no-print flex justify-center gap-3">
        <Button onClick={() => window.print()}>
          Print Receipt
        </Button>
      </div>

      {/* =========================
      Print Style
      ========================= */}

      <style jsx global>{`
        .logo-large {
          width: 200px;
          height: auto;
        }

        @media print {
          body * {
            visibility: hidden;
          }

          .receipt-area,
          .receipt-area * {
            visibility: visible;
          }

          .receipt-area {
            position: absolute;
            left: 0;
            top: 0;
            width: 210mm;
            padding: 20mm;
            background: white;
          }

          .logo-large {
            width: 260px;
            margin-bottom: 10mm;
          }

          .no-print {
            display: none !important;
          }
        }
      `}</style>
    </div>
  )
}