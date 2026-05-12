"use client";

import { ClerkProvider } from "@clerk/clerk-react";
import { useRouter } from "next/navigation";

const BASE_PATH = process.env.NODE_ENV === "production" ? "/NEXUS-MIND" : "";

export function Providers({ children }: { children: React.ReactNode }) {
  // Emergency Auth Bypass — Clerk is disabled to isolate production errors
  return <>{children}</>;
}
