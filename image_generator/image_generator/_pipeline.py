import threading

import torch
from diffusers import StableDiffusionXLImg2ImgPipeline, StableDiffusionXLPipeline
from huggingface_hub import snapshot_download

_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_DTYPE = torch.float16 if _DEVICE == "cuda" else torch.float32

_load_lock = threading.Lock()
_text2img_pipe: StableDiffusionXLPipeline | None = None
_img2img_pipe: StableDiffusionXLImg2ImgPipeline | None = None


def _load() -> None:
    global _text2img_pipe, _img2img_pipe
    if _text2img_pipe is not None:
        return

    with _load_lock:
        if _text2img_pipe is not None:
            return

        if _DEVICE == "cuda":
            # diffusers' automatic variant-vs-default file selection is unreliable
            # for this repo, so the fp16 files are fetched explicitly and loaded
            # from the local snapshot to guarantee only ~7GB (not ~15GB) is pulled.
            local_dir = snapshot_download(
                _MODEL_ID,
                allow_patterns=["*.fp16.safetensors", "*.json", "*.txt"],
            )
            pipe = StableDiffusionXLPipeline.from_pretrained(
                local_dir,
                torch_dtype=_DTYPE,
                use_safetensors=True,
                variant="fp16",
                local_files_only=True,
            )
        else:
            pipe = StableDiffusionXLPipeline.from_pretrained(
                _MODEL_ID, torch_dtype=_DTYPE, use_safetensors=True
            )
        pipe.vae.enable_slicing()
        pipe.vae.enable_tiling()

        pipe.to(_DEVICE)

        _text2img_pipe = pipe


def get_device() -> str:
    return _DEVICE


def get_text2img_pipeline() -> StableDiffusionXLPipeline:
    _load()
    assert _text2img_pipe is not None
    return _text2img_pipe


def get_img2img_pipeline() -> StableDiffusionXLImg2ImgPipeline:
    global _img2img_pipe
    _load()
    if _img2img_pipe is None:
        with _load_lock:
            if _img2img_pipe is None:
                _img2img_pipe = StableDiffusionXLImg2ImgPipeline.from_pipe(_text2img_pipe)
    return _img2img_pipe
