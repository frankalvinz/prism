"use client";

import type { AnalysisReport } from "@prism/shared";

import { ActionItems } from "@/components/report/action-items";
import { ChangedFilesPanel } from "@/components/report/changed-files-panel";
import { FindingsList } from "@/components/report/findings-list";
import { MetricsRow } from "@/components/report/metrics-row";
import { PrHeader } from "@/components/report/pr-header";
import { TechnicalDetails } from "@/components/report/technical-details";
import { useFindingsFilter } from "@/components/report/use-findings-filter";
import { VerdictCard } from "@/components/report/verdict-card";
import { VisualsCard } from "@/components/report/visuals-card";

export function AnalysisDashboard({ report }: { report: AnalysisReport }) {
  const filter = useFindingsFilter();

  return (
    <div className="space-y-8">
      <PrHeader report={report} />
      <VerdictCard review={report.review} />
      <ActionItems items={report.review?.action_items ?? []} />
      <MetricsRow report={report} />
      <VisualsCard report={report} filter={filter} />
      <FindingsList risks={report.risks} filter={filter} />
      <ChangedFilesPanel report={report} />
      <TechnicalDetails report={report} />
    </div>
  );
}
