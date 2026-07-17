import { waitForPywebview } from "./pywebview";

export type GenerateProgressEvent =
  | { type: "progress"; step: number; total: number }
  | { type: "done"; image: string }
  | { type: "error"; message: string };

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string).split(",")[1] ?? "");
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export async function generateImage(
  prompt: string,
  image: File | string | null,
  strength: number | null,
  onEvent: (event: GenerateProgressEvent) => void
): Promise<void> {
  await waitForPywebview();

  function handleProgress(e: Event) {
    const { step, total } = (e as CustomEvent<{ step: number; total: number }>).detail;
    onEvent({ type: "progress", step, total });
  }
  window.addEventListener("generate-progress", handleProgress);

  try {
    const imageBase64 =
      image === null ? null : typeof image === "string" ? image : await fileToBase64(image);
    const result = await window.pywebview!.api.generate_image(prompt, imageBase64, strength);
    if ("error" in result) {
      onEvent({ type: "error", message: result.error });
    } else {
      onEvent({ type: "done", image: result.image });
    }
  } catch (err) {
    onEvent({ type: "error", message: err instanceof Error ? err.message : String(err) });
  } finally {
    window.removeEventListener("generate-progress", handleProgress);
  }
}
