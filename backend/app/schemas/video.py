from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=2000)
    duration: int = Field(default=15, ge=5, le=15)
    aspect_ratio: str = Field(default="16:9", pattern="^(16:9|9:16|1:1)$")
    model: str = Field(default="wan2.1")
    image_urls: list[str] = Field(default_factory=list, max_length=5)


class JobResponse(BaseModel):
    id: str
    status: str
    progress: float
    prompt: str
    duration: int
    aspect_ratio: str
    model: str
    error_message: str | None
    credits_used: int
    created_at: str
    started_at: str | None
    completed_at: str | None

    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    id: str
    prompt: str
    duration: int
    aspect_ratio: str
    model_used: str
    file_path: str
    thumbnail_path: str | None
    file_size: int
    resolution: str
    created_at: str

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    videos: list[VideoResponse]
    total: int
