import json
import asyncio
import tempfile
import struct
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

            video_path, thumb_path = await _encode_video(frames, job)

            await _update_job(db, job, progress=0.8)

            stored_path = await storage_service.save_video_from_path(video_path, job.id)

            if not thumb_path:
                thumb_path = await _generate_thumbnail_from_frame(frames[0], job.id)

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
            import traceback
            traceback.print_exc()
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


async def _generate_frames(job: Job, db: AsyncSession) -> list:
    """Generate video frames using the selected AI model."""
    frames_dir = tempfile.mkdtemp()

    model = job.model
    prompt = job.prompt
    duration = job.duration
    fps = 12
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


async def _run_wan21(prompt: str, total_frames: int, images: list, output_dir: str, aspect: str) -> list:
    """Placeholder for Wan 2.1 model inference — generates animated placeholder frames."""
    from PIL import Image, ImageDraw, ImageFont
    import math

    width, height = _get_dimensions(aspect)
    # Use lower res for speed in placeholder mode
    w, h = width // 2, height // 2
    total_frames = min(total_frames, 60)

    frames = []
    for i in range(total_frames):
        t = i / max(total_frames - 1, 1)

        # Animated gradient background
        r = int(20 + 40 * math.sin(t * math.pi * 2))
        g = int(30 + 80 * math.sin(t * math.pi * 2 + 1))
        b = int(80 + 120 * math.sin(t * math.pi * 2 + 2))

        img = Image.new("RGB", (w, h), (r, g, b))
        draw = ImageDraw.Draw(img)

        # Animated circle
        cx = int(w * (0.3 + 0.4 * math.sin(t * math.pi * 4)))
        cy = int(h * (0.3 + 0.4 * math.cos(t * math.pi * 3)))
        radius = int(min(w, h) * 0.15)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill="white", outline="yellow", width=2)

        # Progress bar
        bar_w = int(w * 0.6)
        bar_h = 10
        bar_x = (w - bar_w) // 2
        bar_y = h - 30
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline="white")
        draw.rectangle([bar_x, bar_y, bar_x + int(bar_w * t), bar_y + bar_h], fill="white")

        # Text
        draw.text((w // 2 - 30, bar_y - 20), f"Frame {i+1}/{total_frames}", fill="white")
        draw.text((10, 10), f"Prompt: {prompt[:40]}...", fill="white")

        frames.append(img)

    return frames


async def _run_ltx_video(prompt: str, total_frames: int, images: list, output_dir: str, aspect: str) -> list:
    return await _run_wan21(prompt, total_frames, images, output_dir, aspect)


async def _run_cogvideox(prompt: str, total_frames: int, images: list, output_dir: str, aspect: str) -> list:
    return await _run_wan21(prompt, total_frames, images, output_dir, aspect)


async def _encode_video(frames: list, job: Job) -> tuple[str, str]:
    """Encode frames to GIF (no FFmpeg needed) and generate thumbnail."""
    output_path = tempfile.mktemp(suffix=".gif")
    thumb_path = ""

    # Save as animated GIF
    duration_ms = int(1000 / 12)  # 12 fps
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )

    # Generate thumbnail from middle frame
    mid_idx = len(frames) // 2
    thumb_img = frames[mid_idx].copy()
    thumb_img.thumbnail((320, 320))
    thumb_bytes = tempfile.mktemp(suffix=".jpg")
    thumb_img.save(thumb_bytes, "JPEG", quality=80)
    with open(thumb_bytes, "rb") as f:
        thumb_content = f.read()
    thumb_path = await storage_service.save_thumbnail(thumb_content, job.id)
    import os
    os.remove(thumb_bytes)

    return output_path, thumb_path


async def _generate_thumbnail_from_frame(frame, job_id: str) -> str:
    """Generate thumbnail from a PIL Image frame."""
    thumb = frame.copy()
    thumb.thumbnail((320, 320))
    import io
    buf = io.BytesIO()
    thumb.save(buf, "JPEG", quality=80)
    return await storage_service.save_thumbnail(buf.getvalue(), job_id)


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
