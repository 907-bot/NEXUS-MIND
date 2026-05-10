"use client";

import Link from "next/link";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import { motion } from "framer-motion";
import { Brain, Zap, GitBranch, Shield, ArrowRight, Cpu } from "lucide-react";

const FEATURES = [
  {
    icon: Brain,
    title: "Goal Decomposition",
    desc: "Break any objective into a precise atomic task graph powered by Gemini 1.5 Flash.",
  },
  {
    icon: GitBranch,
    title: "Parallel Execution",
    desc: "Independent tasks run concurrently across specialised agents — no bottlenecks.",
  },
  {
    icon: Zap,
    title: "A2A Communication",
    desc: "Agents share context via a Redis pub/sub message bus in real time.",
  },
  {
    icon: Shield,
    title: "Self-Review",
    desc: "A dedicated Critic Agent validates every output before final assembly.",
  },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* ── Navbar ─────────────────────────────────────────────────────────── */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-gray-800/60 backdrop-blur-sm sticky top-0 z-50 bg-gray-950/80">
        <div className="flex items-center gap-3">
          <Cpu className="w-7 h-7 text-purple-500" />
          <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">
            NexusMind
          </span>
        </div>

        <div className="flex items-center gap-4">
          <SignedOut>
            <SignInButton mode="modal">
              <button className="px-4 py-2 text-sm font-semibold border border-gray-700 rounded-lg hover:border-purple-500 hover:text-purple-400 transition-all">
                Sign In
              </button>
            </SignInButton>
            <SignInButton mode="modal">
              <button className="px-4 py-2 text-sm font-bold bg-purple-600 hover:bg-purple-700 rounded-lg transition-all">
                Get Started
              </button>
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <Link
              href="/dashboard"
              className="px-4 py-2 text-sm font-bold bg-purple-600 hover:bg-purple-700 rounded-lg transition-all flex items-center gap-2"
            >
              Dashboard <ArrowRight className="w-4 h-4" />
            </Link>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────────────────── */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 py-24 relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-purple-900/20 blur-3xl" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <span className="inline-block mb-6 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-purple-400 border border-purple-500/30 rounded-full bg-purple-500/10">
            Level 2 Autonomous Multi-Agent System
          </span>

          <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-6 leading-none">
            <span className="bg-gradient-to-br from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
              One Goal.
            </span>
            <br />
            <span className="bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">
              Infinite Agents.
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-lg text-gray-400 mb-10 leading-relaxed">
            Describe what you want to build. NexusMind autonomously plans,
            assigns specialised AI agents, runs them in parallel, self-reviews the
            outputs, and delivers a production-ready deliverable.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-8 py-4 bg-purple-600 hover:bg-purple-500 rounded-xl font-bold text-lg flex items-center gap-3 transition-all shadow-[0_0_40px_rgba(147,51,234,0.3)] hover:shadow-[0_0_60px_rgba(147,51,234,0.5)]">
                  Start Building Free <ArrowRight className="w-5 h-5" />
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <Link
                href="/dashboard"
                className="px-8 py-4 bg-purple-600 hover:bg-purple-500 rounded-xl font-bold text-lg flex items-center gap-3 transition-all shadow-[0_0_40px_rgba(147,51,234,0.3)]"
              >
                Open Dashboard <ArrowRight className="w-5 h-5" />
              </Link>
            </SignedIn>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 border border-gray-700 hover:border-gray-500 rounded-xl font-bold text-lg text-gray-300 transition-all"
            >
              View on GitHub
            </a>
          </div>
        </motion.div>
      </section>

      {/* ── Features ───────────────────────────────────────────────────────── */}
      <section className="py-24 px-6 border-t border-gray-800/60">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-black text-center mb-16 tracking-tight">
            Built for{" "}
            <span className="bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">
              autonomous intelligence
            </span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="p-6 rounded-2xl border border-gray-800 bg-gray-900/40 hover:border-purple-800 hover:bg-purple-900/10 transition-all group"
              >
                <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center mb-4 group-hover:bg-purple-500/20 transition-all">
                  <f.icon className="w-6 h-6 text-purple-400" />
                </div>
                <h3 className="font-bold mb-2 text-white">{f.title}</h3>
                <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer className="py-8 border-t border-gray-800/60 text-center text-sm text-gray-500">
        NexusMind — Autonomous Multi-Agent Intelligence · Powered by Gemini 1.5 Flash
      </footer>
    </main>
  );
}
