"use client";

import Image from "next/image";
import Link from "next/link";

export default function LogoIcon() {
  return (
    <Link href="/" className="flex items-center">
      <Image
        src="/logo/primey-icon.ico"
        alt="Primey"
        width={40}
        height={40}
        className="h-10 w-10 rounded-xl object-cover"
        priority
      />
    </Link>
  );
}