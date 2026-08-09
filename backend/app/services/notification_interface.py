"""
ExamShield - Notification Service Interface

Abstract interface for generating notifications to users.
Currently serves as a placeholder for future implementation
(e.g., Email, SMS, WebSockets) to avoid modifying business logic later.
"""

import abc
import logging
import uuid

logger = logging.getLogger("examshield.notification")


class NotificationService(abc.ABC):
    """Abstract interface for notifying users of events."""

    @abc.abstractmethod
    async def notify_user(self, user_id: uuid.UUID, title: str, message: str) -> None:
        """Send a notification to a specific user."""


class PlaceholderNotificationService(NotificationService):
    """
    Placeholder implementation that simply logs the notification.
    Meets the requirement to NOT implement actual Email or SMS yet.
    """

    async def notify_user(self, user_id: uuid.UUID, title: str, message: str) -> None:
        """Log the notification instead of sending it."""
        logger.info(f"NOTIFICATION to {user_id} | {title}: {message}")
