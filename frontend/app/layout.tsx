import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "SkillSync | Job market intelligence", template: "%s | SkillSync" },
  description: "Job demand, learning supply, wage evidence, and practical next steps for technology careers.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
