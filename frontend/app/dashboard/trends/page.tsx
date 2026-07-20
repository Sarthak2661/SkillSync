import { CalendarDays, History, MapPin, TimerReset } from "lucide-react";
import { PageHeader, MetricCard, Panel } from "@/components/ui";
import { TrendLab } from "@/components/trend-lab";
import { apiGetSafe } from "@/lib/api";
import { dateTime, integer } from "@/lib/format";
import { readRoleFamily, readScope, scopeQuery } from "@/lib/scope";
import type { Kpis, Trend } from "@/lib/types";

export default async function TrendsPage({ searchParams }: { searchParams: Promise<{ scope?: string; role?: string }> }) {
  const scope = await readScope(searchParams);
  const roleFamily = await readRoleFamily(searchParams);
  const query = scopeQuery(scope, roleFamily);
  const [trends, kpis] = await Promise.all([apiGetSafe<Trend[]>(`/skill-trends?limit=10000&${query}`, []), apiGetSafe<Partial<Kpis>>(`/kpis?${query}`, {})]);
  const seriesMap = new Map<string, Trend>();
  for (const row of trends) {
    const key = `${row.run_id}|${row.skill}`;
    const current = seriesMap.get(key);
    if (current) {
      current.job_count += row.job_count;
      current.course_count = Math.max(current.course_count, row.course_count);
    } else {
      seriesMap.set(key, { ...row, source_name: "all", location: "All locations", role_category: "All technology roles" });
    }
  }
  const trendSeries = Array.from(seriesMap.values());
  const timestamps = trends.map((item) => new Date(item.run_timestamp).getTime()).filter(Number.isFinite);
  const roles = new Set(trends.map((item) => item.role_category).filter(Boolean));
  const locations = new Set(trends.map((item) => item.location).filter(Boolean));
  return <><PageHeader eyebrow="Historical snapshots" title="Market trends" description="Track how skill demand changes across pipeline runs, sources, locations, and role categories." /><div className="metric-grid four"><MetricCard label="Runs available" value={integer(kpis.historical_runs_available)} detail="Saved pipeline snapshots" icon={History} tone="blue" /><MetricCard label="First snapshot" value={timestamps.length ? new Date(Math.min(...timestamps)).toLocaleDateString() : "Not available"} detail="Beginning of visible history" icon={CalendarDays} tone="cyan" /><MetricCard label="Role categories" value={String(roles.size)} detail="Classified role families" icon={TimerReset} tone="green" /><MetricCard label="Locations" value={String(locations.size)} detail="Locations represented" icon={MapPin} tone="amber" /></div><Panel title="Skill demand over time" description="Choose up to five skills to compare their job counts across saved runs."><TrendLab trends={trendSeries} /></Panel><Panel title="Latest trend records" description="The most recent location and role-level observations written by the pipeline."><div className="data-table-wrap"><table className="data-table"><thead><tr><th>Timestamp</th><th>Skill</th><th>Jobs</th><th>Courses</th><th>Role category</th><th>Location</th><th>Source</th></tr></thead><tbody>{trends.slice(-50).reverse().map((row, index) => <tr key={`${row.run_id}-${row.skill}-${index}`}><td>{dateTime(row.run_timestamp)}</td><td><strong>{row.skill}</strong></td><td>{row.job_count}</td><td>{row.course_count}</td><td>{row.role_category}</td><td>{row.location}</td><td>{row.source_name}</td></tr>)}</tbody></table></div></Panel></>;
}
