"use client";

import Image from "next/image";

import { SPECTRUM } from "@/constants/theme";
import { Routes } from "@/constants/routes";

export function LogoStage() {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-stage p-6 sm:p-8">
      <div
        className="pointer-events-none absolute inset-0 animate-glow-pulse"
        style={{
          background:
            "radial-gradient(ellipse at 45% 45%, var(--stage-glow-1), transparent 55%), radial-gradient(ellipse at 70% 40%, var(--stage-glow-2), transparent 50%)",
        }}
      />

      <div className="relative grid gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <div className="relative animate-float">
          <Image
            src={Routes.assets_logoLong}
            alt="PRISM — GitHub PR analyzer"
            width={960}
            height={420}
            className="mx-auto h-auto w-full max-w-xl object-contain"
            priority
          />
          <div
            className="pointer-events-none absolute left-[8%] top-[42%] h-px w-[28%] origin-left animate-beam bg-linear-to-r from-transparent via-white/70 to-transparent"
            aria-hidden
          />
        </div>

        <ul className="space-y-3">
          {SPECTRUM.map((item, index) => (
            <li
              key={item.label}
              className="animate-fade-up flex items-center gap-3 rounded-lg border border-white/10 bg-white/5 px-3 py-2.5"
              style={{ animationDelay: `${120 + index * 90}ms` }}
            >
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{
                  backgroundColor: item.colorVar,
                  boxShadow: `0 0 12px ${item.colorVar}`,
                }}
              />
              <span className="text-sm text-white/90">{item.label}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
