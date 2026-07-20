import Link from "next/link";
import { Activity, ArrowRight, BookOpenCheck, BriefcaseBusiness, Database, ShieldAlert, Sparkles, TrendingUp } from "lucide-react";
import { DemandSupplyChart, OpportunityChart } from "@/components/charts";
import { EmptyState, MetricCard, PageHeader, Panel } from "@/components/ui";
import { apiGetSafe } from "@/lib/api";
import { integer, labelClass, percent } from "@/lib/format";
import { dashboardQuery, readRoleFamily, readScope, scopeQuery } from "@/lib/scope";
import type { Kpis, SkillGap, Source } from "@/lib/types";

const emptyKpis: Kpis = { run_id: "", job_postings: 0, course_listings: 0, unique_skills: 0, high_opportunity_skills: 0, high_value_skills: 0, historical_runs_available: 0, quality_warnings: 0, job_skill_coverage: 0, course_skill_coverage: 0, top_opportunity_skill: "Not available" };

export default async function OverviewPage({ searchParams }: { searchParams: Promise<{ scope?: string; role?: string }> }) {
  const scope = await readScope(searchParams);
  const roleFamily = await readRoleFamily(searchParams);
  const query = scopeQuery(scope, roleFamily);
  const navigation = dashboardQuery(scope, roleFamily);
  const [kpis, skills, sources] = await Promise.all([
    apiGetSafe<Kpis>(`/kpis?${query}`, emptyKpis),
    apiGetSafe<SkillGap[]>(`/skill-gaps?limit=100&${query}`, []),
    apiGetSafe<Source[]>(`/sources?${query}`, []),
  ]);
  return (
    <>
      <PageHeader eyebrow="Market overview" title="Technology job intelligence" description="A current view of skill demand, learning supply, wage evidence, and pipeline confidence." action={<Link className="button primary" href={`/dashboard/skills?${navigation}`}>Explore skills <ArrowRight size={15} /></Link>} />
      <div className="metric-grid">
        <MetricCard label="Jobs tracked" value={integer(kpis.job_postings)} detail={`${percent(kpis.job_skill_coverage)} include extracted skills`} icon={BriefcaseBusiness} tone="blue" />
        <MetricCard label="Learning resources" value={integer(kpis.course_listings)} detail={`${percent(kpis.course_skill_coverage)} include skill coverage`} icon={BookOpenCheck} tone="cyan" />
        <MetricCard label="Skills scored" value={integer(kpis.unique_skills)} detail={`${kpis.high_opportunity_skills} high-opportunity signals`} icon={Sparkles} tone="green" />
        <MetricCard label="Quality alerts" value={integer(kpis.quality_warnings)} detail={kpis.quality_warnings ? "Review before interpretation" : "Latest checks passed"} icon={ShieldAlert} tone="amber" />
      </div>

      <div className="overview-callout"><div><span className="callout-icon"><TrendingUp size={19} /></span><div><span>Strongest current signal</span><strong>{kpis.top_opportunity_skill}</strong></div></div><p>Opportunity combines demand, growth, wage premium, learning supply, and market saturation. Treat it as prioritization evidence, not a hiring forecast.</p></div>

      <div className="stacked-panels">
        <Panel title="Skill opportunity ranking" description="Highest composite scores in the latest processed snapshot." action={<Link className="text-link" href={`/dashboard/skills?${navigation}`}>Open full table <ArrowRight size={14} /></Link>}>{skills.length ? <OpportunityChart data={skills} /> : <EmptyState title="No market records in this scope" body="Choose another data scope or run the pipeline with the required live sources enabled." />}</Panel>
        <Panel title="Demand compared with learning supply" description="A visible gap can point to skills worth investigating further.">{skills.length ? <DemandSupplyChart data={skills} /> : <EmptyState title="Nothing to compare yet" body="Demand and learning supply will appear after matching records are ingested." />}</Panel>
      </div>

      <Panel title="Priority skills" description="The highest-ranked skills with the role and wage context behind each score.">
        <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Skill</th><th>Category</th><th>Demand</th><th>Supply</th><th>Opportunity</th><th>Target roles</th></tr></thead><tbody>{skills.slice(0, 10).map((skill) => <tr key={skill.skill}><td><Link className="table-link" href={`/dashboard/skills/${encodeURIComponent(skill.skill)}?${navigation}`}>{skill.skill}</Link></td><td>{skill.category}</td><td>{skill.job_demand}</td><td>{skill.course_supply}</td><td><span className={labelClass(skill.opportunity_label)}>{skill.opportunity_index} · {skill.opportunity_label}</span></td><td className="truncate-cell">{skill.target_job_roles}</td></tr>)}</tbody></table></div>
      </Panel>

      <div className="system-strip"><div><Database size={17} /><span><strong>{sources.length} active dataset sources</strong><small>Latest run {kpis.run_id || "not available"}</small></span></div><div><Activity size={17} /><span><strong>{kpis.historical_runs_available} runs retained</strong><small>Trend history available in the Trend Lab</small></span></div><Link className="text-link" href="/dashboard/pipeline">View pipeline <ArrowRight size={14} /></Link></div>
    </>
  );
}
