import json
import redis
from django.conf import settings

# Connect to Redis
_redis = redis.from_url(settings.REDIS_URL)

def publish_event(channel: str, event_type: str, data: dict):
    """
    Publish an event to a Redis channel.

    Any other service (notification-service, etc.)
    can SUBSCRIBE to these channels and react.

    Example:
        publish_event(
            channel="user-events",
            event_type="user.registered",
            data={"user_id": "abc-123", "email": "joe@test.com"}
        )
    """
    message = json.dumps({
        "event": event_type,
        "data": data,
    })
    _redis.publish(channel, message)
    print(f"[Redis] Published → {channel}: {event_type}")


# ── Specific event helpers ─────────────────────────────────────────────────────

def user_registered_event(user):
    """Fire when a new user registers. Notification service listens to send welcome email."""
    publish_event(
        channel="user-events",
        event_type="user.registered",
        data={
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
        },
    )

def user_logged_in_event(user):
    """Fire when a user logs in. Can be used for audit logs, analytics etc."""
    publish_event(
        channel="user-events",
        event_type="user.logged_in",
        data={
            "user_id": str(user.id),
            "email": user.email,
        },
    )

def user_updated_event(user):
    """Fire when user updates their profile."""
    publish_event(
        channel="user-events",
        event_type="user.updated",
        data={
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
        },
    )
