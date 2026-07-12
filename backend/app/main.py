import argparse
import asyncio
import base64
import ctypes
import os
import threading
from pathlib import Path

import webview
from image_generator import (
    are_weights_downloaded,
    download_weights,
    generate_image,
    preload_model,
)

_console_ctrl_handler = None  # kept alive so ctypes doesn't garbage-collect it


def _force_exit_on_console_ctrl() -> None:
    """Force-exit the whole process on Ctrl+C/close, instead of relying on
    Python's normal KeyboardInterrupt: pywebview's native window loop blocks
    that delivery on Windows, so Ctrl+C otherwise leaves the process (and its
    background threads - preload, generate, download) running indefinitely.
    """
    if os.name != "nt":
        return

    global _console_ctrl_handler
    handler_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)

    def handler(ctrl_type: int) -> int:
        # CTRL_C_EVENT=0, CTRL_BREAK_EVENT=1, CTRL_CLOSE_EVENT=2
        if ctrl_type in (0, 1, 2):
            os._exit(0)
        return 0

    _console_ctrl_handler = handler_type(handler)
    ctypes.windll.kernel32.SetConsoleCtrlHandler(_console_ctrl_handler, True)


class Api:
    def __init__(self) -> None:
        self._window: webview.Window | None = None
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

        if are_weights_downloaded():
            self._preload_model_in_background()

    def _preload_model_in_background(self) -> None:
        threading.Thread(target=preload_model, daemon=True).start()

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def check_weights(self) -> dict:
        return {"downloaded": are_weights_downloaded()}

    def download_weights(self) -> dict:
        future = asyncio.run_coroutine_threadsafe(self._download_weights(), self._loop)
        try:
            future.result()
            self._preload_model_in_background()
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
    _force_exit_on_console_ctrl()

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
        "Concept Art Studio",
        url=target,
        js_api=api,
        width=1280,
        height=800,
        text_select=True,
    )
    api.set_window(window)
    webview.start(debug=args.dev)


if __name__ == "__main__":
    main()
