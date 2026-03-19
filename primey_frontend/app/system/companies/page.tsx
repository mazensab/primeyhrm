"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Search,
  FileDown,
  FileSpreadsheet,
  Eye,
  Power,
  Building2,
  Loader2,
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

/* =========================================
   READ CSRF TOKEN FROM COOKIE
========================================= */
function getCookie(name: string) {
  if (typeof document === "undefined") return null

  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift() || null
  }

  return null
}

type Company = {
  id: number
  name: string
  is_active: boolean
  created_at: string

  owner?: {
    email?: string
  }

  subscription?: {
    plan?: string
    status?: string
  }

  users_count: number
}

export default function SystemCompaniesPage() {
  const router = useRouter()

  const [companies, setCompanies] = useState<Company[]>([])
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(true)
  const [togglingId, setTogglingId] = useState<number | null>(null)

  useEffect(() => {
    const loadCompanies = async () => {
      setLoading(true)

      try {
        const res = await fetch(
          "http://localhost:8000/api/system/companies/list/",
          {
            credentials: "include",
          }
        )

        if (!res.ok) {
          throw new Error(`Failed with status ${res.status}`)
        }

        const data = await res.json()

        console.log("Companies API:", data)
        setCompanies(Array.isArray(data) ? data : [])
      } catch (error) {
        console.error("Failed loading companies", error)
        toast.error("Failed to load companies")
      } finally {
        setLoading(false)
      }
    }

    loadCompanies()
  }, [])

  /* ===============================
     TOGGLE COMPANY ACTIVE
  ================================ */
  const toggleCompany = async (id: number) => {
    setTogglingId(id)

    try {
      const csrftoken = getCookie("csrftoken")

      const res = await fetch(
        `http://localhost:8000/api/system/companies/${id}/toggle-active/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken || "",
          },
        }
      )

      if (!res.ok) {
        console.error("Toggle failed", res.status)
        toast.error("Failed to update company status")
        return
      }

      const updated = companies.map((c) =>
        c.id === id ? { ...c, is_active: !c.is_active } : c
      )

      setCompanies(updated)
      toast.success("Company status updated successfully")
    } catch (error) {
      console.error("Toggle error:", error)
      toast.error("Server error while updating company status")
    } finally {
      setTogglingId(null)
    }
  }

  const filtered = useMemo(() => {
    return companies.filter((c) =>
      c.name.toLowerCase().includes(search.toLowerCase())
    )
  }, [companies, search])

  /* ===============================
     EXPORT EXCEL
  =============================== */
  const exportExcel = () => {
    const rows = [
      ["Company", "Owner", "Plan", "Users", "Status", "Created"],
      ...filtered.map((c) => [
        c.name || "-",
        c.owner?.email || "-",
        c.subscription?.plan || "-",
        String(c.users_count ?? 0),
        c.is_active ? "ACTIVE" : "DISABLED",
        c.created_at
          ? new Date(c.created_at).toLocaleDateString("en-CA")
          : "-",
      ]),
    ]

    const csv =
      "data:text/csv;charset=utf-8," +
      rows.map((e) => e.join(",")).join("\n")

    const link = document.createElement("a")
    link.href = encodeURI(csv)
    link.download = "companies.csv"
    link.click()

    toast.success("Companies exported successfully")
  }

  /* ===============================
     PRINT PDF
  =============================== */
  const printPDF = () => {
    window.print()
  }

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            Companies
          </h1>

          <p className="text-muted-foreground">
            Manage all companies on the platform
          </p>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={printPDF}
          >
            <FileDown className="mr-2 h-4 w-4" />
            PDF
          </Button>

          <Button
            variant="outline"
            onClick={exportExcel}
          >
            <FileSpreadsheet className="mr-2 h-4 w-4" />
            Excel
          </Button>

          <Button
            className="bg-black text-white hover:bg-black/80"
            onClick={() => router.push("/system/companies/create")}
          >
            + Add Company
          </Button>
        </div>
      </div>

      {/* SEARCH */}
      <Card>
        <CardHeader>
          <CardTitle>Search</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="flex items-center gap-3">
            <Search className="h-4 w-4" />

            <Input
              placeholder="Search company..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* TABLE */}
      <Card>
        <CardHeader>
          <CardTitle>Companies List</CardTitle>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Loading companies...
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Users</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">
                    Actions
                  </TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="py-10 text-center text-muted-foreground"
                    >
                      No companies found
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((company) => (
                    <TableRow key={company.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-muted-foreground" />
                          <span>{company.name}</span>
                        </div>
                      </TableCell>

                      <TableCell>
                        {company.owner?.email || "-"}
                      </TableCell>

                      <TableCell>
                        {company.subscription?.plan || "-"}
                      </TableCell>

                      <TableCell>
                        {company.users_count}
                      </TableCell>

                      <TableCell>
                        {company.is_active ? (
                          <span className="rounded-md bg-green-100 px-2 py-1 text-xs text-green-700">
                            ACTIVE
                          </span>
                        ) : (
                          <span className="rounded-md bg-red-100 px-2 py-1 text-xs text-red-700">
                            DISABLED
                          </span>
                        )}
                      </TableCell>

                      <TableCell>
                        {new Date(company.created_at).toLocaleDateString("en-CA")}
                      </TableCell>

                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          {/* MANAGE COMPANY */}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => router.push(`/system/companies/${company.id}`)}
                          >
                            <Building2 className="mr-2 h-4 w-4" />
                            Manage Company
                          </Button>

                          {/* VIEW */}
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => router.push(`/system/companies/${company.id}`)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>

                          {/* ENABLE / DISABLE */}
                          <Button
                            size="icon"
                            variant={company.is_active ? "outline" : "destructive"}
                            onClick={() => toggleCompany(company.id)}
                            disabled={togglingId === company.id}
                          >
                            {togglingId === company.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Power className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}