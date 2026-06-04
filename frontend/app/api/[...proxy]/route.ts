import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.API_URL!;

async function forward(req: NextRequest, segments: string[]): Promise<NextResponse> {
  const path = segments.join("/");
  const url = `${BACKEND}/${path}${req.nextUrl.search}`;
  const init: RequestInit = { method: req.method };
  if (req.method !== "GET") {
    init.body = await req.text();
    init.headers = { "Content-Type": "application/json" };
  }
  const res = await fetch(url, init);
  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("Content-Type") ?? "application/json" },
  });
}

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  const { proxy } = await params;
  return forward(req, proxy);
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ proxy: string[] }> }
) {
  const { proxy } = await params;
  return forward(req, proxy);
}
