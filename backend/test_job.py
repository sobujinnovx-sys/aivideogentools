import asyncio
from app.core.database import async_session
from app.models.job import Job, JobStatus
from app.models.user import User
from app.models.credit import CreditTransaction, TransactionType
from sqlalchemy import select

async def test():
    async with async_session() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            print("No user found")
            return
        print(f"User: {user.email}, credits: {user.credits}")

        if user.credits < 10:
            print("Not enough credits")
            return

        user.credits -= 10
        job = Job(
            user_id=user.id,
            prompt="A cartoon cat dancing in a garden with flowers",
            duration=5,
            aspect_ratio="16:9",
            model="wan2.1",
            credits_used=10,
            status=JobStatus.QUEUED,
        )
        db.add(job)
        db.add(CreditTransaction(user_id=user.id, amount=-10, type=TransactionType.DEBIT, description="Test video 5s"))
        await db.commit()
        await db.refresh(job)
        print(f"Created job: {job.id}")

        from app.services.queue import queue_service
        rq_job = queue_service.enqueue_job(job.id)
        if rq_job:
            print(f"Enqueued RQ job: {rq_job.id}")
        else:
            print("FAILED to enqueue")

asyncio.run(test())
