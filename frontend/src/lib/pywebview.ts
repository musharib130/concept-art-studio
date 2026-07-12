export async function waitForPywebview(): Promise<void> {
  if (window.pywebview?.api) return;
  await new Promise<void>((resolve) => {
    window.addEventListener("pywebviewready", () => resolve(), { once: true });
  });
}
