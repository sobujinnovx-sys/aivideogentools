import json
import asyncio
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.config import settings
from app.models.job import Job, JobStatus
from app.models.video import Video
from app.models.credit import CreditTransaction, TransactionType
from app.models.user import User
from app.services.storage import storage_service


async def _update_job(db: AsyncSession, job: Job, **kwargs):
    for key, value in kwargs.items():
        setattr(job, key, value)
    await db.commit()


async def _run_generation(job_id: str):
    async with async_session() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return

        await _update_job(db, job, status=JobStatus.PROCESSING, started_at=datetime.now(timezone.utc), progress=0.1)

        try:
            model_name = job.model
            frames = await _generate_frames(job, db)

            await _update_job(db, job, progress=0.6)

            video_path = await _encode_video(frames, job)

            await _update_job(db, job, progress=0.8)

            stored_path = await storage_service.save_video_from_path(video_path, job.id)

            thumb_path = await _generate_thumbnail(video_path, job.id)

            file_size = Path(video_path).stat().st_size

            resolution = _get_resolution(job.aspect_ratio)

            video = Video(
                user_id=job.user_id,
                job_id=job.id,
                prompt=job.prompt,
                duration=job.duration,
                aspect_ratio=job.aspect_ratio,
                model_used=model_name,
                file_path=stored_path,
                thumbnail_path=thumb_path,
                file_size=file_size,
                resolution=resolution,
            )
            db.add(video)

            await _update_job(
                db, job,
                status=JobStatus.COMPLETED,
                progress=1.0,
                completed_at=datetime.now(timezone.utc),
            )

            import os
            if os.path.exists(video_path):
                os.remove(video_path)

        except Exception as e:
            await _update_job(
                db, job,
                status=JobStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.now(timezone.utc),
            )

            user = await db.execute(select(User).where(User.id == job.user_id))
            user_obj = user.scalar_one_or_none()
            if user_obj:
                user_obj.credits += job.credits_used
                db.add(CreditTransaction(
                    user_id=job.user_id,
                    amount=job.credits_used,
                    type=TransactionType.REFUND,
                    description=f"Refund for failed job {job.id}",
                    job_id=job.id,
                ))
                await db.commit()


async def _generate_frames(job: Job, db: AsyncSession) -> list[str]:
    """Generate video frames using the selected AI model."""
    frames_dir = tempfile.mkdtemp()

    model = job.model
    prompt = job.prompt
    duration = job.duration
    fps = 24
    total_frames = duration * fps

    image_urls = json.loads(job.image_urls) if job.image_urls else []

    if model == "wan2.1":
        frames = await _run_wan21(prompt, total_frames, image_urls, frames_dir, job.aspect_ratio)
    elif model == "ltx-video":
        frames = await _run_ltx_video(prompt, total_frames, image_urls, frames_dir, job.aspect_ratio)
    elif model == "cogvideox":
        frames = await _run_cogvideox(prompt, total_frames, image_urls, frames_dir, job.aspect_ratio)
    else:
        frames = await _run_wan21(prompt, total_frames, image_urls, frames_dir, job.aspect_ratio)

    return frames


async def _run_wan21(prompt: str, total_frames: int, images: list, output_dir: str, aspect: str) -> list[str]:
    """Placeholder for Wan 2.1 model inference."""
    width, height = _get_dimensions(aspect)

    frame_paths = []
    for i in range(min(total_frames, 48)):
        frame_path = Path(output_dir) / f"frame_{i:04d}.png"
        _create_placeholder_frame(frame_path, width, height, i, total_frames)
        frame_paths.append(str(frame_path))

    return frame_paths


async def _run_ltx_video(prompt: str, total_frames: int, images: list, output_dir: str, aspect: str) -> list[str]:
    """Placeholder for LTX Video model inference."""
    return await _run_wan21(prompt, total_frames, images, output_dir, aspect)


async def _run_cogvideox(prompt: str, total_frames: int, images: list, output_dir: str, aspect: str) -> list[str]:
    """Placeholder for CogVideoX model inference."""
    return await _run_wan21(prompt, total_frames, images, output_dir, aspect)


def _create_placeholder_frame(path: Path, width: int, height: int, frame_idx: int, total: int):
    """Create a placeholder frame for testing without GPU."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        progress = frame_idx / max(total - 1, 1)
        r = int(30 + progress * 50)
        g = int(50 + progress * 100)
        b = int(100 + progress * 155)

        img = Image.new("RGB", (width, height), (r, g, b))
        draw = ImageDraw.Draw(img)

        bar_width = int(width * 0.6)
        bar_height = 20
        bar_x = (width - bar_width) // 2
        bar_y = height - 60
        draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], outline="white", width=2)
        fill_width = int(bar_width * progress)
        draw.rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height], fill="white")

        text = f"Frame {frame_idx + 1}/{total}"
        draw.text((width // 2 - 40, bar_y - 30), text, fill="white")

        img.save(str(path))
    except ImportError:
        import struct
        bmp_data = b""
        row_size = (width * 3 + 3) & ~3
        for y in range(height):
            for x in range(width):
                bmp_data += struct.pack("BBB", 50, 100, 200)
            bmp_data += b"\x00" * (row_size - width * 3)

        with open(str(path), "wb") as f:
            f.write(bmp_data)


async def _encode_video(frame_paths: list[str], job: Job) -> str:
    """Encode frames to MP4 using FFmpeg."""
    output_path = tempfile.mktemp(suffix=".mp4")

    fps = 24
    width, height = _get_dimensions(job.aspect_ratio)

    input_pattern = str(Path(frame_paths[0]).parent / "frame_%04d.png")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", input_pattern,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

    return output_path


async def _generate_thumbnail(video_path: str, job_id: str) -> str:
    """Extract a thumbnail from the video."""
    thumb_path = tempfile.mktemp(suffix=".jpg")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", "thumbnail,scale=320:-1",
        "-frames:v", "1",
        thumb_path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await process.communicate()

    if process.returncode == 0 and Path(thumb_path).exists():
        with open(thumb_path, "rb") as f:
            content = f.read()
        return await storage_service.save_thumbnail(content, job_id)

    return ""


def _get_dimensions(aspect: str) -> tuple[int, int]:
    if aspect == "9:16":
        return 720, 1280
    elif aspect == "1:1":
        return 720, 720
    return 1280, 720


def _get_resolution(aspect: str) -> str:
    w, h = _get_dimensions(aspect)
    return f"{w}x{h}"


def process_video_job(job_id: str):
    """RQ entry point — runs the async pipeline in a sync context."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run_generation(job_id))
    finally:
        loop.close()
