"""
Seed the database with sample movies, halls and showtimes.
Run: python manage.py seed_movies
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from movies.models import Genre, Movie, Hall, Showtime
import decimal


class Command(BaseCommand):
    help = "Seed sample movies, halls and showtimes"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding movies...")

        # Genres
        action, _   = Genre.objects.get_or_create(name="Action")
        drama, _    = Genre.objects.get_or_create(name="Drama")
        comedy, _   = Genre.objects.get_or_create(name="Comedy")
        scifi, _    = Genre.objects.get_or_create(name="Sci-Fi")

        # Halls
        hall1, _ = Hall.objects.get_or_create(name="Hall A", defaults={"total_seats": 80})
        hall2, _ = Hall.objects.get_or_create(name="Hall B", defaults={"total_seats": 120})

        # Movies
        movies = [
            {"title": "Galactic Wars", "genre": scifi, "duration_minutes": 148,
             "release_date": "2024-01-15", "rating": 8.5},
            {"title": "City of Shadows", "genre": action, "duration_minutes": 120,
             "release_date": "2024-02-20", "rating": 7.8},
            {"title": "Last Summer", "genre": drama, "duration_minutes": 105,
             "release_date": "2024-03-10", "rating": 8.1},
            {"title": "The Big Laugh", "genre": comedy, "duration_minutes": 95,
             "release_date": "2024-04-05", "rating": 7.2},
        ]

        created_movies = []
        for m in movies:
            obj, created = Movie.objects.get_or_create(
                title=m["title"],
                defaults={**m, "description": f"A great {m['genre'].name} film."}
            )
            created_movies.append(obj)
            if created:
                self.stdout.write(f"  Created movie: {obj.title}")

        # Showtimes — starting from tomorrow
        now = timezone.now()
        for i, movie in enumerate(created_movies):
            hall = hall1 if i % 2 == 0 else hall2
            start = now + timedelta(days=i + 1, hours=2)
            end = start + timedelta(minutes=movie.duration_minutes)
            showtime, created = Showtime.objects.get_or_create(
                movie=movie,
                hall=hall,
                start_time=start,
                defaults={"end_time": end, "price": decimal.Decimal("12.50")}
            )
            if created:
                # Auto-create seats
                from movies.views import _create_seats_for_showtime
                _create_seats_for_showtime(showtime)
                self.stdout.write(f"  Created showtime: {movie.title} @ {start.strftime('%Y-%m-%d %H:%M')}")

        self.stdout.write(self.style.SUCCESS("Done! Sample data created."))
