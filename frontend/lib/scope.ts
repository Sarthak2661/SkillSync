const allowedScopes = new Set(["all", "curated", "live", "demo"]);

export const roleFamilies = [
  "Data & Analytics",
  "Software Engineering",
  "AI & Machine Learning",
  "Cloud & Platform",
  "Database",
  "IT & Security",
  "Technology Consulting",
  "Other Technology",
] as const;

const allowedRoleFamilies = new Set<string>(roleFamilies);
type DashboardSearchParams = Promise<{
  scope?: string | string[];
  role?: string | string[];
}>;

export async function readScope(searchParams?: DashboardSearchParams): Promise<string> {
  const params = searchParams ? await searchParams : {};
  const raw = Array.isArray(params.scope) ? params.scope[0] : params.scope;
  return raw && allowedScopes.has(raw) ? raw : "all";
}

export async function readRoleFamily(searchParams?: DashboardSearchParams): Promise<string> {
  const params = searchParams ? await searchParams : {};
  const raw = Array.isArray(params.role) ? params.role[0] : params.role;
  return raw && allowedRoleFamilies.has(raw) ? raw : "";
}

export function scopeQuery(scope: string, roleFamily = ""): string {
  const params = new URLSearchParams({ source_view: scope });
  if (roleFamily) params.set("role_family", roleFamily);
  return params.toString();
}

export function dashboardQuery(scope: string, roleFamily = ""): string {
  const params = new URLSearchParams({ scope });
  if (roleFamily) params.set("role", roleFamily);
  return params.toString();
}
