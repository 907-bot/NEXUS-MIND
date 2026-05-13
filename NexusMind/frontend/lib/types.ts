// ── Agent event types ─────────────────────────────────────────────────────────

export type AgentEventType =
  | "CONNECTED"
  | "BACKEND_LOG"
  | "AGENT_INITIALIZED"
  | "PLANNING_STARTED"
  | "PLANNING_COMPLETE"
  | "TASK_STARTED"
  | "TASK_COMPLETE"
  | "TASK_FAILED"
  | "TOOL_CALLED"
  | "REVIEW_STARTED"
  | "REVIEW_COMPLETE"
  | "REVISION_STARTED"
  | "ASSEMBLY_STARTED"
  | "FINAL_OUTPUT"
  | "PIPELINE_ERROR"
  | "ERROR";

export interface AgentEvent {
  agent: string;
  type: AgentEventType;
  timestamp?: number;
  data: Record<string, any>;
}

// ── Task graph ────────────────────────────────────────────────────────────────

export type TaskStatus = "pending" | "running" | "done" | "failed";

export interface TaskNode {
  task_id: string;
  description: string;
  skill_tag: SkillTag;
  depends_on: string[];
  priority: 1 | 2 | 3;
  status?: TaskStatus;
}

export type SkillTag =
  | "backend"
  | "frontend"
  | "research"
  | "data"
  | "content"
  | "devops"
  | "review";

// ── API responses ─────────────────────────────────────────────────────────────

export interface SubmitGoalResponse {
  session_id: string;
  status: "processing";
  user_id: string;
}

export interface SessionStatusResponse {
  session_id: string;
  status: "initialized" | "planning" | "executing" | "completed" | "failed";
}

export interface FinalOutput {
  final_content: string;
  summary: string;
}

// ── Agent registry ────────────────────────────────────────────────────────────

export interface AgentInfo {
  agent_id: string;
  name: string;
  skill_tags: string[];
  status: "idle" | "busy" | "error";
  max_concurrent_tasks: number;
  avg_completion_time_ms: number;
  success_rate: number;
}

// ── Critic review ─────────────────────────────────────────────────────────────

export interface CriticIssue {
  task_id: string;
  issue: string;
  severity: "high" | "medium" | "low";
}

export interface CriticReview {
  score: number;
  issues: CriticIssue[];
  approved: boolean;
  feedback: string;
}
