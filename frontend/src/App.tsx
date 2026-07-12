import { useEffect, useState } from "react";
import ChatPanel, { ChatMessage } from "@/components/ChatPanel";
import DownloadWeightsScreen from "@/components/DownloadWeightsScreen";
import ImagePanel from "@/components/ImagePanel";
import { generateImage, GenerateProgressEvent } from "@/lib/generateImage";
import { checkWeightsDownloaded, downloadWeights } from "@/lib/weights";

type WeightsStatus = "checking" | "missing" | "downloading" | "error" | "ready";

export default function App() {
  const [weightsStatus, setWeightsStatus] = useState<WeightsStatus>("checking");
  const [downloadProgress, setDownloadProgress] = useState<{
    downloaded: number;
    total: number;
  } | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState<{ step: number; total: number } | null>(null);

  useEffect(() => {
    let cancelled = false;
    checkWeightsDownloaded()
      .then((downloaded) => {
        if (!cancelled) setWeightsStatus(downloaded ? "ready" : "missing");
      })
      .catch(() => {
        if (!cancelled) setWeightsStatus("missing");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleDownloadClick() {
    setWeightsStatus("downloading");
    setDownloadProgress(null);
    setDownloadError(null);

    try {
      await downloadWeights((downloaded, total) => {
        setDownloadProgress({ downloaded, total });
      });
      setWeightsStatus("ready");
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : "Unknown error");
      setWeightsStatus("error");
    }
  }

  function addMessage(role: ChatMessage["role"], content: string) {
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role, content }]);
  }

  async function handleSend(prompt: string, attachedImage: File | null) {
    addMessage("user", prompt);
    setIsGenerating(true);
    setProgress(null);

    function handleEvent(event: GenerateProgressEvent) {
      if (event.type === "progress") {
        setProgress({ step: event.step, total: event.total });
      } else if (event.type === "done") {
        setImageUrl(`data:image/png;base64,${event.image}`);
        addMessage("status", "Image generated.");
      } else if (event.type === "error") {
        addMessage("status", `Error: ${event.message}`);
      }
    }

    try {
      await generateImage(prompt, attachedImage, handleEvent);
    } catch (err) {
      addMessage("status", `Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setIsGenerating(false);
      setProgress(null);
    }
  }

  if (weightsStatus === "checking") {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-neutral-950 text-neutral-100">
        <p className="text-sm text-neutral-400">Checking model weights...</p>
      </div>
    );
  }

  if (weightsStatus !== "ready") {
    return (
      <DownloadWeightsScreen
        status={weightsStatus}
        progress={downloadProgress}
        errorMessage={downloadError}
        onDownloadClick={handleDownloadClick}
      />
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-neutral-950 text-neutral-100">
      <ChatPanel messages={messages} isGenerating={isGenerating} onSend={handleSend} />
      <ImagePanel imageUrl={imageUrl} isGenerating={isGenerating} progress={progress} />
    </div>
  );
}
