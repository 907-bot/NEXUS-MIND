"use client";
import ReactMarkdown from "react-markdown";
import { Copy, Terminal } from "lucide-react";

export default function OutputPanel({ content, thinkingLogs, isProcessing }: { content: string; thinkingLogs?: string; isProcessing: boolean }) {
  const copyToClipboard = () => {
    // Only copy the actual final content + success logs, not the thinking logs
    navigator.clipboard.writeText(content);
  };

  return (
    <div className="relative h-full flex flex-col">
      {(content || thinkingLogs) ? (
        <>
          <div className="absolute top-0 right-0 z-10">
            <button
              onClick={copyToClipboard}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors text-gray-400 hover:text-white"
              title="Copy to clipboard"
            >
              <Copy className="w-5 h-5" />
            </button>
          </div>
          <div className="prose prose-invert max-w-none prose-pre:bg-gray-950 prose-pre:border prose-pre:border-gray-800 prose-headings:text-purple-400 prose-a:text-blue-400">
            {thinkingLogs && (
              <details className="mb-6 bg-gray-900/50 border border-gray-800 rounded-lg open:bg-gray-900 transition-colors">
                <summary className="cursor-pointer p-4 font-semibold text-purple-400 hover:text-purple-300 flex items-center select-none">
                  <span className="mr-2">🧠</span>
                  Agent Thinking Process
                </summary>
                <div className="p-4 pt-0 border-t border-gray-800/50 text-sm text-gray-400 prose-sm prose-invert prose-p:leading-relaxed">
                  <ReactMarkdown>{thinkingLogs}</ReactMarkdown>
                </div>
              </details>
            )}
            {content && <ReactMarkdown>{content}</ReactMarkdown>}
          </div>
        </>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-600">
          {isProcessing ? (
            <div className="space-y-4 text-center">
              <div className="flex justify-center gap-1">
                {[1, 2, 3].map(i => (
                  <div key={i} className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.1}s` }} />
                ))}
              </div>
              <p className="text-sm font-medium">Assembling final deliverable...</p>
            </div>
          ) : (
            <div className="text-center space-y-4 opacity-40">
              <Terminal className="w-16 h-16 mx-auto" />
              <p className="text-lg">Final output will appear here.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
