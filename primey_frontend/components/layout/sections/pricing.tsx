"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";
import {
  Check,
  Loader2,
  AlertCircle,
  Building2,
  Users,
  LayoutGrid,
} from "lucide-react";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PricingCtaSection } from "@/components/layout/sections/cta";
import SectionContainer from "@/components/layout/section-container";
import SectionHeader from "@/components/layout/section-header";
import { AnimatedBackground } from "@/components/ui/extras/animated-background";
import { SlidingNumber } from "@/components/ui/extras/sliding-number";
import { Badge } from "@/components/ui/badge";

/* =========================================================
   🔧 API
========================================================= */
const API = process.env.NEXT_PUBLIC_API_URL;

/* =========================================================
   🌐 Language Types
========================================================= */
type AppLang = "ar" | "en";

/* =========================================================
   🧩 Types
========================================================= */
type PeriodValue = "monthly" | "annually";

type Period = {
  label: string;
  value: PeriodValue;
};

type Plan = {
  id: number;
  name: string;
  description: string;
  price_monthly: number | null;
  price_yearly: number | null;
  max_companies: number | null;
  max_employees: number | null;
  is_active: boolean;
  apps: string[];
};

type PlansResponse = {
  plans: Plan[];
};

type PricingContent = {
  section: {
    subTitle: string;
    title: string;
    description: string;
  };
  periods: Record<PeriodValue, string>;
  saveLabel: string;
  loading: string;
  errorTitle: string;
  emptyTitle: string;
  emptyDescription: string;
  mostPopular: string;
  annualDiscountApplied: string;
  companies: string;
  employees: string;
  includedFeatures: string;
  getStarted: string;
  fallbackPlanDescription: string;
  features: {
    upToCompanies: (count: string, rawCount: number) => string;
    upToEmployees: (count: string) => string;
  };
  toasts: {
    loadFailed: string;
  };
};

/* =========================================================
   🌐 Localized Content
========================================================= */
const content: Record<AppLang, PricingContent> = {
  ar: {
    section: {
      subTitle: "الأسعار",
      title: "احصل على وصول غير محدود",
      description:
        "استمتع بوصول غير محدود إلى جميع الميزات والموارد، بما يمكّن أعمالك من النمو دون حدود.",
    },
    periods: {
      monthly: "شهري",
      annually: "سنوي",
    },
    saveLabel: "وفّر",
    loading: "جارٍ تحميل الباقات...",
    errorTitle: "فشل تحميل الباقات",
    emptyTitle: "لا توجد باقات نشطة",
    emptyDescription:
      "ستظهر الباقات النشطة هنا تلقائيًا بمجرد تفعيلها في النظام.",
    mostPopular: "الأكثر شيوعًا",
    annualDiscountApplied: "تم تطبيق خصم الفوترة السنوية",
    companies: "الشركات",
    employees: "الموظفون",
    includedFeatures: "الميزات المتضمنة",
    getStarted: "ابدأ الآن",
    fallbackPlanDescription: "باقة اشتراك Mham Cloud",
    features: {
      upToCompanies: (count: string, rawCount: number) =>
        rawCount === 1 ? `حتى شركة واحدة` : `حتى ${count} شركات`,
      upToEmployees: (count: string) => `حتى ${count} موظف`,
    },
    toasts: {
      loadFailed: "تعذر تحميل الباقات الحالية",
    },
  },
  en: {
    section: {
      subTitle: "Pricing",
      title: "Get Unlimited Access",
      description:
        "Enjoy unlimited access to all features and resources, empowering your business to grow without limits.",
    },
    periods: {
      monthly: "Monthly",
      annually: "Annually",
    },
    saveLabel: "Save",
    loading: "Loading pricing plans...",
    errorTitle: "Failed to load plans",
    emptyTitle: "No active plans found",
    emptyDescription:
      "Active plans will appear here automatically once they are enabled in the system.",
    mostPopular: "Most Popular",
    annualDiscountApplied: "Annual discounted billing applied",
    companies: "Companies",
    employees: "Employees",
    includedFeatures: "Included Features",
    getStarted: "Get Started",
    fallbackPlanDescription: "Mham Cloud subscription plan",
    features: {
      upToCompanies: (count: string, rawCount: number) =>
        `Up to ${count} compan${rawCount === 1 ? "y" : "ies"}`,
      upToEmployees: (count: string) => `Up to ${count} employees`,
    },
    toasts: {
      loadFailed: "Failed to load current plans",
    },
  },
};

/* =========================================================
   🍪 Helpers
========================================================= */
function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;

  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));

  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

function getCurrentLang(): AppLang {
  const cookieLang =
    getCookie("lang") || getCookie("locale") || getCookie("NEXT_LOCALE");

  return cookieLang === "ar" ? "ar" : "en";
}

/* =========================================================
   🛠️ Data Helpers
========================================================= */
function normalizeApps(apps: unknown): string[] {
  if (!Array.isArray(apps)) return [];

  return apps
    .map((item) => String(item).trim())
    .filter(Boolean);
}

function normalizeNumber(value: unknown): number {
  if (typeof value === "number" && !Number.isNaN(value)) {
    return value;
  }

  const parsed = Number(value ?? 0);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function prettifyAppName(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatLimit(value: number | null | undefined): string {
  const safeValue = normalizeNumber(value);

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(safeValue);
}

/* =========================================================
   🧩 Section
========================================================= */
export const PricingSection = () => {
  const [lang, setLang] = useState<AppLang>("en");
  const [selectedPeriodValue, setSelectedPeriodValue] =
    useState<PeriodValue>("monthly");
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  /* -----------------------------------------------------
     🌐 Language sync
  ----------------------------------------------------- */
  useEffect(() => {
    const updateLang = () => {
      setLang(getCurrentLang());
    };

    updateLang();

    const observer = new MutationObserver(() => {
      updateLang();
    });

    if (typeof document !== "undefined") {
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["lang", "dir"],
      });
    }

    return () => observer.disconnect();
  }, []);

  const isArabic = lang === "ar";
  const dir = isArabic ? "rtl" : "ltr";
  const t = content[lang];

  const periods: Period[] = useMemo(
    () => [
      { label: t.periods.monthly, value: "monthly" },
      { label: t.periods.annually, value: "annually" },
    ],
    [t]
  );

  const selectedPeriod =
    periods.find((period) => period.value === selectedPeriodValue) ?? periods[0];

  /* -----------------------------------------------------
     📡 Fetch real plans from system
  ----------------------------------------------------- */
  useEffect(() => {
    let isMounted = true;

    async function fetchPlans() {
      try {
        setLoading(true);
        setError("");

        if (!API) {
          throw new Error("NEXT_PUBLIC_API_URL is not configured");
        }

        const response = await fetch(`${API}/api/system/plans/`, {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch plans: ${response.status}`);
        }

        const data: PlansResponse = await response.json();

        const normalizedPlans: Plan[] = Array.isArray(data?.plans)
          ? data.plans
              .filter((plan) => plan?.is_active !== false)
              .map((plan) => ({
                id: normalizeNumber(plan.id),
                name: String(plan.name || "Plan"),
                description: String(plan.description || ""),
                price_monthly: normalizeNumber(plan.price_monthly),
                price_yearly: normalizeNumber(plan.price_yearly),
                max_companies: normalizeNumber(plan.max_companies),
                max_employees: normalizeNumber(plan.max_employees),
                is_active: Boolean(plan.is_active),
                apps: normalizeApps(plan.apps),
              }))
          : [];

        if (!isMounted) return;

        setPlans(normalizedPlans);
      } catch (err) {
        console.error("PricingSection fetch error:", err);

        if (!isMounted) return;

        setError(t.toasts.loadFailed);
        toast.error(t.toasts.loadFailed);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchPlans();

    return () => {
      isMounted = false;
    };
  }, [t.toasts.loadFailed]);

  /* -----------------------------------------------------
     ⭐ Sort plans by selected period price
  ----------------------------------------------------- */
  const sortedPlans = useMemo(() => {
    return [...plans].sort((a, b) => {
      const aPrice =
        selectedPeriod.value === "monthly"
          ? normalizeNumber(a.price_monthly)
          : normalizeNumber(a.price_yearly);

      const bPrice =
        selectedPeriod.value === "monthly"
          ? normalizeNumber(b.price_monthly)
          : normalizeNumber(b.price_yearly);

      return aPrice - bPrice;
    });
  }, [plans, selectedPeriod]);

  /* -----------------------------------------------------
     ⭐ Middle plan = popular
  ----------------------------------------------------- */
  const popularPlanId = useMemo(() => {
    if (sortedPlans.length === 0) return null;
    if (sortedPlans.length === 1) return sortedPlans[0].id;
    return sortedPlans[Math.floor(sortedPlans.length / 2)]?.id ?? null;
  }, [sortedPlans]);

  /* -----------------------------------------------------
     💰 Annual discount
  ----------------------------------------------------- */
  const annualDiscountPercent = useMemo(() => {
    if (sortedPlans.length === 0) return 0;

    const firstPlanWithDiscount = sortedPlans.find((plan) => {
      const monthly = normalizeNumber(plan.price_monthly);
      const yearly = normalizeNumber(plan.price_yearly);

      return monthly > 0 && yearly > 0 && yearly < monthly * 12;
    });

    if (!firstPlanWithDiscount) return 0;

    const monthly = normalizeNumber(firstPlanWithDiscount.price_monthly);
    const yearly = normalizeNumber(firstPlanWithDiscount.price_yearly);

    const discount = Math.round(((monthly * 12 - yearly) / (monthly * 12)) * 100);
    return discount > 0 ? discount : 0;
  }, [sortedPlans]);

  return (
    <SectionContainer id="pricing">
      <div dir={dir}>
        <SectionHeader
          subTitle={t.section.subTitle}
          title={t.section.title}
          description={t.section.description}
        />

        <div className="mx-auto max-w-6xl">
          {/* فترة الاشتراك */}
          <div className="flex justify-center">
            <div className="mb-8 flex justify-center rounded-lg border">
              <AnimatedBackground
                defaultValue={selectedPeriod.value}
                className="bg-background rounded-lg"
                onValueChange={(value) => {
                  const nextPeriod = periods.find((p) => p.value === value);
                  if (nextPeriod) {
                    setSelectedPeriodValue(nextPeriod.value);
                  }
                }}
                transition={{
                  ease: "easeInOut",
                  duration: 0.2,
                }}
              >
                {periods.map((period) => (
                  <Button key={period.value} data-id={period.value} variant="ghost">
                    {period.label}
                    {period.value === "annually" && annualDiscountPercent > 0 && (
                      <Badge className="ms-1 border-0 bg-transparent text-green-600">
                        {t.saveLabel} {annualDiscountPercent}%
                      </Badge>
                    )}
                  </Button>
                ))}
              </AnimatedBackground>
            </div>
          </div>

          {/* Loading */}
          {loading && (
            <div className="flex min-h-[240px] items-center justify-center">
              <div className="flex items-center gap-3 rounded-xl border px-5 py-4">
                <Loader2 className="size-5 animate-spin" />
                <span className="text-sm font-medium">{t.loading}</span>
              </div>
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <Card className="mx-auto max-w-2xl">
              <CardContent className="flex flex-col items-center justify-center gap-3 py-12 text-center">
                <AlertCircle className="text-destructive size-10" />
                <h3 className="text-xl font-semibold">{t.errorTitle}</h3>
                <p className="text-muted-foreground">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Empty */}
          {!loading && !error && sortedPlans.length === 0 && (
            <Card className="mx-auto max-w-2xl">
              <CardContent className="flex flex-col items-center justify-center gap-3 py-12 text-center">
                <AlertCircle className="size-10" />
                <h3 className="text-xl font-semibold">{t.emptyTitle}</h3>
                <p className="text-muted-foreground">{t.emptyDescription}</p>
              </CardContent>
            </Card>
          )}

          {/* Plans */}
          {!loading && !error && sortedPlans.length > 0 && (
            <div className="grid gap-6 lg:grid-cols-3 lg:gap-8">
              {sortedPlans.map((plan) => {
                const isPopular = plan.id === popularPlanId;

                const currentPrice =
                  selectedPeriod.value === "monthly"
                    ? normalizeNumber(plan.price_monthly)
                    : normalizeNumber(plan.price_yearly);

                const hasDiscount =
                  normalizeNumber(plan.price_monthly) > 0 &&
                  normalizeNumber(plan.price_yearly) > 0 &&
                  normalizeNumber(plan.price_yearly) <
                    normalizeNumber(plan.price_monthly) * 12;

                const companiesCount = normalizeNumber(plan.max_companies);
                const employeesCount = formatLimit(plan.max_employees);

                const features: string[] = [
                  t.features.upToCompanies(
                    formatLimit(plan.max_companies),
                    companiesCount
                  ),
                  t.features.upToEmployees(employeesCount),
                  ...plan.apps.map(prettifyAppName),
                ];

                return (
                  <Card
                    key={plan.id}
                    className={cn("relative h-full overflow-hidden", {
                      "border-primary!": isPopular,
                    })}
                  >
                    {isPopular && (
                      <div
                        className={cn(
                          "bg-primary text-primary-foreground absolute top-0 rounded-bl-lg px-3 py-1 text-xs font-medium",
                          isArabic ? "left-0 rounded-br-lg rounded-bl-none" : "right-0"
                        )}
                      >
                        {t.mostPopular}
                      </div>
                    )}

                    <CardHeader>
                      <CardTitle className={cn(isArabic && "text-right")}>
                        {plan.name}
                      </CardTitle>
                    </CardHeader>

                    <CardContent className="flex h-full flex-col">
                      <div
                        className={cn(
                          "flex items-end gap-2",
                          isArabic && "flex-row-reverse justify-end"
                        )}
                      >
                        <div
                          className={cn(
                            "flex items-center gap-2 text-4xl font-bold",
                            isArabic && "flex-row-reverse"
                          )}
                        >
                          <Image
                            src="/currency/sar.svg"
                            alt="SAR"
                            width={28}
                            height={28}
                            className="h-7 w-7 shrink-0"
                          />
                          <span className="flex items-baseline">
                            <SlidingNumber value={currentPrice} />
                          </span>
                        </div>

                        <span className="text-muted-foreground mb-1 text-sm">
                          /{selectedPeriod.label}
                        </span>
                      </div>

                      {hasDiscount && selectedPeriod.value === "annually" && (
                        <p
                          className={cn(
                            "mt-2 text-sm font-medium text-green-600",
                            isArabic && "text-right"
                          )}
                        >
                          {t.annualDiscountApplied}
                        </p>
                      )}

                      <p className={cn("text-muted-foreground mt-3", isArabic && "text-right")}>
                        {plan.description || t.fallbackPlanDescription}
                      </p>

                      <div className="mt-4 grid gap-3 sm:grid-cols-2">
                        <div className="rounded-lg border p-3">
                          <div
                            className={cn(
                              "text-muted-foreground mb-2 flex items-center gap-2 text-xs",
                              isArabic && "flex-row-reverse justify-end text-right"
                            )}
                          >
                            <Building2 className="size-4" />
                            <span>{t.companies}</span>
                          </div>
                          <p className={cn("font-semibold", isArabic && "text-right")}>
                            {formatLimit(plan.max_companies)}
                          </p>
                        </div>

                        <div className="rounded-lg border p-3">
                          <div
                            className={cn(
                              "text-muted-foreground mb-2 flex items-center gap-2 text-xs",
                              isArabic && "flex-row-reverse justify-end text-right"
                            )}
                          >
                            <Users className="size-4" />
                            <span>{t.employees}</span>
                          </div>
                          <p className={cn("font-semibold", isArabic && "text-right")}>
                            {formatLimit(plan.max_employees)}
                          </p>
                        </div>
                      </div>

                      <div className="mt-6">
                        <div
                          className={cn(
                            "mb-3 flex items-center gap-2 text-sm font-medium",
                            isArabic && "flex-row-reverse justify-end text-right"
                          )}
                        >
                          <LayoutGrid className="text-primary size-4" />
                          <span>{t.includedFeatures}</span>
                        </div>

                        <ul className="space-y-3">
                          {features.map((feature, index) => (
                            <li
                              key={`${plan.id}-${index}`}
                              className={cn(
                                "flex items-center",
                                isArabic && "flex-row-reverse justify-end text-right"
                              )}
                            >
                              <Check
                                className={cn(
                                  "text-primary size-4 shrink-0",
                                  isArabic ? "ml-2" : "mr-2"
                                )}
                              />
                              <span>{feature}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="mt-6 flex-grow" />

                      <Button asChild variant={isPopular ? "default" : "outline"}>
                        <Link href="/register">{t.getStarted}</Link>
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          <PricingCtaSection />
        </div>
      </div>
    </SectionContainer>
  );
};