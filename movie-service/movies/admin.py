from django.contrib import admin
from .models import Genre, Movie, Hall, Showtime, Seat

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "genre", "duration_minutes", "release_date", "rating", "is_active"]
    list_filter = ["genre", "is_active", "language"]
    search_fields = ["title"]

@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ["movie", "hall", "start_time", "price", "available_seats", "is_active"]
    list_filter = ["is_active", "hall"]

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["showtime", "row", "number", "seat_type", "is_booked"]
    list_filter = ["is_booked", "seat_type"]

admin.site.register(Genre)
admin.site.register(Hall)
