from .models import Notification
from users.models import CustomUser, Visitor
import logging

logger = logging.getLogger(__name__)


def create_notification(recipient, notification_type, title, message, related_visitor=None, priority='medium'):
    """
    Utility function to create notifications
    """
    try:
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            related_visitor=related_visitor,
            priority=priority
        )
        return notification
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        return None


def notify_overstay_alert(visitor):
    """
    Create overstay alert notification
    """
    message = f"Visitor {visitor.full_name} has overstayed their allocated time."
    return create_notification(
        recipient=visitor.host_member,
        notification_type='overstay',
        title=f'Overstay Alert - {visitor.full_name}',
        message=message,
        related_visitor=visitor,
        priority='high'
    )


def notify_security_breach(user, details):
    """
    Create security breach notification
    """
    commanders = CustomUser.objects.filter(user_type='commander')
    for commander in commanders:
        create_notification(
            recipient=commander,
            notification_type='security_breach',
            title='Security Breach Detected',
            message=f"Security breach detected for user {user.username}. Details: {details}",
            priority='high'
        )


def notify_access_granted(user, action):
    """
    Create access granted notification
    """
    create_notification(
        recipient=user,
        notification_type='access_granted',
        title='Access Granted',
        message=f"Your {action} request has been approved and access has been granted.",
        priority='medium'
    )


def notify_access_denied(user, action, reason):
    """
    Create access denied notification
    """
    create_notification(
        recipient=user,
        notification_type='access_denied',
        title='Access Denied',
        message=f"Your {action} request has been denied. Reason: {reason}",
        priority='medium'
    )
