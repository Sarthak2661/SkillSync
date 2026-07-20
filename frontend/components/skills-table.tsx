"use client";

import Link from "next/link";
import { Search, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";
import { currency, labelClass } from "@/lib/format";
import { dashboardQuery } from "@/lib/scope";
import type { SkillGap } from "@/lib/types";

export function SkillsTable({ skills, scope = "all", roleFamily = "" }: { skills: SkillGap[]; scope?: string; roleFamily?: string }) {
  const categories = ["All categories", ...Array.from(new Set(skills.map((item) => item.category))).sort()];
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All categories");
  const [minimum, setMinimum] = useState(0);
  const filtered = useMemo(() => skills.filter((item) => {
    const matchesQuery = item.skill.toLowerCase().includes(query.toLowerCase()) || item.target_job_roles.toLowerCase().includes(query.toLowerCase());
    const matchesCategory = category === "All categories" || item.category === category;
    return matchesQuery && matchesCategory && item.opportunity_index >= minimum;
  }), [skills, query, category, minimum]);

  return (
    <>
      <div className="filter-bar">
        <label className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search skills or target roles" /></label>
        <label className="select-field"><SlidersHorizontal size={15} /><select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
        <label className="range-field"><span>Minimum score</span><input type="range" min="0" max="100" value={minimum} onChange={(event) => setMinimum(Number(event.target.value))} /><strong>{minimum}</strong></label>
      </div>
      <div className="table-meta"><span>{filtered.length} skills</span><span>Click a skill for jobs, courses, scoring inputs, and wage evidence.</span></div>
      <div className="data-table-wrap">
        <table className="data-table">
          <thead><tr><th>Skill</th><th>Demand</th><th>Supply</th><th>Opportunity</th><th>Wage evidence</th><th>Direction</th></tr></thead>
          <tbody>{filtered.map((item) => (
            <tr key={item.skill}>
              <td><Link className="row-link" href={`/dashboard/skills/${encodeURIComponent(item.skill)}?${dashboardQuery(scope, roleFamily)}`}><strong>{item.skill}</strong><small>{item.category}</small></Link></td>
              <td>{item.job_demand}</td><td>{item.course_supply}</td>
              <td><span className={labelClass(item.opportunity_label)}>{item.opportunity_index} · {item.opportunity_label}</span></td>
              <td>{currency(item.onet_wage_median_annual)}</td><td>{item.market_direction}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </>
  );
}
