type Props = {
  status: "missing" | "downloading" | "error";
  progress: { downloaded: number; total: number } | null;
  errorMessage: string | null;
  onDownloadClick: () => void;
};

function formatGB(bytes: number): string {
  return (bytes / 1e9).toFixed(2);
}

export default function DownloadWeightsScreen({
  status,
  progress,
  errorMessage,
  onDownloadClick,
}: Props) {
  const pct = progress && progress.total > 0
    ? Math.min(100, Math.round((progress.downloaded / progress.total) * 100))
    : 0;

  return (
    <div className="flex h-screen w-screen flex-col items-center justify-center gap-4 bg-neutral-950 text-neutral-100">
      <h1 className="text-lg font-medium">Model weights not downloaded yet</h1>
      <p className="max-w-md text-center text-sm text-neutral-400">
        Concept Art Studio needs to download the SDXL model (~7 GB) before it can generate images.
        This only happens once.
      </p>

      {status === "missing" && (
        <button
          onClick={onDownloadClick}
          className="rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-500"
        >
          Download weights
        </button>
      )}

      {status === "downloading" && (
        <div className="flex w-full max-w-xs flex-col items-center gap-2">
          <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-700">
            <div
              className="h-full bg-blue-500 transition-all duration-200"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-sm text-neutral-300">
            {progress
              ? `${formatGB(progress.downloaded)} GB / ${formatGB(progress.total)} GB (${pct}%)`
              : "Starting download..."}
          </p>
        </div>
      )}

      {status === "error" && (
        <>
          <p className="max-w-md text-center text-sm text-red-400">
            {errorMessage ?? "Download failed."}
          </p>
          <button
            onClick={onDownloadClick}
            className="rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-500"
          >
            Retry
          </button>
        </>
      )}
    </div>
  );
}
