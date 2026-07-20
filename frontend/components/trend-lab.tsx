"use client";

import { useMemo, useState } from "react";
import { TrendChart } from "@/components/charts";
import type { Trend } from "@/lib/types";

export function TrendLab({ trends }: { trends: Trend[] }) {
  const options = useMemo(() => Array.from(new Set(trends.map((item) => item.skill))).sort(), [trends]);
  const preferred = ["Python", "SQL", "Power BI", "AWS", "dbt"].filter((skill) => options.includes(skill));
  const [selected, setSelected] = useState<string[]>(preferred.length ? preferred : options.slice(0, 5));
  function toggle(skill: string) { setSelected((current) => current.includes(skill) ? current.filter((item) => item !== skill) : current.length < 5 ? [...current, skill] : current); }
  return <><div className="chip-row" role="group" aria-label="Skills shown in trend chart">{options.map((skill) => <button key={skill} className={`filter-chip ${selected.includes(skill) ? "selected" : ""}`} onClick={() => toggle(skill)}>{skill}</button>)}</div><TrendChart data={trends} skills={selected} /><p className="chart-note">Select up to five skills. Counts are historical snapshots, not unique openings across the entire period.</p></>;
}
