"use client";

import { useEffect } from "react";

declare global {
  interface Window {
    dataLayer: unknown[];
    gtag?: (...args: unknown[]) => void;
  }
}

export default function GoogleAnalyticsInit() {
  useEffect(() => {
    const GA_KEY = process.env.NEXT_PUBLIC_GA_KEY || process.env.GA_KEY;

    if (!GA_KEY || typeof window === "undefined") {
      console.error("Google Analytics key not provided.");
      return;
    }

    if (!document.querySelector(`script[data-ga="${GA_KEY}"]`)) {
      const script = document.createElement("script");
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_KEY}`;
      script.setAttribute("data-ga", GA_KEY);
      document.head.appendChild(script);
    }

    window.dataLayer = window.dataLayer || [];

    function gtag(...args: unknown[]) {
      window.dataLayer.push(args);
    }

    window.gtag = gtag;

    gtag("js", new Date());
    gtag("config", GA_KEY, {
      page_path: window.location.pathname + window.location.search,
    });
  }, []);

  return null;
}