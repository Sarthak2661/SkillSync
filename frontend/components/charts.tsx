"use client";

import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SkillGap, Trend } from "@/lib/types";

const chartColors = { blue: "#c45138", cyan: "#16756c", green: "#3e7658", amber: "#b27a17", ink: "#34443e" };

export function OpportunityChart({ data }: { data: SkillGap[] }) {
  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data.slice(0, 10)} layout="vertical" margin={{ left: 8, right: 20, top: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#d9e0dc" />
          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "#68766f" }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="skill" width={100} tick={{ fontSize: 12, fill: "#34443e" }} axisLine={false} tickLine={false} />
          <Tooltip cursor={{ fill: "#f2f5f2" }} contentStyle={{ borderRadius: 8, border: "1px solid #d9e0dc", boxShadow: "0 12px 30px rgba(29, 48, 41, .12)" }} />
          <Bar dataKey="opportunity_index" name="Opportunity" fill={chartColors.blue} radius={[0, 4, 4, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DemandSupplyChart({ data }: { data: SkillGap[] }) {
  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data.slice(0, 10)} margin={{ left: 0, right: 12, top: 8, bottom: 28 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d9e0dc" />
          <XAxis dataKey="skill" angle={-28} textAnchor="end" height={60} tick={{ fontSize: 11, fill: "#68766f" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#68766f" }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #d9e0dc", boxShadow: "0 12px 30px rgba(29, 48, 41, .12)" }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="job_demand" name="Job demand" fill={chartColors.cyan} radius={[4, 4, 0, 0]} isAnimationActive={false} />
          <Bar dataKey="course_supply" name="Course supply" fill={chartColors.amber} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TrendChart({ data, skills }: { data: Trend[]; skills: string[] }) {
  const grouped = new Map<string, Record<string, string | number>>();
  for (const row of data.filter((item) => skills.includes(item.skill))) {
    const date = row.run_timestamp.slice(0, 10);
    const current = grouped.get(date) ?? { date };
    current[row.skill] = Number(current[row.skill] ?? 0) + row.job_count;
    grouped.set(date, current);
  }
  const chartData = Array.from(grouped.values()).sort((a, b) => String(a.date).localeCompare(String(b.date))).slice(-30);
  const colors = [chartColors.blue, chartColors.cyan, chartColors.green, chartColors.amber, chartColors.ink];
  return (
    <div className="chart-wrap trend-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ left: 0, right: 16, top: 12, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d9e0dc" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#68766f" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#68766f" }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #d9e0dc", boxShadow: "0 12px 30px rgba(29, 48, 41, .12)" }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {skills.map((skill, index) => <Line key={skill} dataKey={skill} stroke={colors[index % colors.length]} strokeWidth={2.2} dot={false} connectNulls isAnimationActive={false} />)}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
