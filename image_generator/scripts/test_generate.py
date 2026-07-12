import asyncio
import os
import time

from image_generator import generate_image

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "sdxl_test_output.png")


async def main() -> None:
    print("starting generation (this triggers model download+load on first run)")
    started = time.monotonic()

    image_bytes = await generate_image(
        "make a ultra realistic photo of a cute baby sea otter",
    )

    elapsed = time.monotonic() - started
    with open(OUTPUT_PATH, "wb") as f:
        f.write(image_bytes)

    print(f"done in {elapsed:.1f}s, wrote {len(image_bytes)} bytes to {OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # The GPU work runs in a background thread (asyncio.to_thread) and
        # CUDA calls don't respond to signals mid-kernel, so asyncio.run's
        # graceful shutdown would hang waiting for that thread. Force-exit
        # the whole process instead - the OS reclaims the CUDA context.
        print("interrupted, forcing exit")
        os._exit(1)
