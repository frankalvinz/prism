import { cn } from "@/lib/utils";

const TONES = {
  danger: "border-danger/40 bg-danger/10 text-danger",
  warn: "border-warn/40 bg-warn/10 text-warn",
  info: "border-border bg-panel text-muted",
} as const;

export function Alert({
  tone = "info",
  className,
  children,
  role = "status",
}: {
  tone?: keyof typeof TONES;
  className?: string;
  children: React.ReactNode;
  role?: "status" | "alert";
}) {
  return (
    <div
      className={cn("rounded-lg border px-3 py-2 text-sm", TONES[tone], className)}
      role={role}
    >
      {children}
    </div>
  );
}
