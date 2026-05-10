"use client";

import { useAuth } from "@clerk/nextjs";
import { useSearchParams, useRouter } from "next/navigation";
import { useState, useCallback, useEffect, Suspense } from "react";
import OutputPanel from "@/components/OutputPanel";
import TaskTimeline from "@/components/TaskTimeline";
import AgentGraph from "@/components/AgentGraph";
import AgentCard from "@/components/AgentCard";
import StreamConsumer from "@/components/StreamConsumer";
import { getSessionStatus, getSessionOutput } from "@/lib/api";
import { AgentEvent } from "@/lib/types";
import { ArrowLeft, Loader2, Cpu } from "lucide-react";
import Link from "next/link";

const KNOWN_AGENTS = [
  "PlannerAgent",
  "BackendAgent",
  "FrontendAgent",
  "ResearchAgent",
  "ContentAgent",
  "DataAgent",
  "DevOpsAgent",
  "CriticAgent",
  "AssemblerAgent",
];

function SessionContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("id");
  const router = useRouter();
  const { getToken, isLoaded } = useAuth();

  const [token, setToken] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [output, setOutput] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(true);
  const [status, setStatus] = useState<string>("loading");

  // Fetch token and initial session status on mount
  useEffect(() => {
    if (!isLoaded || !sessionId) return;
    (async () => {
      const t = await getToken();
      if (!t) { router.push("/"); return; }
      setToken(t);
      try {
        const s = await getSessionStatus(sessionId, t);
        setStatus(s.status);
        if (s.status === "completed" || s.status === "failed") {
          setIsProcessing(false);
          // Fetch final output if already complete
          try {
            const out = await getSessionOutput(sessionId, t);
            setOutput(out.final_content ?? "");
          } catch {}
        }
      } catch {
        setStatus("not found");
        setIsProcessing(false);
      }
    })();
  }, [isLoaded, sessionId, getToken, router]);

  const handleEvent = useCallback((event: AgentEvent) => {
    setEvents((prev) => [...prev, event]);
    if (event.type === "TASK_STARTED" || event.type === "PLANNING_STARTED") {
      setStatus("executing");
    }
  }, []);

  const handleFinalOutput = useCallback((content: string) => {
    setOutput(content);
    setStatus("completed");
  }, []);

  const handleDone = useCallback(() => setIsProcessing(false), []);
  const handleError = useCallback(() => {
    setIsProcessing(false);
    setStatus("error");
  }, []);

  // Determine which agents were active in this session
  const activeAgents = [
    ...new Set(events.map((e) => e.agent).filter((a) => KNOWN_AGENTS.includes(a))),
  ];

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950 text-white">
        <p>No Session ID provided.</p>
      </div>
    );
  }

  if (!isLoaded || !token) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-[1600px] mx-auto space-y-6">
      {/* Header */}
      <header className="flex items-center gap-4 border-b border-gray-800 pb-5">
        <Link
          href="/dashboard"
          className="p-2 rounded-lg border border-gray-800 hover:border-gray-600 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div className="flex items-center gap-3">
          <Cpu className="w-6 h-6 text-purple-500" />
          <div>
            <h1 className="text-xl font-extrabold tracking-tight text-white">
              Session Details
            </h1>
            <p className="text-xs text-gray-500 font-mono mt-0.5">{sessionId}</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold ${
              status === "completed"
                ? "bg-green-500/20 text-green-300"
                : status === "failed" || status === "error"
                ? "bg-red-500/20 text-red-300"
                : status === "executing" || status === "planning"
                ? "bg-purple-500/20 text-purple-300"
                : "bg-gray-800 text-gray-400"
            }`}
          >
            {status}
          </span>
          {isProcessing && <Loader2 className="w-4 h-4 animate-spin text-purple-500" />}
        </div>
      </header>

      {/* SSE Consumer */}
      {isProcessing && token && (
        <StreamConsumer
          sessionId={sessionId}
          token={token}
          onEvent={handleEvent}
          onFinalOutput={handleFinalOutput}
          onDone={handleDone}
          onError={handleError}
        />
      )}

      {/* Agent Cards */}
      {activeAgents.length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">
            Active Agents
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {activeAgents.map((name) => (
              <AgentCard key={name} agentName={name} events={events} />
            ))}
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-4 space-y-5">
          <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-5">
            <h2 className="text-sm font-bold mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
              Agent Network
            </h2>
            <AgentGraph events={events} />
          </div>

          <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-5">
            <h2 className="text-sm font-bold mb-4">Task Timeline</h2>
            <TaskTimeline events={events} />
          </div>
        </div>

        <div className="xl:col-span-8 bg-gray-900/50 border border-gray-800 rounded-2xl p-6 min-h-[500px]">
          <h2 className="text-sm font-bold mb-5 flex justify-between items-center">
            Output Deliverable
            {isProcessing && <Loader2 className="w-4 h-4 animate-spin text-purple-500" />}
          </h2>
          <OutputPanel content={output} isProcessing={isProcessing} />
        </div>
      </div>
    </div>
  );
}

export default function SessionPage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center bg-gray-950"><Loader2 className="w-8 h-8 animate-spin text-purple-500" /></div>}>
      <SessionContent />
    </Suspense>
  );
}
