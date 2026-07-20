import { AppShell } from "@/components/app-shell";
import { apiGetSafe } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const health = await apiGetSafe<{ status: string; latest_run_id?: string }>("/health", { status: "offline" });
  return <AppShell apiReady={health.status === "ok"} runId={health.latest_run_id}>{children}</AppShell>;
}
