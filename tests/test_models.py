import pytest
from datetime import date
from hotel.models import Room, Guest, Reservation, RoomType


def sample_objects():
    room = Room(101, RoomType.STANDARD, 2500, 2, 1)
    guest = Guest("Иван Иванов", "+79990000000", 1)
    return room, guest


def test_room_managed_attributes():
    room, _ = sample_objects()
    assert room.price_per_night == 2500
    with pytest.raises(ValueError):
        room.capacity = 0


def test_guest_validation():
    with pytest.raises(ValueError):
        Guest("", "12345")


def test_reservation_calculation():
    room, guest = sample_objects()
    booking = Reservation(room, guest, date(2026, 12, 1), date(2026, 12, 4), 2)
    assert booking.nights == 3
    assert booking.accommodation_cost == 7500
    assert booking.total_cost == 8000


def test_reservation_capacity_validation():
    room, guest = sample_objects()
    with pytest.raises(ValueError):
        Reservation(room, guest, date(2026, 12, 1), date(2026, 12, 2), 3)


def test_dunder_methods():
    room, guest = sample_objects()
    assert "101" in str(room)
    assert "Room(" in repr(room)
    assert len(guest) == len("Иван Иванов")
