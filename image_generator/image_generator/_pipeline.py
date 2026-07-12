import threading
from pathlib import Path

import torch
from diffusers import (
    AutoencoderKL,
    StableDiffusionXLImg2ImgPipeline,
    StableDiffusionXLPipeline,
    UNet2DConditionModel,
)
from diffusers.schedulers import EulerDiscreteScheduler
from safetensors.torch import load_file as load_safetensors
from transformers import CLIPTextConfig, CLIPTextModel, CLIPTextModelWithProjection, CLIPTokenizer

from . import _weights

_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_DTYPE = torch.float16 if _DEVICE == "cuda" else torch.float32

_load_lock = threading.Lock()
_text2img_pipe: StableDiffusionXLPipeline | None = None
_img2img_pipe: StableDiffusionXLImg2ImgPipeline | None = None


def _load_transformers_weights(cls, config_cls, local_dir: str, subfolder: str, dtype):
    # `from_pretrained(..., variant="fp16", local_files_only=True)` is unreliable
    # for this repo: it can still silently fetch the fp32 "model.safetensors"
    # over the network even when the fp16 file is present locally. Loading the
    # config and weights file explicitly, by exact known filename, sidesteps
    # that variant-resolution machinery entirely.
    config = config_cls.from_pretrained(local_dir, subfolder=subfolder)
    model = cls(config)
    weights_path = Path(local_dir) / subfolder / "model.fp16.safetensors"
    model.load_state_dict(load_safetensors(str(weights_path)))
    return model.to(dtype)


def _load_diffusers_weights(cls, local_dir: str, subfolder: str, dtype):
    config = cls.load_config(local_dir, subfolder=subfolder)
    model = cls.from_config(config)
    weights_path = Path(local_dir) / subfolder / "diffusion_pytorch_model.fp16.safetensors"
    model.load_state_dict(load_safetensors(str(weights_path)))
    return model.to(dtype)


def _load() -> None:
    global _text2img_pipe
    if _text2img_pipe is not None:
        return

    with _load_lock:
        if _text2img_pipe is not None:
            return

        if _DEVICE == "cuda":
            local_dir = _weights.ensure_fp16_weights()
            tokenizer = CLIPTokenizer.from_pretrained(local_dir, subfolder="tokenizer")
            tokenizer_2 = CLIPTokenizer.from_pretrained(local_dir, subfolder="tokenizer_2")
            scheduler = EulerDiscreteScheduler.from_pretrained(local_dir, subfolder="scheduler")
            text_encoder = _load_transformers_weights(
                CLIPTextModel, CLIPTextConfig, local_dir, "text_encoder", _DTYPE
            )
            text_encoder_2 = _load_transformers_weights(
                CLIPTextModelWithProjection, CLIPTextConfig, local_dir, "text_encoder_2", _DTYPE
            )
            vae = _load_diffusers_weights(AutoencoderKL, local_dir, "vae", _DTYPE)
            unet = _load_diffusers_weights(UNet2DConditionModel, local_dir, "unet", _DTYPE)
        else:
            tokenizer = CLIPTokenizer.from_pretrained(_MODEL_ID, subfolder="tokenizer")
            tokenizer_2 = CLIPTokenizer.from_pretrained(_MODEL_ID, subfolder="tokenizer_2")
            scheduler = EulerDiscreteScheduler.from_pretrained(_MODEL_ID, subfolder="scheduler")
            text_encoder = CLIPTextModel.from_pretrained(_MODEL_ID, subfolder="text_encoder")
            text_encoder_2 = CLIPTextModelWithProjection.from_pretrained(
                _MODEL_ID, subfolder="text_encoder_2"
            )
            vae = AutoencoderKL.from_pretrained(_MODEL_ID, subfolder="vae")
            unet = UNet2DConditionModel.from_pretrained(_MODEL_ID, subfolder="unet")

        pipe = StableDiffusionXLPipeline(
            vae=vae,
            text_encoder=text_encoder,
            text_encoder_2=text_encoder_2,
            tokenizer=tokenizer,
            tokenizer_2=tokenizer_2,
            unet=unet,
            scheduler=scheduler,
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
