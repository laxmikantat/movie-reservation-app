import json
import redis
from django.conf import settings

_redis = redis.from_url(settings.REDIS_URL)


def publish_event(channel: str, event_type: str, data: dict):
    message = json.dumps({"event": event_type, "data": data})
    _redis.publish(channel, message)
    print(f"[Redis] Published → {channel}: {event_type}")


def showtime_created_event(showtime):
    publish_event(
        channel="movie-events",
        event_type="showtime.created",
        data={
            "showtime_id": str(showtime.id),
            "movie_id": str(showtime.movie.id),
            "movie_title": showtime.movie.title,
            "start_time": str(showtime.start_time),
            "price": str(showtime.price),
        },
    )


def seat_booked_event(seat, user_id):
    """Fire when reservation-service books a seat via internal API"""
    publish_event(
        channel="movie-events",
        event_type="seat.booked",
        data={
            "seat_id": str(seat.id),
            "showtime_id": str(seat.showtime.id),
            "movie_title": seat.showtime.movie.title,
            "row": seat.row,
            "number": seat.number,
            "user_id": str(user_id),
        },
    )


def seat_released_event(seat):
    publish_event(
        channel="movie-events",
        event_type="seat.released",
        data={
            "seat_id": str(seat.id),
            "showtime_id": str(seat.showtime.id),
        },
    )
