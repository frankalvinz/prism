"use client";

import { useCallback, useState } from "react";
import type { RiskCategory, Severity } from "@prism/shared";

export function useFindingsFilter() {
  const [category, setCategory] = useState<RiskCategory | null>(null);
  const [severity, setSeverity] = useState<Severity | null>(null);

  const toggleCategory = useCallback((value: RiskCategory) => {
    setCategory((prev) => (prev === value ? null : value));
  }, []);

  const toggleSeverity = useCallback((value: Severity) => {
    setSeverity((prev) => (prev === value ? null : value));
  }, []);

  const clear = useCallback(() => {
    setCategory(null);
    setSeverity(null);
  }, []);

  return {
    category,
    severity,
    setCategory,
    setSeverity,
    toggleCategory,
    toggleSeverity,
    clear,
  };
}

export type FindingsFilter = ReturnType<typeof useFindingsFilter>;
