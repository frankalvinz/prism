"use client";

import { Tab, TabGroup, TabList, TabPanel, TabPanels } from "@headlessui/react";
import type { AnalysisReport } from "@prism/shared";

import { AreaDonut } from "@/components/report/charts/area-donut";
import { ChurnBar } from "@/components/report/charts/churn-bar";
import { FindingsDonut } from "@/components/report/charts/findings-donut";
import { SeverityBar } from "@/components/report/charts/severity-bar";
import type { FindingsFilter } from "@/components/report/use-findings-filter";
import { cn } from "@/lib/utils";

const TABS = ["Issues", "Areas", "Churn", "Severity"] as const;

export function VisualsCard({
  report,
  filter,
}: {
  report: AnalysisReport;
  filter: FindingsFilter;
}) {
  return (
    <section className="rounded-xl border border-border bg-panel p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-foreground">Visuals</h2>
      <TabGroup>
        <TabList className="mt-3 flex flex-wrap gap-1 border-b border-border pb-2">
          {TABS.map((tab) => (
            <Tab
              key={tab}
              className={({ selected }) =>
                cn(
                  "rounded-md px-3 py-1.5 text-sm outline-none",
                  selected
                    ? "bg-panel-2 font-medium text-foreground"
                    : "text-muted hover:text-foreground",
                )
              }
            >
              {tab}
            </Tab>
          ))}
        </TabList>
        <TabPanels className="mt-4">
          <TabPanel>
            <FindingsDonut risks={report.risks} filter={filter} />
          </TabPanel>
          <TabPanel>
            <AreaDonut statistics={report.statistics} />
          </TabPanel>
          <TabPanel>
            <ChurnBar statistics={report.statistics} />
          </TabPanel>
          <TabPanel>
            <SeverityBar risks={report.risks} filter={filter} />
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </section>
  );
}
