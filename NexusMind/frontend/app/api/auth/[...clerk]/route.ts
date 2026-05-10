import { clerkClient } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

/**
 * Clerk auth catch-all route handler.
 * Required in dev (Next.js server mode). Unused in static GitHub Pages export.
 * Reference: https://clerk.com/docs/references/nextjs/auth-route
 */
export async function GET() {
  return NextResponse.json({ status: "clerk-auth-route-active" });
}
