"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import {
  Activity,
  BadgeCheck,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  ChevronLeft,
  Database,
  GitBranch,
  LayoutDashboard,
  Menu,
  Newspaper,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { roleFamilies } from "@/lib/scope";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/skills", label: "Skill explorer", icon: Search },
  { href: "/dashboard/trends", label: "Market trends", icon: BarChart3 },
  { href: "/dashboard/reports", label: "Weekly briefings", icon: Newspaper },
  { href: "/dashboard/practice", label: "Practice projects", icon: GitBranch },
  { href: "/dashboard/certifications", label: "Certifications", icon: BadgeCheck },
  { href: "/dashboard/quality", label: "Data quality", icon: ShieldCheck },
];

const systemItems = [
  { href: "/dashboard/sources", label: "Sources", icon: Database },
  { href: "/dashboard/pipeline", label: "Pipeline runs", icon: Activity },
];

function NavLink({ href, label, icon: Icon, onClick }: (typeof navItems)[number] & { onClick?: () => void }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const scope = searchParams.get("scope") ?? "all";
  const role = searchParams.get("role") ?? "";
  const query = new URLSearchParams({ scope });
  if (role) query.set("role", role);
  const active = href === "/dashboard" ? pathname === href : pathname.startsWith(href);
  return (
    <Link className={`nav-link ${active ? "active" : ""}`} href={`${href}?${query.toString()}`} onClick={onClick}>
      <Icon size={17} strokeWidth={1.8} />
      <span>{label}</span>
    </Link>
  );
}

export function AppShell({ children, apiReady, runId }: { children: React.ReactNode; apiReady: boolean; runId?: string }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const scope = searchParams.get("scope") ?? "all";
  const scopeEnabled = !pathname.startsWith("/dashboard/quality") && !pathname.startsWith("/dashboard/pipeline");
  const role = searchParams.get("role") ?? "";
  function changeScope(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("scope", value);
    router.replace(`${pathname}?${params.toString()}`);
  }
  function changeRole(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set("role", value);
    else params.delete("role");
    router.replace(`${pathname}?${params.toString()}`);
  }

  return (
    <div className="app-shell">
      <button className="mobile-menu" onClick={() => setOpen(true)} aria-label="Open navigation">
        <Menu size={20} />
      </button>
      {open && <button className="sidebar-backdrop" onClick={() => setOpen(false)} aria-label="Close navigation" />}
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-head">
          <Link href="/" className="brand" onClick={() => setOpen(false)}>
            <span className="brand-mark"><BarChart3 size={17} /></span>
            <span>SkillSync</span>
          </Link>
          <button className="sidebar-close" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>
        <div className="workspace-pill">
          <span className="workspace-icon"><BriefcaseBusiness size={16} /></span>
          <span><strong>Technology careers</strong><small>Market workspace</small></span>
        </div>
        <nav aria-label="Dashboard">
          <span className="nav-heading">Workspace</span>
          {navItems.map((item) => <NavLink key={item.href} {...item} onClick={() => setOpen(false)} />)}
          <span className="nav-heading system">System</span>
          {systemItems.map((item) => <NavLink key={item.href} {...item} onClick={() => setOpen(false)} />)}
        </nav>
        <div className="sidebar-foot">
          <div className={`api-state ${apiReady ? "ready" : "offline"}`}><span />{apiReady ? "API connected" : "API unavailable"}</div>
          {runId && <small>Run {runId}</small>}
          <Link href="/methodology"><BookOpen size={15} /> Methodology</Link>
          <Link href="/"><ChevronLeft size={15} /> Back to site</Link>
        </div>
      </aside>
      <main className="app-main">
        <header className="app-topbar">
          <div><span className="eyebrow"><Sparkles size={13} /> Technology market workspace</span></div>
          <div className="topbar-actions">
            {scopeEnabled && <label className="scope-control"><span>Data scope</span><select value={scope} onChange={(event) => changeScope(event.target.value)}><option value="all">All sources</option><option value="curated">Curated snapshot</option><option value="live">Live sources only</option><option value="demo">Demo-safe data</option></select></label>}
            {scopeEnabled && <label className="scope-control"><span>Role family</span><select value={role} onChange={(event) => changeRole(event.target.value)}><option value="">All technology roles</option>{roleFamilies.map((family) => <option key={family} value={family}>{family}</option>)}</select></label>}
            <a className="text-link" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API docs</a>
          </div>
        </header>
        <div className="app-content">{children}</div>
      </main>
    </div>
  );
}
