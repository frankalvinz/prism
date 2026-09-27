"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { QUICK_START_CHECKS } from "@/constants/content";

export function QuickStartCards({ onDemo }: { onDemo: () => void }) {
  return (
    <aside className="space-y-4">
      <Card as="article">
        <h2 className="mb-1 text-sm font-semibold text-foreground">Try the demo</h2>
        <p className="mb-3 text-sm text-muted">
          Analyze a fixture PR instantly — no GitHub access required.
        </p>
        <Button type="button" variant="secondary" onClick={onDemo}>
          Run demo PR
        </Button>
      </Card>

      <Card as="article">
        <h2 className="mb-2 text-sm font-semibold text-foreground">What PRISM checks</h2>
        <ul className="space-y-1.5 text-sm text-muted">
          {QUICK_START_CHECKS.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Card>

      <Card as="article">
        <h2 className="mb-1 text-sm font-semibold text-foreground">Privacy</h2>
        <p className="text-sm leading-relaxed text-muted">
          PRISM reads PR metadata and diffs only. Tokens stay in an encrypted HttpOnly cookie. Code
          is never cloned or executed.
        </p>
      </Card>
    </aside>
  );
}
