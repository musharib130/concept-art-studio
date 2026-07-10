from . import _generator

__all__ = ["generate_image"]


async def generate_image(prompt: str, image: bytes | None = None) -> bytes:
    return await _generator._generate_image(prompt, image)
