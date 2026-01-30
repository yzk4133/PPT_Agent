"use client";
import { useState } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePresentationSlides } from "@/hooks/presentation/usePresentationSlides";
import { usePresentationState } from "@/states/presentation-state";

export function DownloadPPT() {
  const { items } = usePresentationSlides();
  const [loading, setLoading] = useState(false);
  const { presentationInput, references } = usePresentationState();

  const handleDownload = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/presentation/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: presentationInput, items, references }),
      });
      const data = await res.json();
      if (data.url) {
        // 触发浏览器下载
        const link = document.createElement("a");
        link.href = data.url;
        link.download = "presentation.pptx";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        alert("下载失败，请稍后重试");
      }
    } catch (e) {
      alert("下载失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      className="text-muted-foreground hover:text-foreground"
      onClick={handleDownload}
      disabled={loading}
    >
      <Download className="mr-1 h-4 w-4" />
      {loading ? "下载中..." : "下载PPT"}
    </Button>
  );
}