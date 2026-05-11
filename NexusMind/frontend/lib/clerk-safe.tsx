"use client";

import React from "react";
import * as Clerk from "@clerk/clerk-react";

const isClerkEnabled = 
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && 
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY !== "pk_test_..." && 
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY !== "pk_live_...";

export const SignedIn = ({ children }: { children: React.ReactNode }) => {
  if (!isClerkEnabled) return null;
  return <Clerk.SignedIn>{children}</Clerk.SignedIn>;
};

export const SignedOut = ({ children }: { children: React.ReactNode }) => {
  if (!isClerkEnabled) return <>{children}</>;
  return <Clerk.SignedOut>{children}</Clerk.SignedOut>;
};

export const SignInButton = ({ children, mode }: { children: React.ReactNode; mode?: "modal" | "redirect" }) => {
  if (!isClerkEnabled) {
    return (
      <div onClick={() => alert("Clerk is not configured. Please set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY in .env.local")}>
        {children}
      </div>
    );
  }
  return <Clerk.SignInButton mode={mode}>{children}</Clerk.SignInButton>;
};

export const SignUpButton = ({ children, mode }: { children: React.ReactNode; mode?: "modal" | "redirect" }) => {
  if (!isClerkEnabled) {
    return (
      <div onClick={() => alert("Clerk is not configured. Please set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY in .env.local")}>
        {children}
      </div>
    );
  }
  return <Clerk.SignUpButton mode={mode}>{children}</Clerk.SignUpButton>;
};

export const UserButton = (props: any) => {
  if (!isClerkEnabled) return <div className="w-8 h-8 rounded-full bg-gray-800 animate-pulse" />;
  return <Clerk.UserButton {...props} />;
};

export const useAuth = () => {
  if (!isClerkEnabled) {
    return { isLoaded: true, userId: "dev_user", isSignedIn: true, getToken: async () => "mock_token" };
  }
  return Clerk.useAuth();
};

export { isClerkEnabled };
