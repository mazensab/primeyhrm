"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, Clock, Mail, Phone } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import SectionContainer from "@/components/layout/section-container";
import SectionHeader from "@/components/layout/section-header";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

/* =========================================================
   🌐 API Helpers
========================================================= */
const ENV_API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ?? "";

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  if (ENV_API_BASE) {
    return `${ENV_API_BASE}${normalizedPath}`;
  }

  if (typeof window !== "undefined") {
    return `${window.location.origin}${normalizedPath}`;
  }

  return normalizedPath;
}

const SUBJECT_OPTIONS = [
  "Sales Inquiry",
  "Demo Request",
  "Technical Support",
  "Billing & Subscription",
  "Partnership",
  "General Inquiry",
] as const;

type AppLang = "ar" | "en";
type SubjectOption = (typeof SUBJECT_OPTIONS)[number];

type ContactFormValues = {
  firstName: string;
  lastName: string;
  email: string;
  subject: SubjectOption;
  message: string;
};

type ContactContent = {
  section: {
    subTitle: string;
    title: string;
    description: string;
  };
  contactInfo: {
    locationLabel: string;
    locationValue: string;
    phoneLabel: string;
    phoneValue: string;
    emailLabel: string;
    emailValue: string;
    businessHoursLabel: string;
    businessHoursValue: string;
  };
  form: {
    cardTitle: string;
    firstName: string;
    lastName: string;
    email: string;
    subject: string;
    message: string;
    firstNamePlaceholder: string;
    lastNamePlaceholder: string;
    emailPlaceholder: string;
    subjectPlaceholder: string;
    messagePlaceholder: string;
    submit: string;
    submitting: string;
  };
  validation: {
    firstNameRequired: string;
    lastNameRequired: string;
    tooLong: string;
    invalidEmail: string;
    selectSubject: string;
    messageTooShort: string;
    messageTooLong: string;
  };
  toast: {
    success: string;
    errorDefault: string;
    sendFailed: string;
  };
  subjects: Record<SubjectOption, string>;
};

const content: Record<AppLang, ContactContent> = {
  ar: {
    section: {
      subTitle: "تواصل معنا",
      title: "ابقَ على اتصال معنا",
      description:
        "ابقَ على تواصل معنا للحصول على التحديثات، الدعم، والرؤى المفيدة. نحن هنا لمساعدتك في كل خطوة.",
    },
    contactInfo: {
      locationLabel: "الموقع:",
      locationValue:
        "Madina 2809 Al-Jumah, Prince Abdul Mohsen bin Abdul Aziz, 42316",
      phoneLabel: "اتصل بنا:",
      phoneValue: "00966 (50) 526-3775",
      emailLabel: "راسلنا:",
      emailValue: "info@mhamcloud.sa",
      businessHoursLabel: "ساعات العمل:",
      businessHoursValue: "من الثلاثاء إلى السبت، 9 صباحًا - 5 مساءً",
    },
    form: {
      cardTitle: "إرسال رسالة",
      firstName: "الاسم الأول",
      lastName: "اسم العائلة",
      email: "البريد الإلكتروني",
      subject: "الموضوع",
      message: "الرسالة",
      firstNamePlaceholder: "مازن",
      lastNamePlaceholder: "العتيبي",
      emailPlaceholder: "info@example.com",
      subjectPlaceholder: "اختر الموضوع",
      messagePlaceholder: "اكتب رسالتك هنا...",
      submit: "إرسال الرسالة",
      submitting: "جارٍ الإرسال...",
    },
    validation: {
      firstNameRequired: "الاسم الأول مطلوب",
      lastNameRequired: "اسم العائلة مطلوب",
      tooLong: "النص طويل جدًا",
      invalidEmail: "البريد الإلكتروني غير صالح",
      selectSubject: "يرجى اختيار الموضوع",
      messageTooShort: "الرسالة قصيرة جدًا",
      messageTooLong: "الرسالة طويلة جدًا",
    },
    toast: {
      success: "تم إرسال رسالتك بنجاح.",
      errorDefault: "حدث خطأ أثناء إرسال رسالتك.",
      sendFailed: "تعذر إرسال الرسالة",
    },
    subjects: {
      "Sales Inquiry": "استفسار مبيعات",
      "Demo Request": "طلب عرض تجريبي",
      "Technical Support": "الدعم الفني",
      "Billing & Subscription": "الفوترة والاشتراك",
      Partnership: "شراكة",
      "General Inquiry": "استفسار عام",
    },
  },
  en: {
    section: {
      subTitle: "Contact",
      title: "Get Connect With Us access",
      description:
        "Stay in touch with us for updates, support, and valuable insights. We’re here to help you every step of the way!",
    },
    contactInfo: {
      locationLabel: "Location:",
      locationValue:
        "Madina 2809 Al-Jumah, Prince Abdul Mohsen bin Abdul Aziz, 42316",
      phoneLabel: "Call us:",
      phoneValue: "+9 (665) 526-3775",
      emailLabel: "Email us:",
      emailValue: "info@mhamcloud.sa",
      businessHoursLabel: "Business Hours:",
      businessHoursValue: "Saturday to Thursday, 9 AM - 5 PM",
    },
    form: {
      cardTitle: "Send Message",
      firstName: "Firstname",
      lastName: "Lastname",
      email: "Email",
      subject: "Subject",
      message: "Message",
      firstNamePlaceholder: "Leopoldo",
      lastNamePlaceholder: "Miranda",
      emailPlaceholder: "contact@mhamcloud.com",
      subjectPlaceholder: "Select a subject",
      messagePlaceholder: "Your message...",
      submit: "Send message",
      submitting: "Sending...",
    },
    validation: {
      firstNameRequired: "First name is required",
      lastNameRequired: "Last name is required",
      tooLong: "Too long",
      invalidEmail: "Invalid email address",
      selectSubject: "Please select a subject",
      messageTooShort: "Message is too short",
      messageTooLong: "Message is too long",
    },
    toast: {
      success: "Message sent successfully.",
      errorDefault: "Something went wrong while sending your message.",
      sendFailed: "Failed to send message",
    },
    subjects: {
      "Sales Inquiry": "Sales Inquiry",
      "Demo Request": "Demo Request",
      "Technical Support": "Technical Support",
      "Billing & Subscription": "Billing & Subscription",
      Partnership: "Partnership",
      "General Inquiry": "General Inquiry",
    },
  },
};

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

  if (cookieLang === "ar") return "ar";
  return "en";
}

function createFormSchema(t: ContactContent) {
  return z.object({
    firstName: z
      .string()
      .trim()
      .min(1, t.validation.firstNameRequired)
      .max(50, t.validation.tooLong),
    lastName: z
      .string()
      .trim()
      .min(1, t.validation.lastNameRequired)
      .max(50, t.validation.tooLong),
    email: z.string().trim().email(t.validation.invalidEmail),
    subject: z.enum(SUBJECT_OPTIONS, {
      errorMap: () => ({ message: t.validation.selectSubject }),
    }),
    message: z
      .string()
      .trim()
      .min(2, t.validation.messageTooShort)
      .max(2000, t.validation.messageTooLong),
  });
}

export const ContactSection = () => {
  const [lang, setLang] = useState<AppLang>("en");
  const [mounted, setMounted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const nextLang = getCurrentLang();
    setLang(nextLang);
    setMounted(true);

    if (typeof document !== "undefined") {
      const observer = new MutationObserver(() => {
        const updatedLang = getCurrentLang();
        setLang((prev) => (prev === updatedLang ? prev : updatedLang));
      });

      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["lang", "dir"],
      });

      return () => observer.disconnect();
    }
  }, []);

  const t = content[lang];
  const isArabic = lang === "ar";
  const dir = isArabic ? "rtl" : "ltr";

  const formSchema = useMemo(() => createFormSchema(t), [t]);

  const form = useForm<ContactFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      email: "",
      subject: undefined,
      message: "",
    },
  });

  useEffect(() => {
    if (!mounted) return;
    form.clearErrors();
  }, [lang, mounted, form]);

  async function onSubmit(values: ContactFormValues) {
    setIsSubmitting(true);

    try {
      const response = await fetch(buildApiUrl("/api/public/contact/"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          first_name: values.firstName,
          last_name: values.lastName,
          email: values.email,
          subject: values.subject,
          message: values.message,
        }),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.message || t.toast.sendFailed);
      }

      toast.success(t.toast.success);

      form.reset({
        firstName: "",
        lastName: "",
        email: "",
        subject: undefined,
        message: "",
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : t.toast.errorDefault;

      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <SectionContainer id="contact">
      <div dir={dir} className={cn("w-full", isArabic && "font-[inherit]")}>
        <SectionHeader
          subTitle={t.section.subTitle}
          title={t.section.title}
          description={t.section.description}
        />

        <section className="mx-auto grid max-w-screen-lg grid-cols-1 gap-6 md:grid-cols-2">
          <div>
            <div className="flex flex-col gap-6 *:rounded-lg *:border *:p-6">
              <div className="bg-muted">
                <div
                  className={cn(
                    "mb-4 flex items-center gap-3",
                    isArabic && "flex-row-reverse justify-end text-right"
                  )}
                >
                  <Building2 className="size-4 shrink-0" />
                  <div className="font-bold">{t.contactInfo.locationLabel}</div>
                </div>
                <div
                  className={cn(
                    "text-muted-foreground",
                    isArabic && "text-right"
                  )}
                >
                  {t.contactInfo.locationValue}
                </div>
              </div>

              <div className="bg-muted">
                <div
                  className={cn(
                    "mb-4 flex items-center gap-3",
                    isArabic && "flex-row-reverse justify-end text-right"
                  )}
                >
                  <Phone className="size-4 shrink-0" />
                  <div className="font-bold">{t.contactInfo.phoneLabel}</div>
                </div>
                <div
                  className={cn(
                    "text-muted-foreground",
                    isArabic && "text-right"
                  )}
                >
                  {t.contactInfo.phoneValue}
                </div>
              </div>

              <div className="bg-muted">
                <div
                  className={cn(
                    "mb-4 flex items-center gap-3",
                    isArabic && "flex-row-reverse justify-end text-right"
                  )}
                >
                  <Mail className="size-4 shrink-0" />
                  <div className="font-bold">{t.contactInfo.emailLabel}</div>
                </div>
                <div
                  className={cn(
                    "text-muted-foreground",
                    isArabic && "text-right"
                  )}
                >
                  {t.contactInfo.emailValue}
                </div>
              </div>

              <div className="bg-muted">
                <div
                  className={cn(
                    "mb-4 flex items-center gap-3",
                    isArabic && "flex-row-reverse justify-end text-right"
                  )}
                >
                  <Clock className="size-4 shrink-0" />
                  <div className="font-bold">
                    {t.contactInfo.businessHoursLabel}
                  </div>
                </div>
                <div
                  className={cn(
                    "text-muted-foreground",
                    isArabic && "text-right"
                  )}
                >
                  {t.contactInfo.businessHoursValue}
                </div>
              </div>
            </div>
          </div>

          <Card className="bg-muted">
            <CardHeader>
              <CardTitle className={cn(isArabic && "text-right")}>
                {t.form.cardTitle}
              </CardTitle>
            </CardHeader>

            <CardContent>
              <Form {...form}>
                <form
                  onSubmit={form.handleSubmit(onSubmit)}
                  className="grid w-full gap-6"
                >
                  <div className="flex flex-col gap-6 md:flex-row">
                    <FormField
                      control={form.control}
                      name="firstName"
                      render={({ field, fieldState }) => (
                        <FormItem className="w-full gap-4">
                          <FormLabel
                            className={cn(
                              "font-semibold",
                              isArabic && "text-right"
                            )}
                          >
                            {t.form.firstName}
                          </FormLabel>
                          <FormControl>
                            <Input
                              placeholder={t.form.firstNamePlaceholder}
                              dir={isArabic ? "rtl" : "ltr"}
                              className={cn(isArabic && "text-right")}
                              {...field}
                            />
                          </FormControl>
                          {fieldState.error && (
                            <p
                              className={cn(
                                "text-sm text-red-500",
                                isArabic && "text-right"
                              )}
                            >
                              {fieldState.error.message}
                            </p>
                          )}
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="lastName"
                      render={({ field, fieldState }) => (
                        <FormItem className="w-full gap-4">
                          <FormLabel
                            className={cn(
                              "font-semibold",
                              isArabic && "text-right"
                            )}
                          >
                            {t.form.lastName}
                          </FormLabel>
                          <FormControl>
                            <Input
                              placeholder={t.form.lastNamePlaceholder}
                              dir={isArabic ? "rtl" : "ltr"}
                              className={cn(isArabic && "text-right")}
                              {...field}
                            />
                          </FormControl>
                          {fieldState.error && (
                            <p
                              className={cn(
                                "text-sm text-red-500",
                                isArabic && "text-right"
                              )}
                            >
                              {fieldState.error.message}
                            </p>
                          )}
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <FormField
                      control={form.control}
                      name="email"
                      render={({ field, fieldState }) => (
                        <FormItem className="gap-4">
                          <FormLabel
                            className={cn(
                              "font-semibold",
                              isArabic && "text-right"
                            )}
                          >
                            {t.form.email}
                          </FormLabel>
                          <FormControl>
                            <Input
                              type="email"
                              placeholder={t.form.emailPlaceholder}
                              dir="ltr"
                              className={cn(isArabic && "text-left")}
                              {...field}
                            />
                          </FormControl>
                          {fieldState.error && (
                            <p
                              className={cn(
                                "text-sm text-red-500",
                                isArabic && "text-right"
                              )}
                            >
                              {fieldState.error.message}
                            </p>
                          )}
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <FormField
                      control={form.control}
                      name="subject"
                      render={({ field, fieldState }) => (
                        <FormItem className="gap-4">
                          <FormLabel
                            className={cn(
                              "font-semibold",
                              isArabic && "text-right"
                            )}
                          >
                            {t.form.subject}
                          </FormLabel>

                          <Select value={field.value} onValueChange={field.onChange}>
                            <FormControl>
                              <SelectTrigger className="w-full">
                                <SelectValue placeholder={t.form.subjectPlaceholder} />
                              </SelectTrigger>
                            </FormControl>

                            <SelectContent>
                              {SUBJECT_OPTIONS.map((option) => (
                                <SelectItem key={option} value={option}>
                                  {t.subjects[option]}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>

                          {fieldState.error && (
                            <p
                              className={cn(
                                "text-sm text-red-500",
                                isArabic && "text-right"
                              )}
                            >
                              {fieldState.error.message}
                            </p>
                          )}
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <FormField
                      control={form.control}
                      name="message"
                      render={({ field, fieldState }) => (
                        <FormItem className="gap-4">
                          <FormLabel
                            className={cn(
                              "font-semibold",
                              isArabic && "text-right"
                            )}
                          >
                            {t.form.message}
                          </FormLabel>
                          <FormControl>
                            <Textarea
                              rows={5}
                              placeholder={t.form.messagePlaceholder}
                              className={cn(
                                "resize-none",
                                isArabic && "text-right"
                              )}
                              dir={isArabic ? "rtl" : "ltr"}
                              {...field}
                            />
                          </FormControl>
                          {fieldState.error && (
                            <p
                              className={cn(
                                "text-sm text-red-500",
                                isArabic && "text-right"
                              )}
                            >
                              {fieldState.error.message}
                            </p>
                          )}
                        </FormItem>
                      )}
                    />
                  </div>

                  <Button size="lg" type="submit" disabled={isSubmitting}>
                    {isSubmitting ? t.form.submitting : t.form.submit}
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>
        </section>
      </div>
    </SectionContainer>
  );
};