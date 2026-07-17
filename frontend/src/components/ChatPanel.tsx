import { useRef, useState } from "react";

export type ChatMessage = {
  id: string;
  role: "user" | "status";
  content: string;
};

type Props = {
  messages: ChatMessage[];
  isGenerating: boolean;
  onSend: (prompt: string, image: File | null) => void;
  allowImageAttach: boolean;
};

export default function ChatPanel({ messages, isGenerating, onSend, allowImageAttach }: Props) {
  const [prompt, setPrompt] = useState("");
  const [attachedImage, setAttachedImage] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed || isGenerating) return;

    onSend(trimmed, attachedImage);
    setPrompt("");
    setAttachedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  return (
    <div className="flex w-1/2 min-w-[320px] flex-col border-r border-neutral-800">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-sm text-neutral-500">Describe what you want to generate...</p>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={
              m.role === "user"
                ? "ml-auto max-w-[80%] rounded-lg bg-blue-600 px-3 py-2 text-sm text-white"
                : "max-w-[80%] rounded-lg bg-neutral-800 px-3 py-2 text-sm text-neutral-300"
            }
          >
            {m.content}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-2 border-t border-neutral-800 p-3">
        {allowImageAttach && attachedImage && (
          <div className="flex items-center gap-2 text-xs text-neutral-400">
            <span>📎 {attachedImage.name}</span>
            <button
              type="button"
              onClick={() => {
                setAttachedImage(null);
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
              className="text-red-400 hover:text-red-300"
            >
              remove
            </button>
          </div>
        )}
        {!allowImageAttach && (
          <p className="text-xs text-neutral-500">Continuing from the last generated image</p>
        )}
        <div className="flex items-center gap-2">
          {allowImageAttach && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                id="image-attach"
                onChange={(e) => setAttachedImage(e.target.files?.[0] ?? null)}
              />
              <label
                htmlFor="image-attach"
                className="cursor-pointer rounded-md border border-neutral-700 px-2 py-2 text-sm hover:bg-neutral-800"
                title="Attach an image"
              >
                📎
              </label>
            </>
          )}
          <input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want..."
            className="flex-1 rounded-md border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-blue-500"
            disabled={isGenerating}
          />
          <button
            type="submit"
            disabled={isGenerating || !prompt.trim()}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            {isGenerating ? "Generating..." : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}
