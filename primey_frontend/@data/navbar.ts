export interface LocalizedText {
  ar: string;
  en: string;
}

export interface RouteProps {
  href: string;
  label: LocalizedText;
}

export interface ProductProps {
  title: LocalizedText;
  icon: string;
  description: LocalizedText;
}

export const routeList: RouteProps[] = [
  {
    href: "#solutions",
    label: {
      ar: "الحلول",
      en: "Solutions",
    },
  },
  {
    href: "#pricing",
    label: {
      ar: "الأسعار",
      en: "Pricing",
    },
  },
  {
    href: "#team",
    label: {
      ar: "الفريق",
      en: "Team",
    },
  },
  {
    href: "#contact",
    label: {
      ar: "تواصل معنا",
      en: "Contact",
    },
  },
];

export const productList: ProductProps[] = [
  {
    title: {
      ar: "منصة الإطلاق",
      en: "LaunchPad",
    },
    icon: "Frame",
    description: {
      ar: "أنشئ صفحات احترافية عالية التأثير بسهولة.",
      en: "Launch high-impact pages effortlessly.",
    },
  },
  {
    title: {
      ar: "تحليلات أوربت",
      en: "Orbit Analytics",
    },
    icon: "ChartScatter",
    description: {
      ar: "رؤى قوية تساعدك على اتخاذ قرارات أذكى.",
      en: "Powerful insights for smarter decisions.",
    },
  },
  {
    title: {
      ar: "مُكامل نوفا",
      en: "Nova Integrator",
    },
    icon: "Blocks",
    description: {
      ar: "تكاملات سلسة مع أدواتك المفضلة.",
      en: "Seamless connections with your favorite tools.",
    },
  },
];