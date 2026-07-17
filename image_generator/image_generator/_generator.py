import asyncio
from typing import Callable

import torch
from PIL import Image

from . import _pipeline
from ._image_codec import bytes_to_image, image_to_bytes

_NUM_INFERENCE_STEPS = 50
_DEFAULT_IMG2IMG_STRENGTH = 0.6

ProgressCallback = Callable[[int, int], None]


def _generate_image_sync(
    prompt: str,
    image: bytes | None,
    on_progress: ProgressCallback | None,
    strength: float | None,
) -> Image.Image:
    generator = torch.Generator(device=_pipeline.get_device())
    effective_strength = _DEFAULT_IMG2IMG_STRENGTH if strength is None else strength

    # img2img only runs strength * num_inference_steps actual denoising steps,
    # so the reported total has to match or progress would never hit 100%.
    total_steps = (
        _NUM_INFERENCE_STEPS
        if image is None
        else max(1, round(_NUM_INFERENCE_STEPS * effective_strength))
    )

    def _step_callback(pipe, step_index, timestep, callback_kwargs):
        if on_progress is not None:
            on_progress(step_index + 1, total_steps)
        return callback_kwargs

    if image is None:
        pipe = _pipeline.get_text2img_pipeline()
        result = pipe(
            prompt=prompt,
            generator=generator,
            num_inference_steps=_NUM_INFERENCE_STEPS,
            callback_on_step_end=_step_callback,
        )
    else:
        pipe = _pipeline.get_img2img_pipeline()
        result = pipe(
            prompt=prompt,
            image=bytes_to_image(image),
            generator=generator,
            num_inference_steps=_NUM_INFERENCE_STEPS,
            strength=effective_strength,
            callback_on_step_end=_step_callback,
        )

    return result.images[0]


async def _generate_image(
    prompt: str,
    image: bytes | None = None,
    on_progress: ProgressCallback | None = None,
    strength: float | None = None,
) -> bytes:
    pil_image: Image.Image = await asyncio.to_thread(
        _generate_image_sync, prompt, image, on_progress, strength
    )
    return image_to_bytes(pil_image)
