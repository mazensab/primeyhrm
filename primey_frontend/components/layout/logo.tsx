import Link from "next/link";
import Image from "next/image";
import React from "react";

export default function Logo() {
  return (
    <Link href="/" className="flex items-center px-2 py-1">
      <div className="flex items-center rounded-lg bg-transparent px-3 py-2">
        <Image
          src="/logo/primey.svg"
          alt="Primey HR Cloud"
          width={120}
          height={32}
          priority
          className="object-contain"
        />
      </div>
    </Link>
  );
}