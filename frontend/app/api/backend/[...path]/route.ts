import { NextRequest, NextResponse } from "next/server";

const BACKEND = "http://127.0.0.1:8000";

async function handler(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const joined   = path.join("/");
  const url      = new URL(req.url);
  const backendUrl = `${BACKEND}/${joined}${url.search}`;

  const contentType = req.headers.get("content-type") ?? "";
  const isFormData  = contentType.includes("multipart/form-data");

  let body: BodyInit | undefined;
  const forwardHeaders: Record<string, string> = {};

  if (req.method !== "GET" && req.method !== "HEAD") {
    if (isFormData) {
      // ✅ Parse FormData and re-stream it — preserves boundary correctly
      const formData = await req.formData();
      body = formData;
      // DO NOT set content-type manually — fetch sets it with correct boundary
    } else {
      body = await req.text();
      forwardHeaders["content-type"] = contentType || "application/json";
    }
  }

  const backendRes = await fetch(backendUrl, {
    method:  req.method,
    headers: forwardHeaders,
    body,
  });

  const resBody = await backendRes.blob();

  return new NextResponse(resBody, {
    status: backendRes.status,
    headers: {
      "content-type": backendRes.headers.get("content-type") ?? "application/json",
    },
  });
}

export const GET    = handler;
export const POST   = handler;
export const DELETE = handler;
export const PUT    = handler;
export const PATCH  = handler;
