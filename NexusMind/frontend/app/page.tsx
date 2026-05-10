"use client";

import Link from "next/link";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/clerk-react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Zap, GitBranch, Shield, ArrowRight, Cpu, Activity, Globe, Lock, Code2 } from "lucide-react";
import { useState, useEffect } from "react";

const FEATURES = [
  {
    icon: Brain,
    title: "Autonomous Planning",
    desc: "Gemini 1.5 Flash decomposes goals into high-precision atomic task graphs.",
    color: "from-purple-500 to-indigo-500",
  },
  {
    icon: GitBranch,
    title: "Multi-Agent Swarm",
    desc: "Parallel execution across specialized agents — scaling intelligence in real-time.",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: Zap,
    title: "A2A Message Bus",
    desc: "Agents communicate and share context via a high-speed Redis pub/sub backbone.",
    color: "from-cyan-500 to-teal-500",
  },
  {
    icon: Shield,
    title: "Critic Validation",
    desc: "Dedicated review loops ensure output quality, security, and logical consistency.",
    color: "from-indigo-500 to-blue-500",
  },
];

const STATS = [
  { label: "Active Agents", value: "128+", icon: Cpu },
  { label: "Tasks/Sec", value: "2.4k", icon: Activity },
  { label: "Uptime", value: "99.99%", icon: Globe },
  { label: "Security", value: "Military", icon: Lock },
];

export default function LandingPage() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <main className="min-h-screen bg-[#0a0a0c] text-gray-100 flex flex-col selection:bg-cyan-500/30">
      {/* ── Scanline Effect ── */}
      <div className="fixed inset-0 pointer-events-none z-[100] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%),linear-gradient(90deg,rgba(255,0,0,0.02),rgba(0,255,0,0.01),rgba(0,0,255,0.02))] bg-[length:100%_2px,3px_100%] opacity-20" />

      {/* ── Navbar ─────────────────────────────────────────────────────────── */}
      <nav 
        className={`fixed top-0 w-full z-50 transition-all duration-300 border-b ${
          isScrolled 
            ? "py-3 bg-[#0a0a0c]/80 backdrop-blur-xl border-white/5" 
            : "py-6 bg-transparent border-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-3 group cursor-pointer">
            <div className="relative">
              <div className="absolute inset-0 bg-cyan-500 blur-lg opacity-20 group-hover:opacity-40 transition-opacity" />
              <Cpu className="w-8 h-8 text-cyan-400 relative" />
            </div>
            <span className="text-2xl font-black tracking-tighter bg-gradient-to-r from-white via-white to-gray-500 bg-clip-text text-transparent">
              NEXUS<span className="text-cyan-500">MIND</span>
            </span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
            <a href="#features" className="hover:text-cyan-400 transition-colors">Architecture</a>
            <a href="#network" className="hover:text-cyan-400 transition-colors">Network</a>
            <a href="#security" className="hover:text-cyan-400 transition-colors">Security</a>
          </div>

          <div className="flex items-center gap-4">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-5 py-2 text-sm font-bold text-gray-300 hover:text-white transition-all">
                  Sign In
                </button>
              </SignInButton>
              <SignInButton mode="modal">
                <button className="px-6 py-2.5 text-sm font-bold bg-white text-black hover:bg-cyan-400 transition-all rounded-full shadow-[0_0_20px_rgba(255,255,255,0.1)]">
                  Launch App
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <Link
                href="/dashboard"
                className="px-6 py-2.5 text-sm font-bold bg-cyan-500 hover:bg-cyan-400 text-black rounded-full transition-all flex items-center gap-2 shadow-[0_0_30px_rgba(6,182,212,0.3)]"
              >
                Dashboard <ArrowRight className="w-4 h-4" />
              </Link>
              <UserButton afterSignOutUrl="/" />
            </SignedIn>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center pt-20 px-6 overflow-hidden">
        {/* Stunning Background Image */}
        <div className="absolute inset-0 -z-20">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0a0a0c]/50 to-[#0a0a0c]" />
          <img 
            src="/hero-bg.png" 
            alt="NexusMind Hero" 
            className="w-full h-full object-cover opacity-40 scale-105 animate-[pulse_8s_infinite]"
          />
        </div>

        {/* Floating Particles Overlay (Simulated) */}
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_50%,rgba(6,182,212,0.05),transparent_50%)]" />

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center max-w-5xl"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-bold uppercase tracking-[0.2em] mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
            Level 2 Autonomous Intelligence Protocol
          </div>

          <h1 className="text-7xl md:text-9xl font-black tracking-tightest leading-[0.85] mb-8">
            <span className="bg-gradient-to-b from-white to-gray-500 bg-clip-text text-transparent">
              THINK BEYOND
            </span>
            <br />
            <span className="text-cyan-500 text-glow">
              AUTONOMY
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-xl text-gray-400 mb-12 leading-relaxed font-light">
            NexusMind is a self-evolving multi-agent network that plans, builds, 
            and delivers complex software systems with zero human intervention.
          </p>

          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link
              href="/dashboard"
              className="group relative px-10 py-5 bg-cyan-500 text-black font-black text-xl rounded-2xl transition-all overflow-hidden"
            >
              <div className="absolute inset-0 bg-white translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
              <span className="relative z-10 flex items-center gap-3">
                START BUILDING <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
              </span>
            </Link>
            
            <button className="px-10 py-5 border border-white/10 hover:border-cyan-500/50 rounded-2xl font-bold text-xl text-white transition-all backdrop-blur-sm hover:bg-cyan-500/5">
              Documentation
            </button>
          </div>
        </motion.div>

        {/* ── Stats ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-6xl w-full mt-32 px-6">
          {STATS.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
              className="text-center p-6 glass-card rounded-3xl"
            >
              <div className="flex justify-center mb-3">
                <s.icon className="w-5 h-5 text-cyan-500/50" />
              </div>
              <div className="text-3xl font-black text-white mb-1">{s.value}</div>
              <div className="text-xs uppercase tracking-widest text-gray-500 font-bold">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Features ───────────────────────────────────────────────────────── */}
      <section id="features" className="py-32 px-6 border-t border-white/5 relative">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />
        
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-end justify-between mb-20 gap-8">
            <div className="max-w-2xl">
              <h2 className="text-5xl font-black tracking-tighter mb-6">
                ARCHITECTED FOR <br />
                <span className="text-cyan-500">SCALABLE INTELLIGENCE</span>
              </h2>
              <p className="text-gray-400 text-lg">
                Our multi-agent protocol ensures every task is handled by a specialist, 
                validated by a critic, and integrated by an assembler.
              </p>
            </div>
            <div className="flex gap-2">
              <div className="w-12 h-[2px] bg-cyan-500" />
              <div className="w-4 h-[2px] bg-white/10" />
              <div className="w-4 h-[2px] bg-white/10" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                whileHover={{ y: -10 }}
                className="group relative p-8 rounded-3xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-all"
              >
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${f.color} p-[1px] mb-8 group-hover:rotate-6 transition-transform`}>
                  <div className="w-full h-full bg-[#0a0a0c] rounded-2xl flex items-center justify-center">
                    <f.icon className="w-8 h-8 text-white" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold mb-4 text-white tracking-tight">{f.title}</h3>
                <p className="text-gray-400 leading-relaxed mb-8">{f.desc}</p>
                
                <div className="absolute bottom-8 right-8 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Code2 className="w-5 h-5 text-cyan-500" />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Network Visualization (Placeholder for Stitch/Custom Component) ── */}
      <section className="py-32 px-6 bg-gradient-to-b from-transparent to-cyan-500/5">
        <div className="max-w-5xl mx-auto glass-panel p-1 border-white/10 rounded-[40px] overflow-hidden">
          <div className="bg-[#0a0a0c] rounded-[38px] p-20 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(6,182,212,0.1),transparent_70%)]" />
            <h2 className="text-4xl font-black mb-8 relative z-10">THE SWARM IS READY.</h2>
            <p className="text-gray-400 max-w-xl mx-auto mb-12 relative z-10 text-lg">
              Experience the power of a fully coordinated AI workforce. 
              Deploy your first NexusMind session in seconds.
            </p>
            <div className="relative z-10 flex flex-col sm:flex-row gap-4 justify-center">
              <button className="px-10 py-4 bg-white text-black font-black rounded-xl hover:bg-cyan-400 transition-all">
                Launch Genesis Node
              </button>
              <button className="px-10 py-4 border border-white/10 hover:bg-white/5 font-bold rounded-xl transition-all">
                View Network Stats
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer className="py-20 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12 mb-20">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-3 mb-8">
              <Cpu className="w-8 h-8 text-cyan-500" />
              <span className="text-2xl font-black tracking-tighter">NEXUSMIND</span>
            </div>
            <p className="text-gray-500 max-w-sm leading-relaxed">
              Pioneering the future of autonomous multi-agent intelligence. 
              Built with Google Gemini 1.5 Flash and Model Context Protocol.
            </p>
          </div>
          <div>
            <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Platform</h4>
            <ul className="space-y-4 text-gray-500 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Agents</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Protocols</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Integrations</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Resources</h4>
            <ul className="space-y-4 text-gray-500 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
              <li><a href="#" className="hover:text-white transition-colors">API Reference</a></li>
              <li><a href="#" className="hover:text-white transition-colors">GitHub</a></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center pt-8 border-t border-white/5 text-gray-600 text-xs font-medium">
          <div>© 2026 NEXUSMIND TECHNOLOGIES · ALL AGENTS RESERVED.</div>
          <div className="flex gap-8 mt-4 md:mt-0 uppercase tracking-widest">
            <a href="#" className="hover:text-white">Privacy</a>
            <a href="#" className="hover:text-white">Terms</a>
            <a href="#" className="hover:text-white">Security</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
