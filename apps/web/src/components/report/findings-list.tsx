"use client";

import { Disclosure, DisclosureButton, DisclosurePanel } from "@headlessui/react";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import type { RiskCategory, RiskFinding, Severity } from "@prism/shared";

import type { FindingsFilter } from "@/components/report/use-findings-filter";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { cn } from "@/lib/utils";

function chipLabel(value: string) {
  return value.replaceAll("_", " ");
}

export function FindingsList({
  risks,
  filter,
}: {
  risks: RiskFinding[];
  filter: FindingsFilter;
}) {
  const categories = [...new Set(risks.map((r) => r.category))];
  const severities = [...new Set(risks.map((r) => r.severity))] as Severity[];

  const filtered = risks.filter((r) => {
    if (filter.category && r.category !== filter.category) return false;
    if (filter.severity && r.severity !== filter.severity) return false;
    return true;
  });

  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-foreground">Findings</h2>
        <p className="mt-1 text-sm text-muted">
          Grouped by category — pattern indicators, not confirmed vulnerabilities.
        </p>
      </div>

      {risks.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => filter.toggleCategory(cat as RiskCategory)}
              className={cn(
                "rounded border px-2 py-0.5 text-[11px] capitalize",
                filter.category === cat
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-muted hover:text-foreground",
              )}
            >
              {chipLabel(cat)}
            </button>
          ))}
          {severities.map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => filter.toggleSeverity(sev)}
              className={cn(
                "rounded border px-2 py-0.5 text-[11px] capitalize",
                filter.severity === sev
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-muted hover:text-foreground",
              )}
            >
              {sev}
            </button>
          ))}
          {filter.category || filter.severity ? (
            <button
              type="button"
              onClick={filter.clear}
              className="rounded border border-border px-2 py-0.5 text-[11px] text-secondary"
            >
              Clear filters
            </button>
          ) : null}
        </div>
      ) : null}

      {filtered.length === 0 ? (
        <p className="text-sm text-muted">
          {risks.length === 0 ? "No risk indicators detected." : "No findings match the current filters."}
        </p>
      ) : (
        <ul className="space-y-3">
          {filtered.map((risk) => {
            const files = risk.files?.length ? risk.files : risk.file ? [risk.file] : [];
            return (
              <li key={risk.id} className="rounded-lg border border-border bg-panel p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <SeverityBadge severity={risk.severity} />
                  <span className="text-sm font-medium">{risk.title}</span>
                  <span className="font-mono text-[11px] uppercase text-muted">
                    {chipLabel(risk.category)}
                  </span>
                </div>
                <p className="text-sm text-muted">{risk.description}</p>
                {risk.recommendation ? (
                  <p className="mt-2 text-sm text-foreground">
                    <span className="font-medium text-primary">Recommendation:</span>{" "}
                    {risk.recommendation}
                  </p>
                ) : null}
                {risk.evidence ? (
                  <p className="mt-2 font-mono text-xs text-secondary">Evidence: {risk.evidence}</p>
                ) : null}
                {files.length > 0 ? (
                  <Disclosure as="div" className="mt-3">
                    <DisclosureButton className="inline-flex items-center gap-1 text-xs text-muted hover:text-foreground">
                      {files.length} affected file{files.length === 1 ? "" : "s"}
                      <ChevronDownIcon className="h-4 w-4" />
                    </DisclosureButton>
                    <DisclosurePanel className="mt-2 space-y-1">
                      {files.map((f) => (
                        <div key={f} className="font-mono text-xs text-muted">
                          {f}
                        </div>
                      ))}
                    </DisclosurePanel>
                  </Disclosure>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
