"use client";
import { useState } from "react";
import { Send, Sparkles } from "lucide-react";

export default function GoalInput({ onSubmit, disabled }: { onSubmit: (goal: string) => void; disabled?: boolean }) {
  const [goal, setGoal] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (goal.trim() && !disabled) {
      onSubmit(goal);
      setGoal("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative group">
      <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
      <div className="relative flex items-center bg-gray-900 border border-gray-800 rounded-2xl p-2 pl-6">
        <Sparkles className="text-purple-500 mr-4 w-5 h-5" />
        <input
          type="text"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="What should the NexusMind agents build today?"
          className="bg-transparent border-none focus:ring-0 w-full text-lg py-4 placeholder-gray-500"
          disabled={disabled}
        />
        <button
          type="submit"
          disabled={!goal.trim() || disabled}
          className="ml-4 px-8 py-4 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-bold flex items-center gap-2 transition-all"
        >
          {disabled ? "Thinking..." : "Initialize"}
          <Send className="w-4 h-4" />
        </button>
      </div>
    </form>
  );
}
