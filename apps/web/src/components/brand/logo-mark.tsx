"use client";

import Image from "next/image";
import Link from "next/link";

import { Routes } from "@/constants/routes";
import { cn } from "@/lib/utils";

export function LogoMark({
  className,
  size = 36,
  showWordmark = true,
}: {
  className?: string;
  size?: number;
  showWordmark?: boolean;
}) {
  return (
    <Link
      href={Routes.home}
      className={cn("inline-flex items-center gap-2.5 no-underline", className)}
      aria-label="PRISM home"
    >
      <span
        className="relative shrink-0 overflow-hidden rounded-md border border-border bg-stage-mark"
        style={{ width: size, height: size }}
      >
        <Image
          src={Routes.assets_logoShort}
          alt=""
          width={size}
          height={size}
          className="h-full w-full object-cover"
          priority
        />
      </span>
      {showWordmark ? (
        <span className="text-sm font-semibold tracking-[0.18em] text-foreground">PRISM</span>
      ) : null}
    </Link>
  );
}
