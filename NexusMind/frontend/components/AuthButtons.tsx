"use client";

import {
  SignInButton,
  SignUpButton,
  UserButton,
  useAuth,
} from "@clerk/nextjs";
import { LogIn, UserPlus } from "lucide-react";

interface AuthButtonsProps {
  /** Show compact icon-only variant (useful in tight navbars) */
  compact?: boolean;
}

export default function AuthButtons({ compact = false }: AuthButtonsProps) {
  const { isSignedIn } = useAuth();

  if (isSignedIn) {
    return (
      <UserButton
        afterSignOutUrl="/"
        appearance={{
          elements: {
            avatarBox: "w-9 h-9",
          },
        }}
      />
    );
  }

  return (
    <div className="flex items-center gap-3">
      <SignInButton mode="modal">
        <button
          className={`flex items-center gap-2 font-semibold border border-gray-700 rounded-lg transition-all hover:border-purple-500 hover:text-purple-400 ${
            compact ? "px-3 py-2 text-sm" : "px-5 py-2.5"
          }`}
        >
          <LogIn className="w-4 h-4" />
          {!compact && "Sign In"}
        </button>
      </SignInButton>

      <SignUpButton mode="modal">
        <button
          className={`flex items-center gap-2 font-bold bg-purple-600 hover:bg-purple-700 rounded-lg transition-all ${
            compact ? "px-3 py-2 text-sm" : "px-5 py-2.5"
          }`}
        >
          <UserPlus className="w-4 h-4" />
          {!compact && "Sign Up"}
        </button>
      </SignUpButton>
    </div>
  );
}
