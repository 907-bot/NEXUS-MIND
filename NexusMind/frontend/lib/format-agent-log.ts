/**
 * Markdown snippets for the live "Output Deliverable" panel (mirrors backend-style logs).
 */

export function formatPlanningComplete(data: Record<string, unknown>): string {
  const brief = data?.brief as string | undefined;
  const next_agent = data?.next_agent as string | undefined;

  if (brief) {
    return (
      `### Autonomous Swarm Plan Complete\n\n` +
      `**Project Brief:**\n> ${brief}\n\n` +
      `**First Agent:** \`${next_agent || "ResearchAgent"}\`\n\n`
    );
  }

  // Fallback for old task graph
  const tasks = data?.tasks;
  const count =
    typeof data?.task_count === "number"
      ? data.task_count
      : Array.isArray(tasks)
        ? tasks.length
        : 0;

  if (!Array.isArray(tasks) || tasks.length === 0) {
    return `### Planning complete\n\n**${count}** task(s) queued.\n\n`;
  }

  const lines = tasks.map((t: Record<string, unknown>, i: number) => {
    const id = String(t.task_id ?? i + 1);
    const tag = String(t.skill_tag ?? "?");
    const desc = String(t.description ?? "").trim();
    const short =
      desc.length > 140 ? `${desc.slice(0, 140).trim()}…` : desc;
    return `${i + 1}. **[${tag}]** \`${id}\` — ${short}`;
  });

  return (
    `### Planning complete\n\n` +
    `**${count} tasks** generated:\n\n` +
    lines.join("\n") +
    `\n\n`
  );
}

export function formatTaskStarted(agent: string, data: Record<string, unknown>): string {
  const tid = String(data?.task_id ?? "");
  const desc = String(data?.description ?? "").trim();
  const short =
    desc.length > 200 ? `${desc.slice(0, 200).trim()}…` : desc;
  return short
    ? `▶ **${agent}** started **${tid}** — ${short}\n\n`
    : `▶ **${agent}** started **${tid}**.\n\n`;
}

export function formatToolCalled(agent: string, data: Record<string, unknown>): string {
  const tool = String(data?.tool ?? "tool");
  const tid = data?.task_id ? String(data.task_id) : "";
  let extra = "";
  if (data?.query) extra = `query: ${String(data.query).slice(0, 80)}`;
  else if (data?.url) extra = String(data.url).slice(0, 72);
  else if (data?.filename) extra = String(data.filename);
  else if (data?.purpose) extra = String(data.purpose).slice(0, 72);
  const tail = extra ? ` — _${extra}${extra.length >= 72 ? "…" : ""}_` : "";
  const prefix = tid ? `\`${tid}\` · ` : "";
  return `🔧 **${agent}** ${prefix}\`${tool}\`${tail}\n\n`;
}
