import { AlertTriangle, CheckCircle2, Database, ShieldCheck } from "lucide-react";
import { MetricCard, PageHeader, Panel } from "@/components/ui";
import { apiGetSafe } from "@/lib/api";
import { labelClass } from "@/lib/format";
import type { QualityCheck } from "@/lib/types";

export default async function QualityPage() {
  const checks = await apiGetSafe<QualityCheck[]>("/quality", []);
  const passed = checks.filter((item) => item.status === "pass").length;
  const failed = checks.reduce((sum, item) => sum + item.failed_count, 0);
  const datasets = new Set(checks.map((item) => item.dataset)).size;
  const score = checks.length ? Math.round((passed / checks.length) * 100) : 0;
  return <><PageHeader eyebrow="Data reliability" title="Quality checks" description="See whether the latest jobs, courses, taxonomy, salaries, and source fields are trustworthy enough to interpret." /><div className="metric-grid four"><MetricCard label="Checks passed" value={`${passed}/${checks.length}`} detail="Latest validation run" icon={CheckCircle2} tone="green" /><MetricCard label="Quality score" value={`${score}%`} detail="Share of passing checks" icon={ShieldCheck} tone="blue" /><MetricCard label="Failing records" value={String(failed)} detail="Across all checks" icon={AlertTriangle} tone="amber" /><MetricCard label="Datasets checked" value={String(datasets)} detail="Pipeline output groups" icon={Database} tone="cyan" /></div><Panel title="Validation results" description="High-severity failures should be resolved before the dashboard is used for market claims."><div className="data-table-wrap"><table className="data-table"><thead><tr><th>Dataset</th><th>Check</th><th>Status</th><th>Severity</th><th>Records</th><th>Failed</th><th>Result</th></tr></thead><tbody>{checks.map((item) => <tr key={`${item.dataset}-${item.check_name}`}><td>{item.dataset}</td><td><strong>{item.check_name.replaceAll("_", " ")}</strong></td><td><span className={labelClass(item.status)}>{item.status}</span></td><td><span className={labelClass(item.severity)}>{item.severity}</span></td><td>{item.records_checked}</td><td>{item.failed_count}</td><td>{item.message}</td></tr>)}</tbody></table></div></Panel></>;
}
