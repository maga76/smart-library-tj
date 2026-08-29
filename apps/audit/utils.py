import logging

from .models import AuditLog

logger = logging.getLogger(__name__)


def log_audit(user, action, object_type, object_id='', description=''):
    """
    Utility function to log significant system actions into AuditLog.
    Safe against None users or logging failures.
    """
    try:
        user_obj = user if (user and getattr(user, 'is_authenticated', False)) else None
        AuditLog.objects.create(
            user=user_obj,
            action=action,
            object_type=object_type,
            object_id=str(object_id) if object_id else '',
            description=description
        )
    except Exception:
        # Prevent audit log failure from crashing business logic, but don't lose visibility
        logger.exception('Failed to write audit log entry: action=%s object_type=%s object_id=%s', action, object_type, object_id)
