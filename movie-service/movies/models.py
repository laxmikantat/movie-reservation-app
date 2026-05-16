import uuid
from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name="movies")
    duration_minutes = models.PositiveIntegerField(help_text="Movie length in minutes")
    release_date = models.DateField()
    language = models.CharField(max_length=50, default="English")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    poster = models.ImageField(upload_to="posters/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Hall(models.Model):
    """Cinema hall / screen"""
    name = models.CharField(max_length=100)
    total_seats = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Showtime(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="showtimes")
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name="showtimes")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.movie.title} @ {self.start_time}"

    @property
    def available_seats(self):
        return self.seats.filter(is_booked=False).count()


class Seat(models.Model):
    """Individual seat in a showtime"""
    SEAT_TYPES = [
        ("standard", "Standard"),
        ("premium", "Premium"),
        ("vip", "VIP"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name="seats")
    row = models.CharField(max_length=5)       # e.g. A, B, C
    number = models.PositiveIntegerField()     # e.g. 1, 2, 3
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPES, default="standard")
    is_booked = models.BooleanField(default=False)
    booked_by_user_id = models.UUIDField(null=True, blank=True)  # user_id from user-service

    class Meta:
        unique_together = ["showtime", "row", "number"]
        ordering = ["row", "number"]

    def __str__(self):
        return f"{self.row}{self.number} - {self.showtime}"
