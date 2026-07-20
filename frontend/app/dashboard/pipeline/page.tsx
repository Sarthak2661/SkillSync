import { Activity, AlertTriangle, Clock3, History } from "lucide-react";
import { MetricCard, PageHeader, Panel } from "@/components/ui";
import { apiGetSafe } from "@/lib/api";
import { dateTime, labelClass } from "@/lib/format";
import type { Run, SchedulerStatus, SourceRun } from "@/lib/types";

export default async function PipelinePage() {
  const [runs, scheduler, sourceRuns] = await Promise.all([
    apiGetSafe<Run[]>("/runs?limit=100", []),
    apiGetSafe<SchedulerStatus>("/scheduler", { interval_minutes: 1440, run_on_start: true }),
    apiGetSafe<SourceRun[]>("/source-runs?limit=500", []),
  ]);
  const latest = runs[0] ?? {};
  const latestRunId = String(latest.run_id ?? "");
  const latestSourceRuns = sourceRuns.filter((run) => run.run_id === latestRunId);
  const sourceFailures = latestSourceRuns.filter((run) => run.status === "failed").length;

  return (
    <>
      <PageHeader eyebrow="Orchestration" title="Pipeline runs" description="Audit scheduled ingestion, transformation, quality, export, and optional warehouse loading." />
      <div className="metric-grid four">
        <MetricCard label="Runs shown" value={String(runs.length)} detail="Most recent history" icon={History} tone="blue" />
        <MetricCard label="Latest jobs" value={String(latest.job_records ?? 0)} detail="Rows in latest run" icon={Activity} tone="cyan" />
        <MetricCard label="Source failures" value={String(sourceFailures)} detail="Latest pipeline run" icon={AlertTriangle} tone="amber" />
        <MetricCard label="Refresh cadence" value={scheduler.interval_minutes === 1440 ? "Daily" : `${scheduler.interval_minutes} min`} detail={scheduler.run_on_start ? "Runs once on scheduler start" : "Waits for the next interval"} icon={Clock3} tone="green" />
      </div>
      <div className="schedule-strip">
        <span><strong>Last recorded update</strong>{dateTime(scheduler.latest_run_timestamp)}</span>
        <span><strong>Estimated next update</strong>{dateTime(scheduler.estimated_next_run)}</span>
        <small>The estimate is only valid while the local scheduler or Airflow DAG is enabled.</small>
      </div>
      <Panel title="Run history" description="Local scheduler and Airflow executions append to the same pipeline history.">
        <div className="data-table-wrap"><table className="data-table">
          <thead><tr><th>Run</th><th>Timestamp</th><th>Jobs</th><th>Courses</th><th>Skills</th><th>Trend rows</th><th>Top skill</th><th>PostgreSQL</th></tr></thead>
          <tbody>{runs.map((run) => <tr key={String(run.run_id)}><td><strong>{run.run_id}</strong></td><td>{dateTime(run.run_timestamp)}</td><td>{run.job_records}</td><td>{run.course_records}</td><td>{run.unique_skills}</td><td>{run.trend_rows}</td><td>{run.top_opportunity_skill}</td><td><span className={`badge ${String(run.postgres).toLowerCase() === "loaded" ? "success" : "neutral"}`}>{run.postgres}</span></td></tr>)}</tbody>
        </table></div>
      </Panel>
      <Panel title="Source activity" description="Connector outcomes for the latest pipeline run, including isolated network failures.">
        <div className="data-table-wrap"><table className="data-table">
          <thead><tr><th>Source</th><th>Type</th><th>Status</th><th>Rows</th><th>Completed</th><th>Duration</th><th>Error</th></tr></thead>
          <tbody>{latestSourceRuns.map((run) => <tr key={`${run.run_id}-${run.source_name}-${run.started_at}`}><td><strong>{run.source_name}</strong></td><td>{run.source_type.replaceAll("_", " ")}</td><td><span className={labelClass(run.status)}>{run.status}</span></td><td>{run.record_count}</td><td>{dateTime(run.completed_at)}</td><td>{run.duration_ms} ms</td><td>{run.error_type ? `${run.error_type}: ${run.error_message ?? "No details"}` : "-"}</td></tr>)}</tbody>
        </table></div>
      </Panel>
      <div className="pipeline-flow" aria-label="Pipeline task order"><span>Ingest</span><i /><span>Transform</span><i /><span>Quality checks</span><i /><span>Power BI export</span><i /><span>PostgreSQL load</span></div>
    </>
  );
}
