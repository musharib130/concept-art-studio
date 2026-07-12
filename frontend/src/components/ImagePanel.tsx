type Props = {
  imageUrl: string | null;
  isGenerating: boolean;
  progress: { step: number; total: number } | null;
};

export default function ImagePanel({ imageUrl, isGenerating, progress }: Props) {
  const pct = progress ? Math.min(100, Math.round((progress.step / progress.total) * 100)) : 0;

  return (
    <div className="relative flex w-1/2 flex-1 items-center justify-center bg-neutral-900">
      {imageUrl ? (
        <img src={imageUrl} alt="Generated" className="max-h-full max-w-full object-contain" />
      ) : (
        !isGenerating && <p className="text-sm text-neutral-600">No image yet</p>
      )}

      {isGenerating && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-black/60 backdrop-blur-sm">
          <div className="h-2 w-2/3 max-w-xs overflow-hidden rounded-full bg-neutral-700">
            <div
              className="h-full bg-blue-500 transition-all duration-200"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-sm text-neutral-300">
            {progress ? `Generating... step ${progress.step}/${progress.total}` : "Starting..."}
          </p>
        </div>
      )}
    </div>
  );
}
