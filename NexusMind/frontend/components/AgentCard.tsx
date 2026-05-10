"use client";

import { motion } from "framer-motion";
import { CheckCircle, XCircle, Loader2, Clock } from "lucide-react";
import { AgentEvent } from "@/lib/types";

interface AgentCardProps {
  agentName: string;
  events: AgentEvent[];
}

/**
 * Displays the current status and recent activity for a single agent.
 * Used in the dashboard to surface per-agent progress during execution.
 */
export default function AgentCard({ agentName, events }: AgentCardProps) {
  const agentEvents = events.filter((e) => e.agent === agentName);
  const lastEvent = agentEvents[agentEvents.length - 1];

  const startedCount = agentEvents.filter((e) => e.type === "TASK_STARTED").length;
  const completedCount = agentEvents.filter((e) => e.type === "TASK_COMPLETE").length;
  const failedCount = agentEvents.filter((e) => e.type === "TASK_FAILED").length;

  const isIdle = startedCount === 0;
  const isActive = startedCount > completedCount + failedCount;
  const isDone = !isIdle && completedCount + failedCount >= startedCount && failedCount === 0;
  const hasFailed = failedCount > 0;

  const statusColor = isActive
    ? "border-purple-500 bg-purple-500/10"
    : isDone
    ? "border-green-500/50 bg-green-500/10"
    : hasFailed
    ? "border-red-500/50 bg-red-500/10"
    : "border-gray-800 bg-gray-900/50";

  const StatusIcon = isActive
    ? Loader2
    : isDone
    ? CheckCircle
    : hasFailed
    ? XCircle
    : Clock;

  const iconClass = isActive
    ? "text-purple-400 animate-spin"
    : isDone
    ? "text-green-400"
    : hasFailed
    ? "text-red-400"
    : "text-gray-600";

  const label = isActive
    ? "Working"
    : isDone
    ? "Done"
    : hasFailed
    ? "Failed"
    : "Idle";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl border p-4 transition-all duration-300 ${statusColor}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-bold text-white truncate">
          {agentName.replace("Agent", " Agent")}
        </span>
        <StatusIcon className={`w-4 h-4 flex-shrink-0 ${iconClass}`} />
      </div>

      <div className="flex gap-3 text-xs text-gray-400 mb-3">
        <span>{startedCount} started</span>
        <span className="text-green-400">{completedCount} done</span>
        {failedCount > 0 && <span className="text-red-400">{failedCount} failed</span>}
      </div>

      <div
        className={`text-xs font-semibold px-2 py-0.5 rounded-full inline-block ${
          isActive
            ? "bg-purple-500/20 text-purple-300"
            : isDone
            ? "bg-green-500/20 text-green-300"
            : hasFailed
            ? "bg-red-500/20 text-red-300"
            : "bg-gray-800 text-gray-500"
        }`}
      >
        {label}
      </div>

      {lastEvent && (
        <p className="mt-2 text-[10px] text-gray-500 truncate">
          Last: {lastEvent.type}
        </p>
      )}
    </motion.div>
  );
}
