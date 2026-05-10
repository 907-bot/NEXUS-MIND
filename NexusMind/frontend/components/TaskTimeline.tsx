"use client";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Clock, PlayCircle, AlertCircle } from "lucide-react";

export default function TaskTimeline({ events }: { events: any[] }) {
  const relevantEvents = events.filter(e => 
    ["TASK_STARTED", "TASK_COMPLETE", "TASK_FAILED", "PLANNING_COMPLETE", "REVISION_STARTED", "FINAL_OUTPUT", "ERROR", "PIPELINE_ERROR"].includes(e.type)
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
              {event.type === "TASK_COMPLETE" || event.type === "PLANNING_COMPLETE" || event.type === "FINAL_OUTPUT" ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : event.type === "ERROR" || event.type === "PIPELINE_ERROR" || event.type === "TASK_FAILED" ? (
                <AlertCircle className="w-5 h-5 text-red-500" />
              ) : event.type === "REVISION_STARTED" ? (
                <Clock className="w-5 h-5 text-yellow-500" />
              ) : (
                <PlayCircle className="w-5 h-5 text-blue-500 animate-pulse" />
              )}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-200">
                <span className="text-purple-400 font-bold">[{event.agent}]</span>{" "}
                {event.type.replace(/_/g, " ")}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {event.data?.description || event.data?.summary || event.data?.message || "Processing..."}
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
