import asyncio

from . import _generator, _pipeline, _weights
from ._generator import ProgressCallback
from ._weights import DownloadProgressCallback

__all__ = ["generate_image", "are_weights_downloaded", "download_weights", "preload_model"]


async def generate_image(
    prompt: str, image: bytes | None = None, on_progress: ProgressCallback | None = None
) -> bytes:
    return await _generator._generate_image(prompt, image, on_progress)


def are_weights_downloaded() -> bool:
    return _weights.are_weights_downloaded()


async def download_weights(on_progress: DownloadProgressCallback | None = None) -> None:
    await asyncio.to_thread(_weights.download_weights, on_progress)


def preload_model() -> None:
    """Eagerly load the SDXL pipeline into memory now, instead of waiting for the first generate_image call."""
    _pipeline.get_text2img_pipeline()
