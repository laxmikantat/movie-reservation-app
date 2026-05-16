from rest_framework import serializers
from .models import Genre, Movie, Hall, Showtime, Seat


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class MovieSerializer(serializers.ModelSerializer):
    genre_name = serializers.CharField(source="genre.name", read_only=True)
    showtimes_count = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id", "title", "description", "genre", "genre_name",
            "duration_minutes", "release_date", "language",
            "rating", "poster", "is_active", "showtimes_count", "created_at",
        ]

    def get_showtimes_count(self, obj):
        return obj.showtimes.filter(is_active=True).count()


class MovieListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    genre_name = serializers.CharField(source="genre.name", read_only=True)

    class Meta:
        model = Movie
        fields = ["id", "title", "genre_name", "duration_minutes",
                  "release_date", "language", "rating", "poster", "is_active"]


class HallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hall
        fields = ["id", "name", "total_seats"]


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "row", "number", "seat_type", "is_booked"]


class ShowtimeSerializer(serializers.ModelSerializer):
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    hall_name = serializers.CharField(source="hall.name", read_only=True)
    available_seats = serializers.IntegerField(read_only=True)
    seats = SeatSerializer(many=True, read_only=True)

    class Meta:
        model = Showtime
        fields = [
            "id", "movie", "movie_title", "hall", "hall_name",
            "start_time", "end_time", "price",
            "available_seats", "seats", "is_active",
        ]


class ShowtimeListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views — no seat details"""
    movie_title = serializers.CharField(source="movie.title", read_only=True)
    hall_name = serializers.CharField(source="hall.name", read_only=True)
    available_seats = serializers.IntegerField(read_only=True)

    class Meta:
        model = Showtime
        fields = [
            "id", "movie", "movie_title", "hall", "hall_name",
            "start_time", "end_time", "price", "available_seats", "is_active",
        ]


class SeatBookSerializer(serializers.Serializer):
    """Used by reservation-service to book/unbook a seat"""
    seat_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=["book", "unbook"])
