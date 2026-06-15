import json
import asyncio
import tempfile
import httpx
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


REPLICATE_MODELS = {
    "wan2.1": "tencent/hunyuan-video",
    "ltx-video": "stability-ai/stable-video-diffusion",
    "cogvideox": "minimax/video-01",
}


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
            await _update_job(db, job, progress=0.2)

            video_url = await _run_replicate(job)

            await _update_job(db, job, progress=0.7)

            video_path = await _download_video(video_url, job.id)

            await _update_job(db, job, progress=0.85)

            stored_path = await storage_service.save_video_from_path(video_path, job.id)

            thumb_path = await _extract_thumbnail(video_path, job.id)

            file_size = Path(video_path).stat().st_size

            video = Video(
                user_id=job.user_id,
                job_id=job.id,
                prompt=job.prompt,
                duration=job.duration,
                aspect_ratio=job.aspect_ratio,
                model_used=job.model,
                file_path=stored_path,
                thumbnail_path=thumb_path,
                file_size=file_size,
                resolution=_get_resolution(job.aspect_ratio),
            )
            db.add(video)

            await _update_job(db, job, status=JobStatus.COMPLETED, progress=1.0, completed_at=datetime.now(timezone.utc))

            import os
            if os.path.exists(video_path):
                os.remove(video_path)

        except Exception as e:
            import traceback
            traceback.print_exc()
            await _update_job(db, job, status=JobStatus.FAILED, error_message=str(e), completed_at=datetime.now(timezone.utc))

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


async def _run_replicate(job: Job) -> str:
    """Call Replicate API to generate video."""
    import replicate

    model_name = REPLICATE_MODELS.get(job.model, REPLICATE_MODELS["wan2.1"])

    aspect_w, aspect_h = _get_dimensions(job.aspect_ratio)
    if aspect_h > aspect_w:
        aspect = "9:16"
    elif aspect_w > aspect_h:
        aspect = "16:9"
    else:
        aspect = "1:1"

    image_urls = json.loads(job.image_urls) if job.image_urls else []

    input_params = {
        "prompt": job.prompt,
        "num_frames": job.duration * 8,
        "aspect_ratio": aspect,
    }

    if image_urls:
        input_params["image"] = image_urls[0]

    output = await asyncio.to_thread(
        replicate.run,
        model_name,
        input=input_params,
    )

    if isinstance(output, str):
        return output
    elif hasattr(output, "url"):
        return output.url
    elif isinstance(output, list) and output:
        url = output[0]
        return url.url if hasattr(url, "url") else str(url)
    else:
        raise RuntimeError(f"Unexpected Replicate output: {output}")


async def _download_video(url: str, job_id: str) -> str:
    """Download video from URL to temp file."""
    output_path = tempfile.mktemp(suffix=".mp4")

    async with httpx.AsyncClient(follow_redirects=True, timeout=300) as client:
        response = await client.get(url)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

    return output_path


async def _extract_thumbnail(video_path: str, job_id: str) -> str:
    """Try to extract thumbnail with ffmpeg, fall back to placeholder."""
    try:
        import subprocess
        thumb_path = tempfile.mktemp(suffix=".jpg")
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vf", "thumbnail,scale=320:-1", "-frames:v", "1", thumb_path],
            capture_output=True, timeout=10,
        )
        if result.returncode == 0 and Path(thumb_path).exists():
            with open(thumb_path, "rb") as f:
                content = f.read()
            path = await storage_service.save_thumbnail(content, job_id)
            import os
            os.remove(thumb_path)
            return path
    except Exception:
        pass

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
    """RQ entry point."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run_generation(job_id))
    finally:
        loop.close()
