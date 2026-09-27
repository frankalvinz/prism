"use client";

import { Disclosure, DisclosureButton, DisclosurePanel } from "@headlessui/react";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import type { AnalysisReport } from "@prism/shared";

export function TechnicalDetails({ report }: { report: AnalysisReport }) {
  return (
    <Disclosure as="section" className="rounded-xl border border-border bg-panel">
      <DisclosureButton className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-panel-2">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-foreground">
            Technical details
          </h2>
          <p className="mt-1 text-sm text-muted">
            Complexity, dependencies, review questions, and impact graph
          </p>
        </div>
        <ChevronDownIcon className="h-5 w-5 shrink-0 text-muted ui-open:rotate-180" />
      </DisclosureButton>
      <DisclosurePanel className="space-y-6 border-t border-border px-5 py-5">
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
            Complexity
          </h3>
          {report.complexity.length === 0 ? (
            <p className="text-sm text-muted">No complexity observations.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-panel-2 text-[11px] uppercase tracking-wide text-muted">
                  <tr>
                    <th className="px-3 py-2 font-medium">File</th>
                    <th className="px-3 py-2 font-medium">Lang</th>
                    <th className="px-3 py-2 font-medium">Funcs</th>
                    <th className="px-3 py-2 font-medium">Max CC</th>
                  </tr>
                </thead>
                <tbody>
                  {report.complexity.map((c) => (
                    <tr key={c.file} className="border-t border-border">
                      <td className="px-3 py-2 font-mono text-xs">{c.file}</td>
                      <td className="px-3 py-2">{c.language}</td>
                      <td className="px-3 py-2 font-mono">{c.function_count}</td>
                      <td className="px-3 py-2 font-mono">
                        {c.max_cyclomatic_complexity ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
            Testing
          </h3>
          <div className="grid gap-3 rounded-lg border border-border bg-panel-2/40 p-4 sm:grid-cols-3">
            <div>
              <div className="text-xs text-muted">Test files +</div>
              <div className="font-mono text-lg">{report.testing.test_files_added}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Test files modified</div>
              <div className="font-mono text-lg">{report.testing.test_files_modified}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Prod files changed</div>
              <div className="font-mono text-lg">{report.testing.production_files_changed}</div>
            </div>
          </div>
        </div>

        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
            Dependencies
          </h3>
          {report.dependencies.length === 0 ? (
            <p className="text-sm text-muted">No dependency changes detected.</p>
          ) : (
            <ul className="space-y-2">
              {report.dependencies.map((d, idx) => (
                <li
                  key={`${d.file}-${d.name}-${idx}`}
                  className="rounded border border-border bg-panel-2/40 px-3 py-2 font-mono text-sm"
                >
                  <span className="capitalize text-primary">{d.change_type}</span> {d.name}
                  {d.old_version || d.new_version
                    ? ` (${d.old_version ?? "?"} → ${d.new_version ?? "?"})`
                    : ""}
                  <span className="text-muted"> · {d.file}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
            Review questions
          </h3>
          {report.review_questions.length === 0 ? (
            <p className="text-sm text-muted">No contextual review questions for this PR.</p>
          ) : (
            <ol className="list-decimal space-y-2 pl-5 text-sm text-foreground">
              {report.review_questions.map((q) => (
                <li key={q}>{q}</li>
              ))}
            </ol>
          )}
        </div>

        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
            Impact graph
          </h3>
          <p className="mb-2 text-xs text-muted">
            Heuristic relationships between changed files (confidence varies).
          </p>
          {report.dependency_edges.length === 0 ? (
            <p className="text-sm text-muted">No impact edges inferred.</p>
          ) : (
            <ul className="space-y-2">
              {report.dependency_edges.map((e, i) => (
                <li
                  key={`${e.source}-${e.target}-${i}`}
                  className="rounded border border-border bg-panel-2/40 px-3 py-2 font-mono text-xs"
                >
                  <span className="text-foreground">{e.source}</span>
                  <span className="mx-2 text-muted">—{e.relationship}→</span>
                  <span className="text-foreground">{e.target}</span>
                  <span className="ml-2 text-muted">
                    conf {(e.confidence * 100).toFixed(0)}%
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </DisclosurePanel>
    </Disclosure>
  );
}
