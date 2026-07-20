import { ArrowDownRight, ArrowUpRight, BookOpenCheck, BriefcaseBusiness, CalendarDays, Newspaper, Sparkles } from "lucide-react";
import { EmptyState, MetricCard, PageHeader, Panel } from "@/components/ui";
import { apiGetSafe } from "@/lib/api";
import { dateTime, integer } from "@/lib/format";
import { readRoleFamily, readScope, scopeQuery } from "@/lib/scope";
import type { WeeklyReport } from "@/lib/types";

export default async function ReportsPage({ searchParams }: { searchParams: Promise<{ scope?: string; role?: string }> }) {
  const scope = await readScope(searchParams);
  const roleFamily = await readRoleFamily(searchParams);
  const query = scopeQuery(scope, roleFamily);
  const reports = await apiGetSafe<WeeklyReport[]>(`/weekly-reports?limit=12&${query}`, []);
  const latest = reports[0];

  if (!latest) {
    return <><PageHeader eyebrow="Weekly analysis" title="Market briefings" description="Dated summaries built from the latest retained pipeline snapshot in each week." /><EmptyState title="No weekly briefing is available yet" body="Run the pipeline across at least one retained week. Week-over-week movement appears after a second weekly snapshot." /></>;
  }

  return (
    <>
      <PageHeader eyebrow="Weekly analysis" title="Market briefings" description="A readable archive of demand movement, learning supply, and the limits of each retained snapshot." />
      <article className="report-feature">
        <div className="report-meta"><span><Newspaper size={15} /> {latest.status}</span><time dateTime={latest.published_at}>{dateTime(latest.published_at)}</time></div>
        <div className="report-heading"><div><span className="eyebrow">Week of {new Date(`${latest.week_start}T00:00:00`).toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })}</span><h2>{latest.title}</h2><p>{latest.summary}</p></div><span className="report-signal"><Sparkles size={18} /><small>Top opportunity signal</small><strong>{latest.top_opportunity_skill}</strong></span></div>
        <div className="report-metrics metric-grid">
          <MetricCard label="Jobs in snapshot" value={integer(latest.jobs)} detail="Retained weekly run" icon={BriefcaseBusiness} tone="blue" />
          <MetricCard label="Learning resources" value={integer(latest.courses)} detail="Courses and paths" icon={BookOpenCheck} tone="cyan" />
          <MetricCard label="Skills scored" value={integer(latest.skills)} detail="Technology taxonomy" icon={Sparkles} tone="green" />
          <MetricCard label="Published" value={new Date(latest.published_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })} detail="UTC pipeline timestamp" icon={CalendarDays} tone="amber" />
        </div>
        <p className="report-method">{latest.methodology_note}</p>
      </article>

      <Panel title="What moved this week" description="Change compares the latest retained run in this week with the latest retained run in the previous week.">
        <div className="movement-grid">
          <section><h3><ArrowUpRight size={17} /> Rising demand</h3>{latest.rising_skills.length ? latest.rising_skills.map((item) => <div className="movement-row positive" key={item.skill}><span><strong>{item.skill}</strong><small>{item.previous} to {item.current} mentions</small></span><b>+{item.change}</b></div>) : <p className="muted-copy">A second weekly snapshot is needed before movement can be calculated.</p>}</section>
          <section><h3><ArrowDownRight size={17} /> Cooling demand</h3>{latest.declining_skills.length ? latest.declining_skills.map((item) => <div className="movement-row negative" key={item.skill}><span><strong>{item.skill}</strong><small>{item.previous} to {item.current} mentions</small></span><b>{item.change}</b></div>) : <p className="muted-copy">No declining skill was detected in the comparable snapshots.</p>}</section>
        </div>
      </Panel>

      <Panel title="Leading skills" description="Demand counts from this report's selected weekly snapshot. Opportunity scores reflect the latest scoped model.">
        <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Skill</th><th>Job mentions</th><th>Learning coverage</th><th>Opportunity</th><th>Role families</th></tr></thead><tbody>{latest.top_skills.map((skill) => <tr key={skill.skill}><td><strong>{skill.skill}</strong></td><td>{skill.job_count}</td><td>{skill.course_count}</td><td>{skill.opportunity_index ?? "-"}</td><td>{skill.role_families || "Multiple technology roles"}</td></tr>)}</tbody></table></div>
      </Panel>

      <Panel title="Briefing archive" description="One article is retained for the latest available pipeline run in each calendar week.">
        <div className="report-archive">{reports.map((report) => <article key={report.report_id}><span className="archive-date"><CalendarDays size={15} /> {new Date(`${report.week_start}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</span><h3>{report.title}</h3><p>{report.summary}</p><footer><span>{integer(report.jobs)} jobs</span><span>{integer(report.skills)} skills</span><span>Run {report.run_id}</span></footer></article>)}</div>
      </Panel>
    </>
  );
}
