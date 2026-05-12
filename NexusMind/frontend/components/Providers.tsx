"use client";

import { ClerkProvider } from "@clerk/clerk-react";
import { useRouter } from "next/navigation";

const BASE_PATH = process.env.NODE_ENV === "production" ? "/NEXUS-MIND" : "";

export function Providers({ children }: { children: React.ReactNode }) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey || publishableKey === "pk_test_..." || publishableKey === "pk_live_...") {
    console.warn("Clerk Publishable Key is missing or a placeholder. Authentication will be disabled.");
    return <>{children}</>;
  }

  return (
    <ClerkProvider
      publishableKey={publishableKey}
      signInFallbackRedirectUrl={`${BASE_PATH}/dashboard/`}
      signUpFallbackRedirectUrl={`${BASE_PATH}/dashboard/`}
      afterSignOutUrl={`${BASE_PATH}/`}
    >
      {children}
    </ClerkProvider>
  );
}
