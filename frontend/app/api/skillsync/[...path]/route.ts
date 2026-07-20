import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.SKILLSYNC_API_URL ?? "http://127.0.0.1:8000";

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = new URL(`${API_URL}/${path.join("/")}`);
  request.nextUrl.searchParams.forEach((value, key) => target.searchParams.set(key, value));
  try {
    const response = await fetch(target, { cache: "no-store", headers: { Accept: "application/json" } });
    return new NextResponse(response.body, { status: response.status, headers: { "content-type": response.headers.get("content-type") ?? "application/json" } });
  } catch {
    return NextResponse.json({ status: "error", message: "SkillSync API is unavailable." }, { status: 503 });
  }
}
