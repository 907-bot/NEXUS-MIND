"use client";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Clock, PlayCircle, AlertCircle, Wrench } from "lucide-react";

function timelineSubtitle(event: { type: string; data?: Record<string, unknown> }): string {
  const d = event.data ?? {};
  if (event.type === "PLANNING_COMPLETE") {
    const n = typeof d.task_count === "number" ? d.task_count : Array.isArray(d.tasks) ? d.tasks.length : 0;
    const tasks = d.tasks as { task_id?: string }[] | undefined;
    if (Array.isArray(tasks) && tasks.length) {
      const ids = tasks.slice(0, 4).map((t) => t.task_id).filter(Boolean).join(", ");
      const more = tasks.length > 4 ? ` +${tasks.length - 4} more` : "";
      return `${n} tasks planned: ${ids}${more}`;
    }
    return `${n} tasks planned`;
  }
  if (event.type === "TOOL_CALLED") {
    const tool = String(d.tool ?? "");
    const q = d.query ? String(d.query).slice(0, 60) : d.filename ? String(d.filename) : "";
    return q ? `${tool}: ${q}${String(q).length >= 60 ? "…" : ""}` : tool || "Tool call";
  }
  if (event.type === "BACKEND_LOG") {
    if (d.phase === "eta_update") {
      const eta = d.eta_minutes != null ? `~${d.eta_minutes} min` : "";
      const rem = d.tasks_remaining != null ? `${d.tasks_remaining} left` : "";
      return [eta, rem].filter(Boolean).join(" · ") || String(d.message ?? "ETA update");
    }
    const m = String(d.message ?? "");
    return m.length > 220 ? `${m.slice(0, 220)}…` : m || "Log";
  }
  return (
    String(d.description ?? d.summary ?? d.message ?? d.goal ?? "") || "Processing…"
  );
}

export default function TaskTimeline({ events }: { events: any[] }) {
  const relevantEvents = events.filter(e =>
    [
      "PLANNING_STARTED",
      "BACKEND_LOG",
      "AGENT_INITIALIZED",
      "TASK_STARTED",
      "TASK_COMPLETE",
      "TASK_FAILED",
      "PLANNING_COMPLETE",
      "TOOL_CALLED",
      "REVIEW_STARTED",
      "REVIEW_COMPLETE",
      "ASSEMBLY_STARTED",
      "REVISION_STARTED",
      "FINAL_OUTPUT",
      "ERROR",
      "PIPELINE_ERROR",
    ].includes(e.type)
  );

  return (
    <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
      <AnimatePresence initial={false}>
        {relevantEvents.map((event, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex gap-3 items-start"
          >
            <div className="mt-1">
              {event.type === "TASK_COMPLETE" || event.type === "PLANNING_COMPLETE" || event.type === "FINAL_OUTPUT" || event.type === "REVIEW_COMPLETE" ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : event.type === "ERROR" || event.type === "PIPELINE_ERROR" || event.type === "TASK_FAILED" ? (
                <AlertCircle className="w-5 h-5 text-red-500" />
              ) : event.type === "REVISION_STARTED" || event.type === "PLANNING_STARTED" || event.type === "BACKEND_LOG" ? (
                <Clock className="w-5 h-5 text-yellow-500" />
              ) : event.type === "TOOL_CALLED" ? (
                <Wrench className="w-5 h-5 text-cyan-500/90" />
              ) : (
                <PlayCircle className="w-5 h-5 text-blue-500 animate-pulse" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200">
                <span className="text-purple-400 font-bold">[{event.agent}]</span>{" "}
                {event.type.replace(/_/g, " ")}
              </p>
              <p className="text-xs text-gray-500 mt-0.5 break-words">
                {timelineSubtitle(event)}
              </p>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
      {relevantEvents.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-gray-600 italic">
          <Clock className="w-8 h-8 mb-2 opacity-20" />
          <p className="text-sm">Waiting for agent activity...</p>
        </div>
      )}
    </div>
  );
}
