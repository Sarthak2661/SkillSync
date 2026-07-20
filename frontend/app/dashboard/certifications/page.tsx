import { BadgeCheck, CircleDollarSign, GraduationCap, Sparkles } from "lucide-react";
import { CertificationTable } from "@/components/certification-table";
import { MetricCard, PageHeader, Panel } from "@/components/ui";
import { apiGetSafe } from "@/lib/api";
import { readRoleFamily, readScope, scopeQuery } from "@/lib/scope";
import type { Certification } from "@/lib/types";

export default async function CertificationsPage({ searchParams }: { searchParams: Promise<{ scope?: string; role?: string }> }) {
  const scope = await readScope(searchParams);
  const roleFamily = await readRoleFamily(searchParams);
  const certifications = await apiGetSafe<Certification[]>(`/certifications?limit=1000&${scopeQuery(scope, roleFamily)}`, []);
  const free = certifications.filter((item) => item.free_or_paid === "Free").length;
  const providers = new Set(certifications.map((item) => item.provider)).size;
  const average = certifications.length ? Math.round(certifications.reduce((sum, item) => sum + item.recommendation_score, 0) / certifications.length) : 0;
  return <><PageHeader eyebrow="Learning path" title="Certifications" description="Compare credentials by skill priority, cost, role relevance, provenance, and current market opportunity." /><div className="metric-grid four"><MetricCard label="Recommendations" value={String(certifications.length)} detail="Catalog matches" icon={BadgeCheck} tone="blue" /><MetricCard label="Free options" value={String(free)} detail="No exam cost listed" icon={CircleDollarSign} tone="green" /><MetricCard label="Providers" value={String(providers)} detail="Credential organizations" icon={GraduationCap} tone="cyan" /><MetricCard label="Average fit" value={String(average)} detail="Recommendation score" icon={Sparkles} tone="amber" /></div><Panel title="Certification paths" description="Recommendations combine credential relevance with the selected skill's market priority."><CertificationTable certifications={certifications} /></Panel></>;
}
