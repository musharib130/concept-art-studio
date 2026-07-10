import asyncio

import torch
from PIL import Image

from . import _pipeline
from ._image_codec import bytes_to_image, image_to_bytes


def _generate_image_sync(prompt: str, image: bytes | None) -> Image.Image:
    generator = torch.Generator(device=_pipeline.get_device())

    if image is None:
        pipe = _pipeline.get_text2img_pipeline()
        result = pipe(prompt=prompt, generator=generator)
    else:
        pipe = _pipeline.get_img2img_pipeline()
        result = pipe(prompt=prompt, image=bytes_to_image(image), generator=generator)

    return result.images[0]


async def _generate_image(prompt: str, image: bytes | None = None) -> bytes:
    pil_image: Image.Image = await asyncio.to_thread(_generate_image_sync, prompt, image)
    return image_to_bytes(pil_image)
