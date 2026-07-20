"use client";

import { ExternalLink, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { currency, labelClass } from "@/lib/format";
import type { Certification } from "@/lib/types";

export function CertificationTable({ certifications }: { certifications: Certification[] }) {
  const [query, setQuery] = useState("");
  const [payment, setPayment] = useState("All");
  const filtered = useMemo(
    () => certifications.filter((item) => {
      const text = `${item.skill} ${item.certification_name} ${item.provider} ${item.target_roles}`.toLowerCase();
      return text.includes(query.toLowerCase()) && (payment === "All" || item.free_or_paid === payment);
    }),
    [certifications, payment, query],
  );

  return (
    <>
      <div className="filter-bar">
        <label className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search skills, providers, or roles" /></label>
        <div className="segmented" aria-label="Cost filter">
          {["All", "Free", "Paid"].map((item) => <button key={item} className={payment === item ? "selected" : ""} onClick={() => setPayment(item)}>{item}</button>)}
        </div>
      </div>
      <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Certification</th><th>Skill</th><th>Level</th><th>Cost</th><th>Recommendation</th><th>Target roles</th><th /></tr></thead><tbody>{filtered.map((item) => <tr key={item.certification_name}><td><strong>{item.certification_name}</strong><small>{item.provider}{item.source_confidence ? ` | ${item.source_confidence.replaceAll("_", " ")}` : ""}</small></td><td>{item.skill}</td><td>{item.level}</td><td>{item.free_or_paid === "Free" ? "Free" : currency(item.estimated_cost_usd)}</td><td><span className={labelClass(item.recommendation_score >= 80 ? "high" : "neutral")}>{item.recommendation_score}</span></td><td className="truncate-cell">{item.target_roles}</td><td><a className="icon-link" href={item.url} target="_blank" rel="noreferrer" aria-label={`Open ${item.certification_name}`}><ExternalLink size={15} /></a></td></tr>)}</tbody></table></div>
    </>
  );
}
