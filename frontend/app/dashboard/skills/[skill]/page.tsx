import Link from "next/link";
import { ArrowLeft, BookOpenCheck, BriefcaseBusiness, ExternalLink, Gauge, TrendingUp, WalletCards } from "lucide-react";
import { MetricCard, PageHeader, Panel } from "@/components/ui";
import { apiGetSafe } from "@/lib/api";
import { currency, labelClass } from "@/lib/format";
import { dashboardQuery, readRoleFamily, readScope, scopeQuery } from "@/lib/scope";
import type { SkillProfile } from "@/lib/types";

export default async function SkillDetailPage({ params, searchParams }: { params: Promise<{ skill: string }>; searchParams: Promise<{ scope?: string; role?: string }> }) {
  const { skill: encodedSkill } = await params;
  const scope = await readScope(searchParams);
  const roleFamily = await readRoleFamily(searchParams);
  const skill = decodeURIComponent(encodedSkill);
  const navigation = dashboardQuery(scope, roleFamily);
  const profile = await apiGetSafe<SkillProfile | null>(`/skills/${encodeURIComponent(skill)}?${scopeQuery(scope, roleFamily)}`, null);
  if (!profile?.gap) return <><Link className="back-link" href={`/dashboard/skills?${navigation}`}><ArrowLeft size={15} /> Back to skills</Link><div className="empty-state"><strong>Skill data unavailable</strong><p>The API did not return a profile for {skill} in this data scope.</p></div></>;
  const gap = profile.gap;
  const references = String(gap.onet_reference_url ?? "").split(" | ").filter(Boolean);
  return (
    <>
      <Link className="back-link" href={`/dashboard/skills?${navigation}`}><ArrowLeft size={15} /> Back to skill explorer</Link>
      <PageHeader eyebrow={gap.category} title={profile.skill} description={`Target roles: ${gap.target_job_roles}`} action={<span className={labelClass(gap.opportunity_label)}>{gap.opportunity_label}</span>} />
      <div className="metric-grid four">
        <MetricCard label="Opportunity index" value={String(gap.opportunity_index)} detail="Composite score out of 100" icon={Gauge} tone="blue" />
        <MetricCard label="Job demand" value={String(profile.job_count)} detail={`Demand score ${gap.demand_score}`} icon={BriefcaseBusiness} tone="cyan" />
        <MetricCard label="Course supply" value={String(profile.course_count)} detail={`Supply score ${gap.course_supply_score}`} icon={BookOpenCheck} tone="green" />
        <MetricCard label="Median wage evidence" value={currency(gap.onet_wage_median_annual)} detail={`${gap.bls_growth_percent ?? 0}% projected growth`} icon={WalletCards} tone="amber" />
      </div>

      <Panel title="Why this skill ranks here" description="The score combines market upside with supply and saturation penalties.">
        <div className="score-grid">
          {[['Demand', gap.demand_score], ['Growth', gap.growth_score], ['Salary premium', gap.salary_premium_score], ['Course supply', gap.course_supply_score], ['Saturation', gap.saturation_score]].map(([label, value]) => <div key={String(label)}><span>{label}</span><strong>{value}</strong><i><em style={{ width: `${Number(value)}%` }} /></i></div>)}
        </div>
        <div className="evidence-note"><TrendingUp size={17} /><div><strong>{gap.market_direction} market direction</strong><p>{gap.onet_growth_outlook || "Growth evidence is not available for this mapping."} · O*NET-SOC {gap.onet_soc_codes || "not mapped"}</p></div></div>
        {references.length > 0 && <div className="reference-links">{references.map((url, index) => <a key={url} href={url} target="_blank" rel="noreferrer">Evidence source {index + 1} <ExternalLink size={13} /></a>)}</div>}
      </Panel>

      <Panel title="Matching jobs" description="A sample of postings where the pipeline extracted this skill."><div className="data-table-wrap"><table className="data-table"><thead><tr><th>Role</th><th>Company</th><th>Location</th><th>Work mode</th><th>Salary range</th><th /></tr></thead><tbody>{profile.sample_jobs.map((job) => <tr key={job.external_id}><td><strong>{job.title}</strong></td><td>{job.company}</td><td>{job.location}</td><td>{job.remote_type}</td><td>{job.salary_min ? `${currency(job.salary_min)} – ${currency(job.salary_max)}` : "Not listed"}</td><td>{job.url && <a className="icon-link" href={job.url} target="_blank" rel="noreferrer" aria-label={`Open ${job.title}`}><ExternalLink size={15} /></a>}</td></tr>)}</tbody></table></div></Panel>

      <Panel title="Learning resources" description="Courses and documentation that cover this skill."><div className="resource-list">{profile.sample_courses.map((course) => <article key={course.external_id}><div><span className="badge neutral">{course.level || "Any level"}</span><h3>{course.title}</h3><p>{course.platform} · {course.source_confidence.replaceAll("_", " ")}</p></div><a className="icon-link" href={course.url} target="_blank" rel="noreferrer" aria-label={`Open ${course.title}`}><ExternalLink size={16} /></a></article>)}</div></Panel>
    </>
  );
}
