"""
Run this as a separate process:
    python manage.py shell < users/subscriber.py
OR add as a management command.

This listens for events FROM other services.
For example: reservation-service might tell us
"user made a booking" so we can update their profile.
"""
import json
import redis
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings

r = redis.from_url(settings.REDIS_URL)
pubsub = r.pubsub()

# Subscribe to channels from OTHER services
pubsub.subscribe("reservation-events")

print("[Subscriber] Listening for events on: reservation-events")

for message in pubsub.listen():
    if message["type"] != "message":
        continue

    try:
        payload = json.loads(message["data"])
        event = payload.get("event")
        data = payload.get("data", {})

        print(f"[Subscriber] Received: {event} → {data}")

        if event == "reservation.confirmed":
            # Example: update user's booking count or send notification
            user_id = data.get("user_id")
            print(f"  → User {user_id} made a reservation. Could update profile here.")

        elif event == "reservation.cancelled":
            user_id = data.get("user_id")
            print(f"  → User {user_id} cancelled a reservation.")

    except Exception as e:
        print(f"[Subscriber] Error processing message: {e}")
