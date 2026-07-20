import { BookOpenCheck, BriefcaseBusiness, Database, RadioTower } from "lucide-react";
import { MetricCard, PageHeader, Panel } from "@/components/ui";
import { apiGetSafe } from "@/lib/api";
import { labelClass } from "@/lib/format";
import { readRoleFamily, readScope, scopeQuery } from "@/lib/scope";
import type { Source } from "@/lib/types";

const catalog = [
  ["Jobs", "Adzuna", "Official API", "live_verified", "API key required"],
  ["Jobs", "Arbeitnow", "Official public API", "live_verified", "No key required"],
  ["Jobs", "Remotive", "Official remote jobs API", "live_verified", "No key required"],
  ["Jobs", "HN Who's Hiring", "Official Algolia HN API", "live_broad", "No key required"],
  ["Jobs", "Curated data snapshot", "Local reproducible dataset", "curated_demo", "Default reliable mode"],
  ["Jobs", "Curated technology-role snapshot", "Local reproducible dataset", "curated_demo", "Default reliable mode"],
  ["Courses", "Microsoft Learn", "Official catalog API", "live_verified", "No key required"],
  ["Courses", "freeCodeCamp curriculum", "Official GitHub curriculum index", "live_verified", "No key required"],
  ["Courses", "GitHub learning paths", "Official repository search API", "live_broad", "Token optional"],
  ["Courses", "Official learning catalog", "Curated vendor resources", "curated_demo", "Local reproducible dataset"],
  ["Courses", "Open course catalog", "Free learning resources", "curated_demo", "Local reproducible dataset"],
  ["Courses", "YouTube", "YouTube Data API", "fallback_learning", "API key optional"],
  ["Courses", "Seed listings", "Offline smoke-test records", "fallback_learning", "Used as fallback"],
  ["Certifications", "Credential Engine Registry", "Official CTDL Search API", "live_verified", "Approved API key required"],
  ["Certifications", "freeCodeCamp certifications", "Official GitHub curriculum index", "live_verified / curated_demo", "No key required in live mode"],
  ["Certifications", "AWS / Microsoft / Google Cloud / Linux Foundation / HashiCorp / Red Hat / Cisco", "Maintained local catalog", "curated_demo", "Manual refresh"],
];

export default async function SourcesPage({ searchParams }: { searchParams: Promise<{ scope?: string; role?: string }> }) {
  const roleFamily = await readRoleFamily(searchParams);
  const scope = await readScope(searchParams);
  const sources = await apiGetSafe<Source[]>(`/sources?${scopeQuery(scope, roleFamily)}`, []);
  const jobRecords = sources.filter((item) => item.dataset === "jobs").reduce((sum, item) => sum + item.record_count, 0);
  const courseRecords = sources.filter((item) => item.dataset === "courses").reduce((sum, item) => sum + item.record_count, 0);
  const verified = sources.filter((item) => item.source_confidence === "live_verified").length;
  return <><PageHeader eyebrow="Data provenance" title="Sources" description="Understand which records are live, curated, fallback, or intended only for parser testing." /><div className="metric-grid four"><MetricCard label="Active sources" value={String(sources.length)} detail="Present in latest run" icon={RadioTower} tone="blue" /><MetricCard label="Job records" value={String(jobRecords)} detail="Across active job sources" icon={BriefcaseBusiness} tone="cyan" /><MetricCard label="Course records" value={String(courseRecords)} detail="Across active learning sources" icon={BookOpenCheck} tone="green" /><MetricCard label="Live verified" value={String(verified)} detail="Official APIs in this run" icon={Database} tone="amber" /></div><Panel title="Active sources in the latest run" description="Confidence describes provenance, not whether every individual record is correct."><div className="data-table-wrap"><table className="data-table"><thead><tr><th>Dataset</th><th>Source</th><th>Confidence</th><th>Records</th></tr></thead><tbody>{sources.map((source) => <tr key={`${source.dataset}-${source.source_name}`}><td>{source.dataset}</td><td><strong>{source.source_name.replaceAll("_", " ")}</strong></td><td><span className={labelClass(source.source_confidence)}>{source.source_confidence?.replaceAll("_", " ") || "unclassified"}</span></td><td>{source.record_count}</td></tr>)}</tbody></table></div></Panel><Panel title="Supported source catalog" description="Live sources can be enabled with environment variables; reliable local defaults avoid network failures on a fresh clone."><div className="data-table-wrap"><table className="data-table"><thead><tr><th>Dataset</th><th>Source</th><th>Access</th><th>Confidence</th><th>Setup</th></tr></thead><tbody>{catalog.map((row) => <tr key={`${row[0]}-${row[1]}`}><td>{row[0]}</td><td><strong>{row[1]}</strong></td><td>{row[2]}</td><td><span className={labelClass(row[3])}>{row[3].replaceAll("_", " ")}</span></td><td>{row[4]}</td></tr>)}</tbody></table></div></Panel><div className="notice warning"><strong>Known limitation:</strong> curated and fallback datasets make the project reproducible, but they are not representative of the whole labor market. Use live API runs and a larger history before making broad market claims.</div></>;
}
