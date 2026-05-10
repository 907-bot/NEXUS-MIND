"use client";
import { motion } from "framer-motion";
import { Cpu, Database, Layout, Search, PenTool, Settings, ShieldCheck, BarChart2 } from "lucide-react";

function Sparkles(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      <path d="M5 3v4" /><path d="M19 17v4" /><path d="M3 5h4" /><path d="M17 19h4" />
    </svg>
  );
}

const AGENT_ICONS: Record<string, any> = {
  PlannerAgent: Cpu,
  BackendAgent: Database,
  FrontendAgent: Layout,
  ResearchAgent: Search,
  ContentAgent: PenTool,
  DataAgent: BarChart2,
  DevOpsAgent: Settings,
  CriticAgent: ShieldCheck,
  AssemblerAgent: Sparkles,
};

const AGENTS = [
  "PlannerAgent",
  "BackendAgent",
  "FrontendAgent",
  "ResearchAgent",
  "ContentAgent",
  "DataAgent",
  "DevOpsAgent",
  "CriticAgent",
];

export default function AgentGraph({ events }: { events: any[] }) {
  // Track active task count per agent to handle agents running multiple tasks
  const agentTaskCounts: Record<string, { started: number; completed: number; failed: number }> = {};
  for (const e of events) {
    const name = e.agent as string;
    if (!agentTaskCounts[name]) agentTaskCounts[name] = { started: 0, completed: 0, failed: 0 };
    if (e.type === "TASK_STARTED") agentTaskCounts[name].started++;
    if (e.type === "TASK_COMPLETE") agentTaskCounts[name].completed++;
    if (e.type === "TASK_FAILED") agentTaskCounts[name].failed++;
  }

  return (
    <div className="grid grid-cols-4 gap-3">
      {AGENTS.map((name) => {
        const Icon = AGENT_ICONS[name] || Cpu;
        const counts = agentTaskCounts[name];
        const hasStarted = counts && counts.started > 0;
        const allDone = hasStarted && (counts.completed + counts.failed) >= counts.started;
        const isActive = hasStarted && !allDone;
        const isDone = allDone && counts.failed === 0;
        const hasFailed = allDone && counts.failed > 0;

        return (
          <motion.div
            key={name}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all duration-500 ${
              isActive
                ? "bg-purple-500/20 border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.4)]"
                : isDone
                ? "bg-green-500/10 border-green-500/50"
                : hasFailed
                ? "bg-red-500/10 border-red-500/50"
                : "bg-gray-800/50 border-gray-800"
            }`}
          >
            <div
              className={`p-2 rounded-lg mb-2 ${
                isActive
                  ? "text-purple-400"
                  : isDone
                  ? "text-green-400"
                  : hasFailed
                  ? "text-red-400"
                  : "text-gray-600"
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? "animate-pulse" : ""}`} />
            </div>
            <span
              className={`text-[9px] font-bold text-center leading-tight ${
                isActive ? "text-white" : isDone ? "text-green-300" : "text-gray-500"
              }`}
            >
              {name.replace("Agent", "")}
            </span>
            {hasStarted && (
              <span className="text-[8px] text-gray-500 mt-0.5">
                {counts.completed}/{counts.started}
              </span>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
