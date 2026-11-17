from datetime import date
from hotel.database import Database
from hotel.models import Room, Guest, Reservation, RoomType


def test_database_roundtrip(tmp_path):
    db = Database(str(tmp_path / "hotel.db"))
    room_id = db.add_room(Room(201, RoomType.COMFORT, 3200, 3))
    guest_id = db.add_guest(Guest("Анна Петрова", "+79991112233"))
    room = db.get_room(room_id)
    guest = db.get_guest(guest_id)
    booking = Reservation(room, guest, date(2026, 12, 10), date(2026, 12, 12), 2)
    db.add_reservation(booking)
    assert len(db.get_reservations()) == 1
    assert db.statistics()["bookings"] == 1
