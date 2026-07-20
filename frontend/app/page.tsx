import Link from "next/link";
import { ArrowRight, BarChart3, BookOpenCheck, BriefcaseBusiness, Code2, DatabaseZap, GitBranch, Newspaper, ShieldCheck, TrendingUp } from "lucide-react";
import { apiGetSafe } from "@/lib/api";
import { integer } from "@/lib/format";
import type { Kpis } from "@/lib/types";

export const dynamic = "force-dynamic";

const fallback: Kpis = { run_id: "", job_postings: 0, course_listings: 0, unique_skills: 0, high_opportunity_skills: 0, high_value_skills: 0, historical_runs_available: 0, quality_warnings: 0, job_skill_coverage: 0, course_skill_coverage: 0, top_opportunity_skill: "Not available" };

export default async function LandingPage() {
  const kpis = await apiGetSafe<Kpis>("/kpis", fallback);
  return (
    <main className="landing">
      <nav className="site-nav">
        <Link href="/" className="brand"><span className="brand-mark"><BarChart3 size={17} /></span><span>SkillSync</span></Link>
        <div className="site-links"><Link href="/dashboard/reports">Weekly briefings</Link><Link href="/methodology">Methodology</Link><Link href="/dashboard/sources">Sources</Link><a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API</a></div>
        <Link className="button secondary" href="/dashboard">Open dashboard <ArrowRight size={15} /></Link>
      </nav>

      <section className="hero-band">
        <div className="hero-content">
          <span className="hero-kicker"><ShieldCheck size={14} /> Grounded in O*NET and BLS labor data</span>
          <h1>Know what to learn before you invest the time.</h1>
          <p>SkillSync connects technology job demand, learning supply, wage evidence, certifications, and open-source practice in one decision workspace.</p>
          <div className="hero-actions"><Link className="button primary" href="/dashboard/skills">Explore skills <ArrowRight size={16} /></Link><a className="button ghost" href="https://github.com/Sarthak2661/SkillSync" target="_blank" rel="noreferrer"><Code2 size={16} /> View repository</a></div>
        </div>
        <div className="hero-signal" aria-label="Latest market signal"><TrendingUp size={18} /><span><small>Latest opportunity signal</small><strong>{kpis.top_opportunity_skill || "Not available"}</strong></span><Link href="/dashboard/reports">Read the weekly briefing <ArrowRight size={14} /></Link></div>
      </section>

      <section className="landing-stats" aria-label="Latest dataset metrics">
        <div><strong>{integer(kpis.job_postings)}</strong><span>Jobs tracked</span></div><div><strong>{integer(kpis.unique_skills)}</strong><span>Skills scored</span></div><div><strong>{integer(kpis.course_listings)}</strong><span>Learning resources</span></div><div><strong>{integer(kpis.historical_runs_available)}</strong><span>Historical runs</span></div>
      </section>

      <section className="landing-section">
        <div className="section-intro"><span className="eyebrow">One decision layer</span><h2>From market signal to demonstrable skill</h2><p>The product closes the loop between what employers ask for and what a job seeker can do next.</p></div>
        <div className="feature-grid">
          <article><span className="feature-icon blue"><BriefcaseBusiness size={20} /></span><h3>Measure demand</h3><p>Compare skills across job postings, role targets, locations, salary bands, and historical snapshots.</p></article>
          <article><span className="feature-icon cyan"><BookOpenCheck size={20} /></span><h3>Find the learning gap</h3><p>See where demand outpaces available courses and certification pathways.</p></article>
          <article><span className="feature-icon green"><GitBranch size={20} /></span><h3>Build proof of work</h3><p>Move from a recommended skill to current GitHub issues where that skill can be practiced.</p></article>
          <article><span className="feature-icon amber"><DatabaseZap size={20} /></span><h3>Trust the pipeline</h3><p>Inspect source confidence, quality checks, scheduled runs, and reproducible warehouse outputs.</p></article>
        </div>
      </section>

      <section className="briefing-band"><div><span className="feature-icon amber"><Newspaper size={20} /></span><div><span className="eyebrow">Weekly market notes</span><h2>A dated record of what changed, not another unexplained chart.</h2><p>Each briefing compares the latest retained snapshot in one week with the previous week and keeps the sample limitations visible.</p></div></div><Link className="button secondary" href="/dashboard/reports">Browse briefings <ArrowRight size={15} /></Link></section>

      <section className="landing-cta"><div><span className="eyebrow">Current market snapshot</span><h2>Start with {kpis.top_opportunity_skill || "the strongest signal"}.</h2><p>Then inspect the evidence, target roles, learning supply, and practical work behind the score.</p></div><Link className="button primary" href="/dashboard/skills">Open skill explorer <ArrowRight size={16} /></Link></section>
      <footer><span>SkillSync | Open-source market intelligence for technology careers</span><div><Link href="/methodology">Methodology</Link><a href="https://github.com/Sarthak2661/SkillSync" target="_blank" rel="noreferrer">GitHub</a></div></footer>
    </main>
  );
}
