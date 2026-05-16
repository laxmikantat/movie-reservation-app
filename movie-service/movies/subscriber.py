"""
Listens for events from other services (user-service, reservation-service).
Run as: python movies/subscriber.py
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
pubsub.subscribe("user-events", "reservation-events")

print("[Movie Subscriber] Listening on: user-events, reservation-events")

for message in pubsub.listen():
    if message["type"] != "message":
        continue

    try:
        payload = json.loads(message["data"])
        event = payload.get("event")
        data = payload.get("data", {})

        print(f"[Movie Subscriber] {event} → {data}")

        if event == "reservation.cancelled":
            # When a reservation is cancelled, unbook the seat
            from movies.models import Seat
            seat_id = data.get("seat_id")
            if seat_id:
                try:
                    seat = Seat.objects.get(id=seat_id)
                    seat.is_booked = False
                    seat.booked_by_user_id = None
                    seat.save()
                    print(f"  → Seat {seat_id} released due to cancellation")
                except Seat.DoesNotExist:
                    print(f"  → Seat {seat_id} not found")

    except Exception as e:
        print(f"[Movie Subscriber] Error: {e}")
