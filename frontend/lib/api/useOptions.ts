"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiErrorMessage } from "./client";
import { getLanguages, getModels, getModes } from "./endpoints";
import type { ModelOptions, Option } from "./types";

export type AppOptions = {
  languages: Option[];
  modes: Option[];
  models: ModelOptions;
};

const EMPTY_MODELS: ModelOptions = { recognition: [], translation: [] };

/**
 * Loads every dropdown's options. Each list loads independently, so one failing request
 * leaves the others usable instead of blocking the page; `error` describes what failed.
 */
export function useOptions() {
  const [options, setOptions] = useState<AppOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let isCurrent = true;
    Promise.allSettled([getLanguages(), getModes(), getModels()]).then(([languages, modes, models]) => {
      if (!isCurrent) return;
      setOptions({
        languages: languages.status === "fulfilled" ? languages.value : [],
        modes: modes.status === "fulfilled" ? modes.value : [],
        models: models.status === "fulfilled" ? models.value : EMPTY_MODELS,
      });
      const failure = [languages, modes, models].find((result) => result.status === "rejected");
      setError(failure ? getApiErrorMessage(failure.reason, "Some options could not be loaded.") : null);
    });
    return () => {
      isCurrent = false;
    };
  }, [attempt]);

  const retry = useCallback(() => setAttempt((current) => current + 1), []);

  return { options, error, retry };
}
