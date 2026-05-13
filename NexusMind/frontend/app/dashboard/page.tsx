"use client";

import { useAuth } from "@/lib/clerk-safe";
import { useState, useCallback } from "react";
import GoalInput from "@/components/GoalInput";
import TaskTimeline from "@/components/TaskTimeline";
import OutputPanel from "@/components/OutputPanel";
import AgentGraph from "@/components/AgentGraph";
import StreamConsumer from "@/components/StreamConsumer";
import AuthButtons from "@/components/AuthButtons";
import { submitGoal } from "@/lib/api";
import { AgentEvent } from "@/lib/types";
import { Loader2, Cpu } from "lucide-react";

export default function Dashboard() {
  const { getToken, isLoaded } = useAuth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamToken, setStreamToken] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [output, setOutput] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (goal: string) => {
    setIsProcessing(true);
    setEvents([]);
    setOutput("🚀 **NexusMind Pipeline Initialized**\nConnecting to autonomous agents via secure stream...\n\n");
    setError(null);
    setSessionId(null);
    setStreamToken(null);

    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const { session_id } = await submitGoal(goal, token);
      // Store token separately so StreamConsumer can use it for ?token= param
      setSessionId(session_id);
      setStreamToken(token);
    } catch (err: any) {
      setError(err.message ?? "Failed to submit goal");
      setIsProcessing(false);
    }
  };

  // StreamConsumer callbacks (stable refs via useCallback)
  const handleEvent = useCallback((event: AgentEvent) => {
    setEvents((prev) => [...prev, event]);

    // Live backend / model lines in the output panel (markdown)
    if (event.type === "BACKEND_LOG" || event.type === "AGENT_INITIALIZED") {
      const msg = event.data?.message ? `${event.data.message}\n\n` : "";
      if (msg) {
        setOutput((prev) => prev + msg);
      }
      return;
    }

    if (event.type === "PLANNING_STARTED" && event.data?.goal) {
      setOutput((prev) =>
        prev + `**Planning started** — _${String(event.data.goal)}_\n\n`
      );
    }
  }, []);

  const handleFinalOutput = useCallback((content: string) => {
    setOutput((prev) => {
      // If we have initialization logs, add a separator
      const prefix = prev ? "---\n\n" : "";
      return prev + prefix + "## 🏁 Final Deliverable\n\n" + content;
    });
  }, []);

  const handleDone = useCallback(() => {
    setIsProcessing(false);
  }, []);

  const handleError = useCallback((message?: string) => {
    setIsProcessing(false);
    setError(message ?? "An unexpected error occurred. Please try again.");
  }, []);

  if (!isLoaded) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-[1600px] mx-auto space-y-8">
      {/* Header */}
      <header className="flex justify-between items-center border-b border-gray-800 pb-6">
        <div className="flex items-center gap-3">
          <Cpu className="w-7 h-7 text-purple-500" />
          <div>
            <h1 className="text-3xl font-extrabold tracking-tighter bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">
              NexusMind
            </h1>
            <p className="text-gray-400 text-xs mt-0.5">Autonomous Multi-Agent Intelligence Network</p>
          </div>
        </div>
        <AuthButtons compact />
      </header>

      {/* Goal Input */}
      <div className="max-w-4xl mx-auto">
        <GoalInput onSubmit={handleSubmit} disabled={isProcessing} />
        {error && (
          <p className="mt-3 text-sm text-red-400 text-center">{error}</p>
        )}
      </div>

      {/* SSE StreamConsumer — headless, manages the EventSource lifecycle */}
      {sessionId && streamToken && (
        <StreamConsumer
          sessionId={sessionId}
          token={streamToken}
          onEvent={handleEvent}
          onFinalOutput={handleFinalOutput}
          onDone={handleDone}
          onError={handleError}
        />
      )}

      {/* Main Dashboard Grid */}
      {sessionId && (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          {/* Left panel: Agent Activity + Timeline */}
          <div className="xl:col-span-4 space-y-6">
            <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 backdrop-blur-sm">
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
                Agent Activity
              </h2>
              <AgentGraph events={events} />
            </div>

            <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 backdrop-blur-sm">
              <h2 className="text-lg font-bold mb-4">Task Timeline</h2>
              <TaskTimeline events={events} />
            </div>
          </div>

          {/* Right panel: Output */}
          <div className="xl:col-span-8 bg-gray-900/50 border border-gray-800 rounded-2xl p-8 backdrop-blur-sm min-h-[600px]">
            <h2 className="text-lg font-bold mb-6 flex justify-between items-center">
              Output Deliverable
              {isProcessing && (
                <Loader2 className="w-5 h-5 animate-spin text-purple-500" />
              )}
            </h2>
            <OutputPanel content={output} isProcessing={isProcessing} />
          </div>
        </div>
      )}
    </div>
  );
}
