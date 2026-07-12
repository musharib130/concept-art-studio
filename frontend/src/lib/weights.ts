import { waitForPywebview } from "./pywebview";

export async function checkWeightsDownloaded(): Promise<boolean> {
  await waitForPywebview();
  const result = await window.pywebview!.api.check_weights();
  return result.downloaded;
}

export async function downloadWeights(
  onProgress: (downloaded: number, total: number) => void
): Promise<void> {
  await waitForPywebview();

  function handleProgress(e: Event) {
    const { downloaded, total } = (e as CustomEvent<{ downloaded: number; total: number }>).detail;
    onProgress(downloaded, total);
  }
  window.addEventListener("download-progress", handleProgress);

  try {
    const result = await window.pywebview!.api.download_weights();
    if (!result.ok) {
      throw new Error(result.error);
    }
  } finally {
    window.removeEventListener("download-progress", handleProgress);
  }
}
