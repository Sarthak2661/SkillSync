import { EmptyState, PageHeader, Panel } from "@/components/ui";
import { SkillsTable } from "@/components/skills-table";
import { apiGetSafe } from "@/lib/api";
import { readRoleFamily, readScope, scopeQuery } from "@/lib/scope";
import type { SkillGap } from "@/lib/types";

export default async function SkillsPage({ searchParams }: { searchParams: Promise<{ scope?: string; role?: string }> }) {
  const scope = await readScope(searchParams);
  const roleFamily = await readRoleFamily(searchParams);
  const skills = await apiGetSafe<SkillGap[]>(`/skill-gaps?limit=1000&${scopeQuery(scope, roleFamily)}`, []);
  return <><PageHeader eyebrow="Skill intelligence" title="Skill explorer" description="Search the market taxonomy, compare demand with learning supply, and inspect the evidence behind each opportunity score." /><Panel title="Market skill index" description="Scores use the latest pipeline output and can change after scheduled runs.">{skills.length ? <SkillsTable skills={skills} scope={scope} roleFamily={roleFamily} /> : <EmptyState title="No skills in this data scope" body="The latest run did not include matching job or course records. Choose another scope or run the pipeline with live sources enabled." />}</Panel></>;
}
