import type { LucideIcon } from "lucide-react";

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return (
    <div className="page-header">
      <div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>
      {action && <div className="page-action">{action}</div>}
    </div>
  );
}

export function MetricCard({ label, value, detail, icon: Icon, tone = "blue" }: { label: string; value: string; detail: string; icon: LucideIcon; tone?: "blue" | "green" | "amber" | "cyan" }) {
  return (
    <div className={`metric-card tone-${tone}`}>
      <div className="metric-top"><span>{label}</span><Icon size={17} /></div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return <div className="empty-state"><strong>{title}</strong><p>{body}</p></div>;
}

export function Panel({ title, description, children, action }: { title: string; description?: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <section className="panel">
      <div className="panel-head"><div><h2>{title}</h2>{description && <p>{description}</p>}</div>{action}</div>
      {children}
    </section>
  );
}
