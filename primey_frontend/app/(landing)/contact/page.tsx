"use client";

import { useState } from "react";
import {
  Building2,
  Clock,
  Mail,
  Phone,
  SendHorizonal,
  ShieldCheck,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

const formSchema = z.object({
  firstName: z
    .string()
    .trim()
    .min(1, "First name is required")
    .max(50, "First name is too long"),
  lastName: z
    .string()
    .trim()
    .min(1, "Last name is required")
    .max(50, "Last name is too long"),
  email: z.string().trim().email("Invalid email address"),
  subject: z.enum(SUBJECT_OPTIONS, {
    errorMap: () => ({ message: "Please select a subject" }),
  }),
  message: z
    .string()
    .trim()
    .min(2, "Message is too short")
    .max(2000, "Message is too long"),
});

type ContactFormValues = z.infer<typeof formSchema>;

function ContactPageContent() {
  const [isSubmitting, setIsSubmitting] = useState(false);

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
        throw new Error(data?.message || "Failed to send message");
      }

      toast.success("Message sent successfully.");
      form.reset({
        firstName: "",
        lastName: "",
        email: "",
        subject: undefined,
        message: "",
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Something went wrong while sending your message.";

      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <SectionContainer id="contact" className="py-16 md:py-24">
      <SectionHeader
        subTitle="Contact Us"
        title="Let’s talk about your business"
        description="Reach out to Primey for sales, demos, support, billing, or partnership requests. Our team will get back to you as soon as possible."
      />

      <section className="mx-auto grid max-w-7xl grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-6">
          <Card className="border-border/60 bg-background/80 shadow-sm backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-xl">
                <ShieldCheck className="h-5 w-5" />
                Contact Information
              </CardTitle>
            </CardHeader>

            <CardContent className="grid gap-4">
              <div className="rounded-2xl border border-border/60 bg-muted/40 p-5">
                <div className="mb-2 flex items-center gap-3">
                  <Building2 className="h-4 w-4" />
                  <div className="font-semibold">Office</div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Primey Business Solutions
                  <br />
                  Saudi Arabia
                </p>
              </div>

              <div className="rounded-2xl border border-border/60 bg-muted/40 p-5">
                <div className="mb-2 flex items-center gap-3">
                  <Phone className="h-4 w-4" />
                  <div className="font-semibold">Phone</div>
                </div>
                <p className="text-sm text-muted-foreground">+966 50 000 0000</p>
              </div>

              <div className="rounded-2xl border border-border/60 bg-muted/40 p-5">
                <div className="mb-2 flex items-center gap-3">
                  <Mail className="h-4 w-4" />
                  <div className="font-semibold">Email</div>
                </div>
                <p className="text-sm text-muted-foreground">info@mhamcloud.sa</p>
              </div>

              <div className="rounded-2xl border border-border/60 bg-muted/40 p-5">
                <div className="mb-2 flex items-center gap-3">
                  <Clock className="h-4 w-4" />
                  <div className="font-semibold">Business Hours</div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Sunday to Thursday, 9:00 AM - 5:00 PM
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-border/60 bg-background/80 shadow-sm backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <SendHorizonal className="h-5 w-5" />
              Send Message
            </CardTitle>
          </CardHeader>

          <CardContent>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="grid gap-6"
              >
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <FormField
                    control={form.control}
                    name="firstName"
                    render={({ field, fieldState }) => (
                      <FormItem>
                        <FormLabel className="font-semibold">
                          First Name
                        </FormLabel>
                        <FormControl>
                          <Input placeholder="Mazen" {...field} />
                        </FormControl>
                        {fieldState.error && (
                          <p className="text-sm text-destructive">
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
                      <FormItem>
                        <FormLabel className="font-semibold">
                          Last Name
                        </FormLabel>
                        <FormControl>
                          <Input placeholder="Al..." {...field} />
                        </FormControl>
                        {fieldState.error && (
                          <p className="text-sm text-destructive">
                            {fieldState.error.message}
                          </p>
                        )}
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field, fieldState }) => (
                    <FormItem>
                      <FormLabel className="font-semibold">Email</FormLabel>
                      <FormControl>
                        <Input
                          type="email"
                          placeholder="name@company.com"
                          {...field}
                        />
                      </FormControl>
                      {fieldState.error && (
                        <p className="text-sm text-destructive">
                          {fieldState.error.message}
                        </p>
                      )}
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="subject"
                  render={({ field, fieldState }) => (
                    <FormItem>
                      <FormLabel className="font-semibold">Subject</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Select a subject" />
                          </SelectTrigger>
                        </FormControl>

                        <SelectContent>
                          <SelectItem value="Sales Inquiry">
                            Sales Inquiry
                          </SelectItem>
                          <SelectItem value="Demo Request">
                            Demo Request
                          </SelectItem>
                          <SelectItem value="Technical Support">
                            Technical Support
                          </SelectItem>
                          <SelectItem value="Billing & Subscription">
                            Billing & Subscription
                          </SelectItem>
                          <SelectItem value="Partnership">
                            Partnership
                          </SelectItem>
                          <SelectItem value="General Inquiry">
                            General Inquiry
                          </SelectItem>
                        </SelectContent>
                      </Select>

                      {fieldState.error && (
                        <p className="text-sm text-destructive">
                          {fieldState.error.message}
                        </p>
                      )}
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="message"
                  render={({ field, fieldState }) => (
                    <FormItem>
                      <FormLabel className="font-semibold">Message</FormLabel>
                      <FormControl>
                        <Textarea
                          rows={6}
                          placeholder="Tell us about your request..."
                          className="resize-none"
                          {...field}
                        />
                      </FormControl>
                      {fieldState.error && (
                        <p className="text-sm text-destructive">
                          {fieldState.error.message}
                        </p>
                      )}
                    </FormItem>
                  )}
                />

                <Button
                  size="lg"
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full md:w-auto"
                >
                  {isSubmitting ? "Sending..." : "Send Message"}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>
      </section>
    </SectionContainer>
  );
}

export default function ContactPage() {
  return <ContactPageContent />;
}