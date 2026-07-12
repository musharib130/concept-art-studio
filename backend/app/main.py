import argparse
import asyncio
import base64
import threading
from pathlib import Path

import webview
from image_generator import are_weights_downloaded, download_weights, generate_image


class Api:
    def __init__(self) -> None:
        self._window: webview.Window | None = None
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def check_weights(self) -> dict:
        return {"downloaded": are_weights_downloaded()}

    def download_weights(self) -> dict:
        future = asyncio.run_coroutine_threadsafe(self._download_weights(), self._loop)
        try:
            future.result()
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def _download_weights(self) -> None:
        def on_progress(downloaded: int, total: int) -> None:
            if self._window is not None:
                self._window.evaluate_js(f"window.__onDownloadProgress({downloaded}, {total})")

        await download_weights(on_progress=on_progress)

    def generate_image(self, prompt: str, image_b64: str | None) -> dict:
        future = asyncio.run_coroutine_threadsafe(
            self._generate(prompt, image_b64), self._loop
        )
        try:
            return future.result()
        except Exception as exc:
            return {"error": str(exc)}

    async def _generate(self, prompt: str, image_b64: str | None) -> dict:
        image_bytes = base64.b64decode(image_b64) if image_b64 else None

        def on_progress(step: int, total: int) -> None:
            if self._window is not None:
                self._window.evaluate_js(f"window.__onGenerateProgress({step}, {total})")

        result_bytes = await generate_image(prompt, image_bytes, on_progress=on_progress)
        return {"image": base64.b64encode(result_bytes).decode("ascii")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", action="store_true", help="Load the Vite dev server instead of the built frontend")
    args = parser.parse_args()

    if args.dev:
        target = "http://localhost:5173"
    else:
        target = str(
            (Path(__file__).resolve().parents[2] / "frontend" / "dist" / "index.html")
        )

    api = Api()
    window = webview.create_window(
        "Concept Art Studio", url=target, js_api=api, width=1280, height=800
    )
    api.set_window(window)
    webview.start(debug=args.dev)


if __name__ == "__main__":
    main()
