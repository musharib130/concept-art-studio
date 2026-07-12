import threading
from pathlib import Path
from typing import Callable

from huggingface_hub import HfApi, constants, snapshot_download

_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
_FP16_ALLOW_PATTERNS = ["*.fp16.safetensors", "*.json", "*.txt"]
_POLL_INTERVAL_SECONDS = 0.5

# SDXL's default VAE is numerically unstable in fp16 and needs an expensive
# fp32 upcast during decode (force_upcast=True), which can OOM on
# VRAM-constrained GPUs once other consumers (e.g. the desktop app's own
# GPU-accelerated UI) are also using VRAM. This community-maintained VAE is
# retrained to decode correctly in pure fp16 (force_upcast=false), avoiding
# the upcast - and the OOM - entirely.
_VAE_FIX_MODEL_ID = "madebyollin/sdxl-vae-fp16-fix"
_VAE_FIX_DIR = Path(constants.HF_HOME) / "concept-art-studio-weights" / "sdxl-vae-fp16-fix"

# Downloaded as plain files into a dedicated folder instead of through
# huggingface_hub's default hardlink/symlink cache-blob system: on Windows,
# creating those links requires Developer Mode or admin rights, and the
# automatic fallback to plain copying isn't reliable in practice (it can still
# raise OSError: [WinError 1314] partway through a download). A plain local_dir
# sidesteps linking entirely - files are written directly, so this can't fail
# that way regardless of the end user's Windows permissions.
_WEIGHTS_DIR = Path(constants.HF_HOME) / "concept-art-studio-weights" / "stable-diffusion-xl-base-1.0"

# The specific large weight files that must exist for generation to actually work.
_WEIGHT_FILES = [
    "text_encoder/model.fp16.safetensors",
    "text_encoder_2/model.fp16.safetensors",
    "vae/diffusion_pytorch_model.fp16.safetensors",
    "unet/diffusion_pytorch_model.fp16.safetensors",
]

DownloadProgressCallback = Callable[[int, int], None]  # (bytes_downloaded, bytes_total)


def are_weights_downloaded() -> bool:
    """Check whether all fp16 weight files are already fully downloaded, without downloading anything."""
    return all((_WEIGHTS_DIR / f).is_file() for f in _WEIGHT_FILES)


def _expected_total_bytes() -> int:
    info = HfApi().model_info(_MODEL_ID, files_metadata=True)
    return sum(
        f.size
        for f in info.siblings
        if f.size and (f.rfilename.endswith(".fp16.safetensors") or f.rfilename.endswith((".json", ".txt")))
    )


def _dir_size(path: Path) -> int:
    total = 0
    if not path.is_dir():
        return 0
    for entry in path.rglob("*"):
        if entry.is_file():
            try:
                total += entry.stat().st_size
            except OSError:
                pass
    return total


def download_weights(on_progress: DownloadProgressCallback | None = None) -> str:
    """Download the fp16 weight set into _WEIGHTS_DIR, returning its path as a string.

    If on_progress is given, it's called periodically with (bytes_downloaded,
    bytes_total) while the download runs. Progress is derived by polling the
    on-disk directory size rather than hooking huggingface_hub's tqdm progress
    bars, since those are created per-file (mixing byte-count and file-count
    units) and don't reliably reflect real-time state for files staged via Xet.
    """
    if on_progress is None:
        return snapshot_download(
            _MODEL_ID, allow_patterns=_FP16_ALLOW_PATTERNS, local_dir=_WEIGHTS_DIR
        )

    total = _expected_total_bytes()
    result: dict[str, str] = {}
    error: dict[str, BaseException] = {}

    def _run() -> None:
        try:
            result["path"] = snapshot_download(
                _MODEL_ID, allow_patterns=_FP16_ALLOW_PATTERNS, local_dir=_WEIGHTS_DIR
            )
        except BaseException as exc:
            error["exc"] = exc

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    while thread.is_alive():
        on_progress(min(_dir_size(_WEIGHTS_DIR), total), total)
        thread.join(timeout=_POLL_INTERVAL_SECONDS)

    if "exc" in error:
        raise error["exc"]

    on_progress(total, total)
    return result["path"]


def ensure_fp16_weights(on_progress: DownloadProgressCallback | None = None) -> str:
    """Ensure the fp16-only weight set is present locally, returning its local directory."""
    if are_weights_downloaded():
        return str(_WEIGHTS_DIR)
    return download_weights(on_progress)


def ensure_vae_fix() -> str:
    """Ensure the fp16-safe replacement VAE is present locally, returning its directory."""
    weights_file = _VAE_FIX_DIR / "diffusion_pytorch_model.safetensors"
    if not weights_file.is_file():
        snapshot_download(
            _VAE_FIX_MODEL_ID,
            allow_patterns=["diffusion_pytorch_model.safetensors", "config.json"],
            local_dir=_VAE_FIX_DIR,
        )
    return str(_VAE_FIX_DIR)
