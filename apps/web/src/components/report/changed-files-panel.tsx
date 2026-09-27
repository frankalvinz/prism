"use client";

import { Disclosure, DisclosureButton, DisclosurePanel } from "@headlessui/react";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import type { AnalysisReport, ChangedFile, FileArea, RiskFinding } from "@prism/shared";

import { cn } from "@/lib/utils";

function DiffView({ patch }: { patch: string | null }) {
  if (!patch) {
    return (
      <p className="font-mono text-xs text-muted">
        No patch available (binary or truncated by GitHub).
      </p>
    );
  }

  return (
    <pre className="max-h-96 overflow-auto rounded border border-border bg-panel-2 p-3 font-mono text-[12px] leading-5">
      {patch.split("\n").map((line, i) => {
        const tone =
          line.startsWith("+") && !line.startsWith("+++")
            ? "text-ok"
            : line.startsWith("-") && !line.startsWith("---")
              ? "text-danger"
              : line.startsWith("@@")
                ? "text-secondary"
                : "text-muted";
        const bg =
          line.startsWith("+") && !line.startsWith("+++")
            ? "bg-diff-add"
            : line.startsWith("-") && !line.startsWith("---")
              ? "bg-diff-del"
              : "";
        return (
          <div key={`${i}-${line.slice(0, 24)}`} className={cn(tone, bg)}>
            {line || " "}
          </div>
        );
      })}
    </pre>
  );
}

function fileFindings(file: ChangedFile, risks: RiskFinding[]) {
  return risks.filter(
    (r) =>
      r.file === file.filename ||
      (r.files?.length ? r.files.includes(file.filename) : false),
  );
}

const AREA_ORDER: FileArea[] = [
  "ui",
  "api",
  "service",
  "hooks_state",
  "auth",
  "data_model",
  "database",
  "constants",
  "config",
  "dependency",
  "infra",
  "ci",
  "test",
  "styles",
  "docs",
  "other",
];

function areaLabel(area: string) {
  return area.replaceAll("_", " ");
}

export function ChangedFilesPanel({ report }: { report: AnalysisReport }) {
  const byArea = new Map<FileArea, ChangedFile[]>();
  for (const file of report.pr.changed_files) {
    const area = (file.area ?? "other") as FileArea;
    const list = byArea.get(area) ?? [];
    list.push(file);
    byArea.set(area, list);
  }

  const orderedAreas = [
    ...AREA_ORDER.filter((a) => byArea.has(a)),
    ...[...byArea.keys()].filter((a) => !AREA_ORDER.includes(a)),
  ];

  if (report.pr.changed_files.length === 0) {
    return <p className="text-sm text-muted">No changed files in report.</p>;
  }

  return (
    <Disclosure as="section" className="rounded-xl border border-border bg-panel" defaultOpen={false}>
      <DisclosureButton className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-panel-2">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-foreground">
            Changed files
          </h2>
          <p className="mt-1 text-sm text-muted">
            {report.pr.changed_files.length} files grouped by area
          </p>
        </div>
        <ChevronDownIcon className="h-5 w-5 shrink-0 text-muted" />
      </DisclosureButton>
      <DisclosurePanel className="space-y-5 border-t border-border px-5 py-5">
        {orderedAreas.map((area) => {
          const files = byArea.get(area) ?? [];
          return (
            <div key={area}>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
                {areaLabel(area)}{" "}
                <span className="font-mono text-secondary">({files.length})</span>
              </h3>
              <div className="space-y-2">
                {files.map((file) => {
                  const findings = fileFindings(file, report.risks);
                  const complexity = report.complexity.find((c) => c.file === file.filename);
                  const categories = [...new Set(findings.map((f) => f.category))];
                  return (
                    <Disclosure
                      key={file.filename}
                      as="div"
                      className="rounded-lg border border-border bg-panel-2/40"
                    >
                      <DisclosureButton className="flex w-full items-start justify-between gap-3 px-3 py-3 text-left hover:bg-panel-2">
                        <div className="min-w-0 space-y-1">
                          <div className="truncate font-mono text-sm text-foreground">
                            {file.filename}
                          </div>
                          <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                            <span className="rounded border border-border px-1.5 py-0.5 capitalize">
                              {areaLabel(area)}
                            </span>
                            <span className="capitalize">{file.status}</span>
                            <span className="text-ok">+{file.additions}</span>
                            <span className="text-danger">-{file.deletions}</span>
                            {complexity?.max_cyclomatic_complexity != null &&
                            complexity.max_cyclomatic_complexity >= 10 ? (
                              <span className="rounded border border-warn/40 px-1.5 py-0.5 text-warn">
                                Complexity: High
                              </span>
                            ) : null}
                            {categories.slice(0, 3).map((cat) => (
                              <span
                                key={cat}
                                className="rounded border border-border px-1.5 py-0.5 capitalize"
                              >
                                {cat.replaceAll("_", " ")}
                              </span>
                            ))}
                          </div>
                        </div>
                        <ChevronDownIcon className="mt-1 h-5 w-5 shrink-0 text-muted" />
                      </DisclosureButton>
                      <DisclosurePanel className="space-y-3 border-t border-border px-3 py-3">
                        {findings.length > 0 ? (
                          <ul className="space-y-2">
                            {findings.map((f) => (
                              <li
                                key={f.id}
                                className="rounded border border-border bg-panel p-2"
                              >
                                <div className="mb-1 text-sm font-medium">{f.title}</div>
                                <p className="text-xs text-muted">{f.evidence}</p>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-xs text-muted">No file-scoped findings.</p>
                        )}
                        {complexity ? (
                          <p className="font-mono text-xs text-muted">
                            funcs={complexity.function_count} classes={complexity.class_count}
                            {complexity.max_cyclomatic_complexity != null
                              ? ` max_cc=${complexity.max_cyclomatic_complexity}`
                              : ""}
                          </p>
                        ) : null}
                        <DiffView patch={file.patch} />
                      </DisclosurePanel>
                    </Disclosure>
                  );
                })}
              </div>
            </div>
          );
        })}
      </DisclosurePanel>
    </Disclosure>
  );
}
