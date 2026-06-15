import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.video import Video
from app.models.credit import CreditTransaction, TransactionType
from app.schemas.video import GenerateRequest, JobResponse, VideoResponse, VideoListResponse
from app.services.storage import storage_service
from app.services.queue import queue_service

router = APIRouter()


def get_credits_for_duration(duration: int) -> int:
    if duration <= 5:
        return settings.CREDITS_5S
    elif duration <= 10:
        return settings.CREDITS_10S
    return settings.CREDITS_15S


@router.post("/generate", response_model=JobResponse)
async def generate_video(
    data: GenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    credits_needed = get_credits_for_duration(data.duration)
    if user.credits < credits_needed:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {credits_needed}, have {user.credits}")

    user.credits -= credits_needed
    db.add(CreditTransaction(
        user_id=user.id,
        amount=-credits_needed,
        type=TransactionType.DEBIT,
        description=f"Video generation ({data.duration}s)",
    ))

    job = Job(
        user_id=user.id,
        prompt=data.prompt,
        duration=data.duration,
        aspect_ratio=data.aspect_ratio,
        model=data.model,
        image_urls=json.dumps(data.image_urls) if data.image_urls else None,
        credits_used=credits_needed,
        status=JobStatus.QUEUED,
    )
    db.add(job)
    await db.flush()

    rq_job = queue_service.enqueue_job(job.id)
    job.rq_job_id = rq_job.id if rq_job else None

    return _job_to_response(job)


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    url = await storage_service.upload_image(content, file.filename or "image.png")
    return {"url": url}


@router.get("/", response_model=VideoListResponse)
async def list_videos(
    page: int = 1,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit

    count_result = await db.execute(select(func.count(Video.id)).where(Video.user_id == user.id))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Video).where(Video.user_id == user.id).order_by(Video.created_at.desc()).offset(offset).limit(limit)
    )
    videos = result.scalars().all()

    return VideoListResponse(
        videos=[_video_to_response(v) for v in videos],
        total=total,
    )


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Video).where(Video.id == video_id, Video.user_id == user.id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    await storage_service.delete_file(video.file_path)
    if video.thumbnail_path:
        await storage_service.delete_file(video.thumbnail_path)

    await db.delete(video)
    return {"message": "Video deleted"}


def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        status=job.status.value,
        progress=job.progress,
        prompt=job.prompt,
        duration=job.duration,
        aspect_ratio=job.aspect_ratio,
        model=job.model,
        error_message=job.error_message,
        credits_used=job.credits_used,
        created_at=job.created_at.isoformat() if job.created_at else "",
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


def _video_to_response(video: Video) -> VideoResponse:
    return VideoResponse(
        id=video.id,
        prompt=video.prompt,
        duration=video.duration,
        aspect_ratio=video.aspect_ratio,
        model_used=video.model_used,
        file_path=video.file_path,
        thumbnail_path=video.thumbnail_path,
        file_size=video.file_size,
        resolution=video.resolution,
        created_at=video.created_at.isoformat() if video.created_at else "",
    )
