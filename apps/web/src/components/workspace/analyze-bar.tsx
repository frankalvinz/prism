"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function AnalyzeBar({
  url,
  onUrlChange,
  onAnalyze,
  onDemo,
  isPending,
  compact = false,
}: {
  url: string;
  onUrlChange: (value: string) => void;
  onAnalyze: () => void;
  onDemo: () => void;
  isPending: boolean;
  compact?: boolean;
}) {
  return (
    <Card
      as="div"
      className={cn("space-y-3", compact && "sticky top-16 z-30 shadow-sm backdrop-blur-sm")}
    >
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          onAnalyze();
        }}
      >
        <label
          htmlFor="pr-url"
          className="block text-xs font-medium uppercase tracking-wide text-muted"
        >
          GitHub pull request URL
        </label>
        <input
          id="pr-url"
          value={url}
          onChange={(e) => onUrlChange(e.target.value)}
          placeholder="https://github.com/owner/repo/pull/123"
          className="w-full rounded-md border border-border bg-panel-2 px-3 py-2.5 font-mono text-sm text-foreground outline-none ring-primary placeholder:text-muted focus:ring-1"
        />
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={isPending || !url.trim()}>
            Analyze PR
          </Button>
          <Button type="button" variant="secondary" disabled={isPending} onClick={onDemo}>
            Try Demo PR
          </Button>
        </div>
      </form>
    </Card>
  );
}
