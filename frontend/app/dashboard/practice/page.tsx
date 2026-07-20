import { PageHeader, Panel } from "@/components/ui";
import { PracticeFinder } from "@/components/practice-finder";
import { apiGetSafe } from "@/lib/api";
import { readRoleFamily, readScope, scopeQuery } from "@/lib/scope";
import type { SkillGap } from "@/lib/types";

export default async function PracticePage({ searchParams }: { searchParams: Promise<{ scope?: string; role?: string }> }) {
  const scope = await readScope(searchParams);
  const roleFamily = await readRoleFamily(searchParams);
  const skills = await apiGetSafe<SkillGap[]>(`/skill-gaps?limit=1000&${scopeQuery(scope, roleFamily)}`, []);
  return <><PageHeader eyebrow="Proof of work" title="Practice projects" description="Find current GitHub issues where a priority skill can be practiced in a real repository." /><Panel title="GitHub-powered recommendations" description="Results use GitHub's public Search API and favor recently updated, beginner-friendly issues."><PracticeFinder skills={skills.map((item) => item.skill)} /></Panel><div className="notice neutral"><strong>Why this matters:</strong> a course shows that you studied a skill; a useful pull request gives you evidence that you applied it.</div></>;
}
