import { cn } from "@/lib/utils";

export function Card({
  className,
  children,
  as: Tag = "div",
  style,
}: {
  className?: string;
  children: React.ReactNode;
  as?: "div" | "section" | "article" | "aside" | "header";
  style?: React.CSSProperties;
}) {
  return (
    <Tag className={cn("rounded-xl border border-border bg-panel p-4", className)} style={style}>
      {children}
    </Tag>
  );
}
