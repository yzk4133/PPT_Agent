import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { PanelTopClose, PanelTopOpen } from "lucide-react";

interface DetailPanelProps {
  visible: boolean;
  expanded: boolean;
  logs: { data: any; metadata: any }[];
  onExpand: () => void;
  onCollapse: () => void;
  isGeneratingPresentation: boolean; 
}

export const DetailPanel: React.FC<DetailPanelProps> = ({
  visible,
  expanded,
  logs,
  onExpand,
  onCollapse,
  isGeneratingPresentation,
}) => {
  const [openIndexes, setOpenIndexes] = useState<number[]>([]);

  const toggleAccordion = (idx: number) => {
    setOpenIndexes((prev) =>
      prev.includes(idx)
        ? prev.filter((i) => i !== idx)
        : [...prev, idx]
    );
  };

  if (!visible) return null;
  return (
    <div
      className={`fixed right-4 bottom-4 z-50 transition-all duration-300 ${
        expanded ? "inset-0 bg-black/60 flex items-center justify-center" : "w-72 h-14 bg-white shadow-lg rounded-lg flex items-center px-4"
      }`}
      style={expanded ? {} : { borderRadius: 8 }}
    >
      {expanded ? (
        <div className="bg-white w-[80vw] h-[80vh] rounded-lg p-6 overflow-auto relative shadow-xl">
          <button
            onClick={onCollapse}
            className="absolute top-2 right-4 p-2 bg-gray-200 rounded hover:bg-gray-300 flex items-center justify-center"
            aria-label="缩小"
          >
            <PanelTopClose className="w-5 h-5" />
          </button>
          <h2 className="text-lg font-bold mb-4">
            进度细节
            <span
              className={`ml-3 text-base font-normal ${isGeneratingPresentation ? 'animate-blink text-blue-500' : 'text-gray-500'}`}
            >
              {isGeneratingPresentation ? '（生成中…）' : '（生成完成）'}
            </span>
          </h2>
          <div className="mt-2 space-y-2 text-sm max-h-[70vh] overflow-y-auto">
            {logs.length === 0 ? (
              <div className="text-gray-400">暂无细节</div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="border-b pb-2 mb-2">
                  <button
                    className="w-full text-left font-semibold text-blue-700 focus:outline-none flex items-center justify-between"
                    onClick={() => toggleAccordion(i)}
                  >
                    <span
                      className={openIndexes.includes(i) ? "text-blue-600" : "text-red-600"}
                    >
                      {JSON.stringify(log.metadata)}
                    </span>
                    <span className="ml-2">{openIndexes.includes(i) ? '▲' : '▼'}</span>
                  </button>
                  {openIndexes.includes(i) && (
                    <div className="mt-2 text-gray-700 whitespace-pre-wrap bg-gray-50 rounded p-2">
                      {typeof log.data === 'string' ? (
                        <ReactMarkdown>{log.data}</ReactMarkdown>
                      ) : (
                        JSON.stringify(log.data, null, 2)
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      ) : (
        <>
          <span className="flex-1 text-gray-700">生成细节</span>
          <span className="text-red-300">{isGeneratingPresentation ? '（生成中…）' : '（生成完成）'}</span>
          <button
            onClick={onExpand}
            className="ml-2 p-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center justify-center"
            aria-label="放大"
          >
            <PanelTopOpen className="w-5 h-5" />
          </button>
        </>
      )}
    </div>
  );
}; 

// 动画样式
<style jsx global>{`
@keyframes blink {
  0%, 100% { opacity: 1; color: #3b82f6; }
  50% { opacity: 0.3; color: #f59e42; }
}
.animate-blink {
  animation: blink 1s infinite;
}
`}</style> 