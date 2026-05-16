from django.urls import path
from .views import (
    GenreListView,
    MovieListView,
    MovieDetailView,
    ShowtimeListView,
    ShowtimeDetailView,
    SeatListView,
    HallListView,
    InternalSeatBookView,
)

urlpatterns = [
    # Public endpoints
    path("",                                    MovieListView.as_view(),       name="movie-list"),
    path("<uuid:pk>/",                          MovieDetailView.as_view(),     name="movie-detail"),
    path("genres/",                             GenreListView.as_view(),       name="genre-list"),
    path("halls/",                              HallListView.as_view(),        name="hall-list"),
    path("showtimes/",                          ShowtimeListView.as_view(),    name="showtime-list"),
    path("showtimes/<uuid:pk>/",               ShowtimeDetailView.as_view(),  name="showtime-detail"),
    path("showtimes/<uuid:showtime_id>/seats/", SeatListView.as_view(),        name="seat-list"),

    # Internal endpoints (called by reservation-service only)
    path("seats/book/",                         InternalSeatBookView.as_view(), name="seat-book"),
]
