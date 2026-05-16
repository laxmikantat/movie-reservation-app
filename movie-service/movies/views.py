from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Genre, Movie, Hall, Showtime, Seat
from .serializers import (
    GenreSerializer, MovieSerializer, MovieListSerializer,
    HallSerializer, ShowtimeSerializer, ShowtimeListSerializer,
    SeatSerializer, SeatBookSerializer,
)
from .events import showtime_created_event, seat_booked_event, seat_released_event


# ── Genre ──────────────────────────────────────────────────────────────────────

class GenreListView(generics.ListCreateAPIView):
    """GET /api/movies/genres/ — list all genres (public)"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


# ── Movies ─────────────────────────────────────────────────────────────────────

class MovieListView(generics.ListCreateAPIView):
    """
    GET  /api/movies/          → list all active movies (public)
    POST /api/movies/          → create movie (admin only)
    Supports ?genre=1 and ?search=title filtering
    """
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description", "genre__name"]

    def get_queryset(self):
        qs = Movie.objects.filter(is_active=True).select_related("genre")
        genre = self.request.query_params.get("genre")
        if genre:
            qs = qs.filter(genre__id=genre)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return MovieListSerializer
        return MovieSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [AllowAny()]


class MovieDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/movies/<id>/"""
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]


# ── Showtimes ──────────────────────────────────────────────────────────────────

class ShowtimeListView(generics.ListCreateAPIView):
    """
    GET  /api/movies/showtimes/          → all upcoming showtimes (public)
    GET  /api/movies/showtimes/?movie=id → filter by movie
    POST /api/movies/showtimes/          → create showtime (admin only)
    """
    filter_backends = [filters.SearchFilter]
    search_fields = ["movie__title", "hall__name"]

    def get_queryset(self):
        from django.utils import timezone
        qs = Showtime.objects.filter(
            is_active=True,
            start_time__gte=timezone.now()
        ).select_related("movie", "hall")

        movie_id = self.request.query_params.get("movie")
        if movie_id:
            qs = qs.filter(movie__id=movie_id)
        return qs

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ShowtimeListSerializer
        return ShowtimeSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [AllowAny()]

    def perform_create(self, serializer):
        showtime = serializer.save()
        # Auto-create seats for this showtime
        _create_seats_for_showtime(showtime)
        # Publish event to Redis
        showtime_created_event(showtime)


class ShowtimeDetailView(generics.RetrieveAPIView):
    """GET /api/movies/showtimes/<id>/ — includes full seat map"""
    queryset = Showtime.objects.all()
    serializer_class = ShowtimeSerializer
    permission_classes = [AllowAny]


# ── Seats ──────────────────────────────────────────────────────────────────────

class SeatListView(generics.ListAPIView):
    """GET /api/movies/showtimes/<showtime_id>/seats/ — see all seats"""
    serializer_class = SeatSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        showtime_id = self.kwargs["showtime_id"]
        return Seat.objects.filter(showtime__id=showtime_id).order_by("row", "number")


class InternalSeatBookView(APIView):
    """
    POST /api/movies/seats/book/

    INTERNAL USE ONLY — called by reservation-service to
    book or unbook a seat atomically.

    Protected by X-Internal-Secret header.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Verify internal secret
        secret = request.headers.get("X-Internal-Secret")
        from django.conf import settings
        if secret != settings.INTERNAL_SECRET:
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        serializer = SeatBookSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        seat_id = serializer.validated_data["seat_id"]
        user_id = serializer.validated_data["user_id"]
        action = serializer.validated_data["action"]

        try:
            with transaction.atomic():
                # Lock the row to prevent double-booking
                seat = Seat.objects.select_for_update().get(id=seat_id)

                if action == "book":
                    if seat.is_booked:
                        return Response(
                            {"error": "Seat is already booked."},
                            status=status.HTTP_409_CONFLICT,
                        )
                    seat.is_booked = True
                    seat.booked_by_user_id = user_id
                    seat.save()
                    seat_booked_event(seat, user_id)
                    return Response({
                        "message": "Seat booked successfully.",
                        "seat": SeatSerializer(seat).data,
                    })

                elif action == "unbook":
                    seat.is_booked = False
                    seat.booked_by_user_id = None
                    seat.save()
                    seat_released_event(seat)
                    return Response({"message": "Seat released successfully."})

        except Seat.DoesNotExist:
            return Response({"error": "Seat not found."}, status=status.HTTP_404_NOT_FOUND)


# ── Halls ──────────────────────────────────────────────────────────────────────

class HallListView(generics.ListCreateAPIView):
    queryset = Hall.objects.all()
    serializer_class = HallSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [AllowAny()]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _create_seats_for_showtime(showtime):
    """Auto-generate seats when a showtime is created."""
    rows = ["A", "B", "C", "D", "E", "F", "G", "H"]
    seats_per_row = showtime.hall.total_seats // len(rows)
    seats = []
    for row in rows:
        for num in range(1, seats_per_row + 1):
            seat_type = "vip" if row in ["A"] else "premium" if row in ["B", "C"] else "standard"
            seats.append(Seat(
                showtime=showtime,
                row=row,
                number=num,
                seat_type=seat_type,
            ))
    Seat.objects.bulk_create(seats)
    print(f"[Movie Service] Created {len(seats)} seats for showtime {showtime.id}")
