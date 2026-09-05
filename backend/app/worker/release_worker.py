import asyncio
import logging
from datetime import datetime, timezone
import uuid
from typing import Optional

from sqlalchemy import select

from app.core.config import get_settings
from app.database.session import async_session_factory
from app.models.release_schedule import ReleaseSchedule, ReleaseStatus
from app.models.user import User
from app.core.dependencies import get_crypto_key_provider
from app.services.release_service import ReleaseService

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("release_worker")

async def get_system_user_id(session_factory=async_session_factory) -> Optional[uuid.UUID]:
    """Retrieve the system user ID for audit logging purposes."""
    async with session_factory() as session:
        stmt = select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user.id if user else None

async def process_due_releases(
    system_user_id: uuid.UUID,
    session_factory=async_session_factory,
) -> None:
    """Find and execute due releases."""
    logger.info("[RELEASE WORKER] Checking for due releases")
    
    # We must use a fresh session to get the due releases
    async with session_factory() as session:
        stmt = select(ReleaseSchedule).where(
            ReleaseSchedule.status == ReleaseStatus.SCHEDULED,
            ReleaseSchedule.release_at <= datetime.now(timezone.utc)
        )
        result = await session.execute(stmt)
        due_schedules = list(result.scalars().all())
    
    if not due_schedules:
        return
        
    logger.info(f"[RELEASE WORKER] Found {len(due_schedules)} due release(s)")
    
    crypto_provider = get_crypto_key_provider()
    
    for schedule in due_schedules:
        logger.info(f"[RELEASE WORKER] Executing release for paper {schedule.question_paper_id}")
        
        # Each schedule execution must run in its own fresh session and transaction
        async with session_factory() as execution_session:
            try:
                # Re-fetch schedule with row-level lock (FOR UPDATE) to prevent race conditions
                # between multiple worker instances.
                lock_stmt = (
                    select(ReleaseSchedule)
                    .where(
                        ReleaseSchedule.id == schedule.id,
                        ReleaseSchedule.status == ReleaseStatus.SCHEDULED,
                    )
                    .with_for_update()
                )
                
                locked_result = await execution_session.execute(lock_stmt)
                locked_schedule = locked_result.scalar_one_or_none()
                
                if not locked_schedule:
                    logger.info(f"[RELEASE WORKER] Schedule {schedule.id} already processed or locked. Skipping.")
                    continue
                
                service = ReleaseService(execution_session, crypto_provider)
                
                # Execute release
                await service.execute_release(
                    paper_id=locked_schedule.question_paper_id,
                    user_id=system_user_id,
                    ip_address=None
                )
                
                await execution_session.commit()
                logger.info(f"[RELEASE WORKER] Release successful for paper {locked_schedule.question_paper_id}")
                
            except Exception as e:
                await execution_session.rollback()
                logger.error(f"[RELEASE WORKER] Release failed for paper {schedule.question_paper_id}: {str(e)}")

async def run_worker_loop(interval_seconds: int = 60, run_once: bool = False):
    """Run the release worker loop."""
    logger.info("[RELEASE WORKER] Starting automatic release worker")
    
    system_user_id = await get_system_user_id()
    if not system_user_id:
        logger.error("[RELEASE WORKER] Could not find system user. Exiting.")
        return
        
    while True:
        try:
            await process_due_releases(system_user_id)
        except Exception as e:
            logger.error(f"[RELEASE WORKER] Unexpected error in worker loop: {str(e)}")
            
        if run_once:
            break
            
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        asyncio.run(run_worker_loop())
    except KeyboardInterrupt:
        logger.info("[RELEASE WORKER] Stopped by user")
