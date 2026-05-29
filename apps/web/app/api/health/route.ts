import { NextResponse } from "next/server";

// Health probe for the web console container (manual section 18.10).
export function GET() {
  return NextResponse.json({ status: "ok" });
}
