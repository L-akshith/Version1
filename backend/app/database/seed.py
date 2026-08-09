"""
ExamShield - Database Seeding Utility

Seeds default permissions, roles, and the first system administrator (superuser).
Idempotent and safe to run multiple times.
"""

import asyncio
import logging
import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.permissions import DEFAULT_PERMISSIONS, DEFAULT_ROLES
from app.database.session import async_session_factory
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.utils.password import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("examshield.seed")

settings = get_settings()


async def seed_permissions(session: AsyncSession) -> List[Permission]:
    """Seed all default permissions. Returns list of all permissions."""
    logger.info("Seeding permissions...")
    seeded_perms: List[Permission] = []

    for perm_data in DEFAULT_PERMISSIONS:
        name = perm_data["name"]
        stmt = select(Permission).where(Permission.name == name)
        res = await session.execute(stmt)
        perm = res.scalar_one_or_none()

        if not perm:
            perm = Permission(
                name=name,
                description=perm_data["description"],
                resource=perm_data["resource"].value,
                action=perm_data["action"].value,
            )
            session.add(perm)
            logger.info("Created permission: %s", name)
        else:
            # Update description if it changed
            perm.description = perm_data["description"]
            perm.resource = perm_data["resource"].value
            perm.action = perm_data["action"].value

        seeded_perms.append(perm)

    await session.flush()
    return seeded_perms


async def seed_roles(session: AsyncSession, permissions: List[Permission]) -> None:
    """Seed default roles and assign respective permissions."""
    logger.info("Seeding roles and mapping permissions...")
    perm_map = {p.name: p for p in permissions}

    for role_name, role_data in DEFAULT_ROLES.items():
        stmt = select(Role).where(Role.name == role_name)
        res = await session.execute(stmt)
        role = res.scalar_one_or_none()

        if not role:
            role = Role(
                name=role_name,
                description=role_data["description"],
            )
            session.add(role)
            logger.info("Created role: %s", role_name)
        else:
            role.description = role_data["description"]

        # Re-fetch permissions for this role and update list
        role_perms = []
        for p_name in role_data["permissions"]:
            if p_name in perm_map:
                role_perms.append(perm_map[p_name])

        role.permissions = role_perms

    await session.flush()


async def seed_superuser(session: AsyncSession) -> None:
    """Seed the initial system administrator account."""
    logger.info("Seeding default superuser...")
    email = settings.FIRST_SUPERUSER_EMAIL

    stmt = select(User).where(User.email == email)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    # Get admin role
    admin_role_stmt = select(Role).where(Role.name == "Admin")
    admin_role_res = await session.execute(admin_role_stmt)
    admin_role = admin_role_res.scalar_one_or_none()

    if not admin_role:
        logger.error("Admin role not found. Ensure roles are seeded before superuser.")
        return

    if not user:
        hashed = hash_password(settings.FIRST_SUPERUSER_PASSWORD)
        user = User(
            email=email,
            hashed_password=hashed,
            full_name=settings.FIRST_SUPERUSER_FULL_NAME,
            is_active=True,
            is_superuser=True,
            role_id=admin_role.id,
        )
        session.add(user)
        logger.info("Created superuser: %s", email)
    else:
        # Update existing superuser details if necessary
        user.is_superuser = True
        user.role_id = admin_role.id
        logger.info("Superuser %s already exists. Ensured admin privileges.", email)

    await session.flush()


async def run_seed() -> None:
    """Run complete database seeding."""
    async with async_session_factory() as session:
        try:
            perms = await seed_permissions(session)
            await seed_roles(session, perms)
            await seed_superuser(session)
            await session.commit()
            logger.info("Database seeding completed successfully.")
        except Exception as e:
            logger.exception("Error occurred during database seeding")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
