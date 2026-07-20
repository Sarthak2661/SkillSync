"use client";

import { ExternalLink, GitBranch, LoaderCircle, Search } from "lucide-react";
import { useState } from "react";
import type { PracticeResponse } from "@/lib/types";

export function PracticeFinder({ skills }: { skills: string[] }) {
  const [skill, setSkill] = useState(skills[0] ?? "dbt");
  const [result, setResult] = useState<PracticeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (skills.length === 0) {
    return <div className="empty-state compact"><strong>No skills in this data scope</strong><p>Choose All sources, Curated snapshot, or Demo-safe data to search for practice issues.</p></div>;
  }

  async function search() {
    setLoading(true); setError("");
    try {
      const response = await fetch(`/api/skillsync/practice-projects?skill=${encodeURIComponent(skill)}&limit=10`);
      if (!response.ok) throw new Error("The GitHub practice service did not respond.");
      setResult(await response.json() as PracticeResponse);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Practice projects could not be loaded.");
    } finally { setLoading(false); }
  }

  return (
    <div className="practice-finder">
      <div className="practice-search">
        <label><Search size={16} /><select value={skill} onChange={(event) => setSkill(event.target.value)}>{skills.map((item) => <option key={item}>{item}</option>)}</select></label>
        <button className="button primary" onClick={search} disabled={loading}>{loading ? <LoaderCircle className="spin" size={16} /> : <GitBranch size={16} />} Find open issues</button>
      </div>
      {error && <div className="notice danger">{error}</div>}
      {result && result.status !== "ok" && <div className="notice warning">{result.message}</div>}
      {result && result.status === "ok" && (
        <>
          <div className="table-meta"><span>GitHub topic: {result.topic}</span><span>{result.authenticated ? "Authenticated API" : "Public API"}{result.rate_limit_remaining != null ? ` · ${result.rate_limit_remaining} searches left` : ""}</span></div>
          {result.items.length === 0 ? <div className="empty-state"><strong>No matching issues today</strong><p>{result.message}</p></div> : (
            <div className="issue-list">{result.items.map((item) => (
              <article className="issue-row" key={item.issue_url}>
                <div><span className="badge neutral">{item.practice_label}</span><h3>{item.issue_title}</h3><p>{item.repository} · {item.language || "Language not listed"} · {item.stars} stars</p></div>
                <a className="icon-link" href={item.issue_url} target="_blank" rel="noreferrer" aria-label={`Open ${item.issue_title}`}><ExternalLink size={17} /></a>
              </article>
            ))}</div>
          )}
        </>
      )}
      {!result && !loading && <div className="empty-state compact"><strong>Turn a skill gap into visible work</strong><p>Select a skill to find recently updated repositories with beginner-friendly issues.</p></div>}
    </div>
  );
}
