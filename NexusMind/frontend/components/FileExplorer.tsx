"use client";

import React, { useMemo } from "react";
import { Download, File as FileIcon, Folder, Code2, ChevronRight, ChevronDown } from "lucide-react";

export interface GeneratedFile {
  filename: string;
  content: string;
}

export default function FileExplorer({ files }: { files: GeneratedFile[] }) {
  const downloadFile = (filename: string, content: string) => {
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename.split("/").pop() || filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAll = () => {
    // Basic multi-download (browsers may block this if more than a few)
    files.forEach((f, i) => {
      setTimeout(() => downloadFile(f.filename, f.content), i * 300);
    });
  };

  if (!files || files.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-600 min-h-[200px]">
        <Code2 className="w-10 h-10 mb-3 opacity-40" />
        <p className="text-sm">No files generated yet.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex justify-between items-center pb-2 border-b border-gray-800">
        <span className="text-sm text-gray-400">{files.length} file{files.length !== 1 ? 's' : ''} generated</span>
        <button
          onClick={downloadAll}
          className="text-xs bg-purple-600 hover:bg-purple-500 text-white px-3 py-1.5 rounded-md flex items-center gap-1 transition-colors"
        >
          <Download className="w-3 h-3" />
          Download All
        </button>
      </div>
      
      <div className="overflow-y-auto max-h-[500px] pr-2 space-y-2 text-sm text-gray-300">
        {files.map((file, idx) => {
          const parts = file.filename.split("/");
          const name = parts.pop();
          const dir = parts.length > 0 ? parts.join("/") : "/";

          return (
            <div key={idx} className="group flex items-start justify-between p-2 hover:bg-gray-800/50 rounded-lg transition-colors border border-transparent hover:border-gray-700">
              <div className="flex flex-col gap-1 overflow-hidden">
                <div className="flex items-center gap-2 text-gray-400 text-xs">
                  <Folder className="w-3 h-3 text-blue-400" />
                  <span className="truncate">{dir}</span>
                </div>
                <div className="flex items-center gap-2 pl-2">
                  <FileIcon className="w-4 h-4 text-purple-400" />
                  <span className="truncate font-medium text-gray-200">{name}</span>
                </div>
              </div>
              <button
                onClick={() => downloadFile(file.filename, file.content)}
                className="opacity-0 group-hover:opacity-100 p-2 hover:bg-gray-700 rounded-md transition-all text-gray-400 hover:text-white"
                title="Download file"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
