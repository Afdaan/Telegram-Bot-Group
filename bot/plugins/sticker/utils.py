import io
import os
import uuid
import asyncio
import tempfile
from PIL import Image
from bot.logger import get_logger

logger = get_logger(__name__)

STICKER_SIZE = 512
MAX_VIDEO_STICKER_BYTES = 256 * 1024


async def run_ffmpeg(*args: str) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")


def resize_to_sticker(image: Image.Image) -> Image.Image:
    width, height = image.size
    if width >= height:
        new_width = STICKER_SIZE
        new_height = max(1, int((STICKER_SIZE / width) * height))
    else:
        new_height = STICKER_SIZE
        new_width = max(1, int((STICKER_SIZE / height) * width))
    return image.resize((new_width, new_height), Image.LANCZOS)


async def image_to_webp(file_obj) -> io.BytesIO:
    photo_bytes = await file_obj.download_as_bytearray()
    image = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
    image = resize_to_sticker(image)

    output = io.BytesIO()
    image.save(output, format="WEBP")
    output.seek(0)
    return output


async def video_to_webm(file_obj) -> io.BytesIO | None:
    tmp_dir = tempfile.mkdtemp()
    uid = uuid.uuid4().hex[:8]
    input_path = os.path.join(tmp_dir, f"{uid}_input.mp4")
    output_path = os.path.join(tmp_dir, f"{uid}_output.webm")

    try:
        file_bytes = await file_obj.download_as_bytearray()
        with open(input_path, "wb") as f:
            f.write(file_bytes)

        for bitrate, fps in [("400k", 30), ("200k", 24)]:
            retcode, _, stderr = await run_ffmpeg(
                "-y", "-i", input_path,
                "-t", "3",
                "-vf", f"scale='if(gt(iw,ih),{STICKER_SIZE},-2)':'if(gt(ih,iw),{STICKER_SIZE},-2)',fps={fps}",
                "-c:v", "libvpx-vp9",
                "-b:v", bitrate,
                "-an",
                "-pix_fmt", "yuva420p",
                output_path,
            )

            if retcode != 0:
                logger.error(f"ffmpeg error (bitrate={bitrate}): {stderr}")
                return None

            if os.path.getsize(output_path) <= MAX_VIDEO_STICKER_BYTES:
                break
        else:
            logger.error("Video sticker too large even after retry")
            return None

        with open(output_path, "rb") as f:
            webm_bytes = f.read()

        webm_io = io.BytesIO(webm_bytes)
        webm_io.name = "sticker.webm"
        return webm_io

    except Exception as e:
        logger.error(f"Error processing video sticker: {e}")
        return None
    finally:
        _cleanup_files(tmp_dir, input_path, output_path)


async def video_to_gif(input_bytes: bytes) -> io.BytesIO | None:
    tmp_dir = tempfile.mkdtemp()
    uid = uuid.uuid4().hex[:8]
    input_path = os.path.join(tmp_dir, f"{uid}_input.webm")
    output_path = os.path.join(tmp_dir, f"{uid}_output.gif")

    try:
        with open(input_path, "wb") as f:
            f.write(input_bytes)

        retcode, _, stderr = await run_ffmpeg(
            "-y", "-i", input_path,
            "-vf", "fps=15,scale=256:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", "0",
            output_path,
        )

        if retcode != 0:
            logger.error(f"ffmpeg error converting to GIF: {stderr}")
            return None

        with open(output_path, "rb") as f:
            gif_bytes = f.read()

        gif_io = io.BytesIO(gif_bytes)
        gif_io.name = "sticker.gif"
        return gif_io

    except Exception as e:
        logger.error(f"Error converting to GIF: {e}")
        return None
    finally:
        _cleanup_files(tmp_dir, input_path, output_path)


def _cleanup_files(tmp_dir: str, *paths: str):
    for p in paths:
        if os.path.exists(p):
            os.remove(p)
    if os.path.exists(tmp_dir):
        os.rmdir(tmp_dir)
