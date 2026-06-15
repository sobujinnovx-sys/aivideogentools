import os
import uuid
import aiofiles
from pathlib import Path

from app.core.config import settings


class StorageService:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.base_path = Path(settings.STORAGE_PATH)
        self._ensure_dirs()

    def _ensure_dirs(self):
        for subdir in ["uploads", "videos", "thumbnails"]:
            (self.base_path / subdir).mkdir(parents=True, exist_ok=True)

    async def upload_image(self, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix or ".png"
        key = f"{uuid.uuid4()}{ext}"
        path = self.base_path / "uploads" / key

        async with aiofiles.open(path, "wb") as f:
            await f.write(content)

        return f"/storage/uploads/{key}"

    async def upload_video(self, content: bytes, job_id: str) -> str:
        key = f"{job_id}.mp4"
        path = self.base_path / "videos" / key

        async with aiofiles.open(path, "wb") as f:
            await f.write(content)

        return f"/storage/videos/{key}"

    async def save_video_from_path(self, source_path: str, job_id: str) -> str:
        key = f"{job_id}.mp4"
        dest = self.base_path / "videos" / key

        async with aiofiles.open(source_path, "rb") as src:
            content = await src.read()

        async with aiofiles.open(dest, "wb") as dst:
            await dst.write(content)

        return f"/storage/videos/{key}"

    async def save_thumbnail(self, content: bytes, job_id: str) -> str:
        key = f"{job_id}.jpg"
        path = self.base_path / "thumbnails" / key

        async with aiofiles.open(path, "wb") as f:
            await f.write(content)

        return f"/storage/thumbnails/{key}"

    async def delete_file(self, file_path: str):
        if file_path.startswith("/storage/"):
            full_path = self.base_path / file_path.replace("/storage/", "")
            if full_path.exists():
                os.remove(full_path)

    def get_full_path(self, relative_path: str) -> str:
        if relative_path.startswith("/storage/"):
            return str(self.base_path / relative_path.replace("/storage/", ""))
        return relative_path


storage_service = StorageService()
