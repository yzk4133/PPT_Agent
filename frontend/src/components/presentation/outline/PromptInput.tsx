import { usePresentationState } from "@/states/presentation-state";
import { RefreshCw } from "lucide-react";
import { toast } from "sonner";

export function PromptInput() {
  const {
    presentationInput,
    setPresentationInput,
    startOutlineGeneration,
    isGeneratingOutline,
    outlineError,
  } = usePresentationState();

  const handleGenerateOutline = () => {
    if (!presentationInput.trim()) {
      toast.error("Please enter a presentation topic");
      return;
    }

    startOutlineGeneration();
  };

  return (
    <div className="space-y-3">
      <div className="relative">
        <input
          type="text"
          value={presentationInput}
          onChange={(e) => setPresentationInput(e.target.value)}
          className="w-full rounded-md bg-muted px-4 py-3 pr-12 text-foreground outline-none focus:ring-2 focus:ring-indigo-400"
          placeholder="Enter your presentation topic..."
          disabled={isGeneratingOutline}
        />
        <button
          className={`absolute right-3 top-1/2 -translate-y-1/2 ${
            isGeneratingOutline
              ? "text-indigo-400"
              : "text-indigo-400 hover:text-indigo-500"
          }`}
          onClick={handleGenerateOutline}
          disabled={isGeneratingOutline || !presentationInput.trim()}
        >
          <RefreshCw size={20} />
        </button>
      </div>

      {outlineError && (
        <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
          <div>{outlineError}</div>
          <div className="mt-1 text-xs text-red-600">
            请检查后端模型配置（`DEEPSEEK_API_KEY` / `OPENAI_API_KEY`）后重试。
          </div>
          <button
            onClick={handleGenerateOutline}
            disabled={!presentationInput.trim() || isGeneratingOutline}
            className="mt-2 rounded bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700 disabled:opacity-50"
          >
            重试生成目录
          </button>
        </div>
      )}
    </div>
  );
}
