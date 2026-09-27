"use client";

import { Tab, TabGroup, TabList, TabPanel, TabPanels } from "@headlessui/react";
import { ArrowPathIcon } from "@heroicons/react/24/outline";
import type { OpenPullRequest, PullRequestFilter } from "@prism/shared";
import { useState } from "react";

import { SignInWithGitHub } from "@/components/auth/sign-in-with-github";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useViewer } from "@/lib/api/auth-client";
import { useMyPullRequests } from "@/lib/api/pull-requests-client";
import { cn } from "@/lib/utils";

const FILTERS: { id: PullRequestFilter; label: string }[] = [
  { id: "authored", label: "Authored" },
  { id: "review_requested", label: "Review requested" },
  { id: "assigned", label: "Assigned" },
];

function relativeTime(iso: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

function SkeletonRows() {
  return (
    <div className="space-y-2">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="h-16 animate-pulse rounded-lg border border-border bg-panel-2"
        />
      ))}
    </div>
  );
}

function PrRow({
  item,
  onAnalyze,
  disabled,
}: {
  item: OpenPullRequest;
  onAnalyze: (htmlUrl: string) => void;
  disabled: boolean;
}) {
  return (
    <li className="flex flex-wrap items-start justify-between gap-3 rounded-lg border border-border bg-panel-2 px-3 py-3">
      <div className="min-w-0 space-y-1">
        <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] text-muted">
          <span>
            {item.owner}/{item.repo} #{item.number}
          </span>
          {item.draft ? (
            <span className="rounded border border-warn/40 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-warn">
              Draft
            </span>
          ) : null}
          {item.updated_at ? <span>{relativeTime(item.updated_at)}</span> : null}
        </div>
        <p className="truncate text-sm font-medium text-foreground">{item.title}</p>
        {item.labels.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {item.labels.slice(0, 4).map((label) => (
              <span
                key={label}
                className="rounded border border-border px-1.5 py-0.5 text-[10px] text-muted"
              >
                {label}
              </span>
            ))}
          </div>
        ) : null}
      </div>
      <Button
        type="button"
        variant="secondary"
        className="shrink-0 !px-3 !py-1.5 !text-xs"
        disabled={disabled}
        onClick={() => onAnalyze(item.html_url)}
      >
        Analyze
      </Button>
    </li>
  );
}

function FilterPanel({
  filter,
  onAnalyze,
  isPending,
}: {
  filter: PullRequestFilter;
  onAnalyze: (htmlUrl: string) => void;
  isPending: boolean;
}) {
  const query = useMyPullRequests(filter);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted">
          {query.isFetching
            ? "Refreshing…"
            : query.data
              ? `${query.data.items.length} open`
              : ""}
        </p>
        <button
          type="button"
          aria-label="Refresh pull requests"
          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border text-muted hover:text-foreground"
          disabled={query.isFetching}
          onClick={() => void query.refetch()}
        >
          <ArrowPathIcon className={cn("h-4 w-4", query.isFetching && "animate-spin")} />
        </button>
      </div>

      {query.isLoading ? <SkeletonRows /> : null}

      {query.isError ? (
        <Alert tone="danger">
          {(query.error as Error)?.message || "Failed to load pull requests."}
        </Alert>
      ) : null}

      {query.data && query.data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-sm text-muted">
          No open pull requests in this view.
        </p>
      ) : null}

      {query.data && query.data.items.length > 0 ? (
        <ul className="space-y-2">
          {query.data.items.map((item) => (
            <PrRow
              key={`${item.owner}/${item.repo}#${item.number}`}
              item={item}
              onAnalyze={onAnalyze}
              disabled={isPending}
            />
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function MyPullRequestsPanel({
  onAnalyze,
  isPending,
}: {
  onAnalyze: (htmlUrl: string) => void;
  isPending: boolean;
}) {
  const { viewer, isLoading } = useViewer();
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (isLoading) {
    return (
      <Card as="section">
        <h2 className="mb-4 text-sm font-semibold text-foreground">Your open pull requests</h2>
        <SkeletonRows />
      </Card>
    );
  }

  if (!viewer?.authenticated) {
    return (
      <Card as="section" className="p-5">
        <h2 className="mb-2 text-sm font-semibold text-foreground">Your open pull requests</h2>
        <p className="mb-4 text-sm text-muted">
          Sign in with GitHub to see PRs you authored, were asked to review, or were assigned.
        </p>
        <SignInWithGitHub />
      </Card>
    );
  }

  return (
    <Card as="section">
      <h2 className="mb-4 text-sm font-semibold text-foreground">Your open pull requests</h2>
      <TabGroup selectedIndex={selectedIndex} onChange={setSelectedIndex}>
        <TabList className="mb-4 flex flex-wrap gap-1 rounded-lg border border-border bg-panel-2 p-1">
          {FILTERS.map((filter) => (
            <Tab
              key={filter.id}
              className="rounded-md px-3 py-1.5 text-xs font-medium text-muted outline-none data-selected:bg-panel data-selected:text-foreground data-selected:shadow-sm"
            >
              {filter.label}
            </Tab>
          ))}
        </TabList>
        <TabPanels>
          {FILTERS.map((filter) => (
            <TabPanel key={filter.id}>
              <FilterPanel filter={filter.id} onAnalyze={onAnalyze} isPending={isPending} />
            </TabPanel>
          ))}
        </TabPanels>
      </TabGroup>
    </Card>
  );
}
