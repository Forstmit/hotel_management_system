"""Слой хранения данных SQLite."""
import sqlite3
from pathlib import Path
from datetime import date
from .models import Room, Guest, Reservation, RoomType, ReservationStatus


class Database:
    def __init__(self, db_path: str = "data/hotel.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self):
        with self.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number INTEGER NOT NULL UNIQUE,
                    room_type TEXT NOT NULL,
                    price_per_night REAL NOT NULL CHECK(price_per_night > 0),
                    capacity INTEGER NOT NULL CHECK(capacity > 0)
                );
                CREATE TABLE IF NOT EXISTS guests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL REFERENCES rooms(id),
                    guest_id INTEGER NOT NULL REFERENCES guests(id),
                    check_in TEXT NOT NULL,
                    check_out TEXT NOT NULL,
                    guests_count INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    accommodation_cost REAL NOT NULL,
                    booking_fee REAL NOT NULL,
                    total_cost REAL NOT NULL
                );
            """)

    def add_room(self, room: Room) -> int:
        with self.connect() as con:
            cur = con.execute(
                "INSERT INTO rooms(number, room_type, price_per_night, capacity) VALUES (?, ?, ?, ?)",
                (room.number, room.room_type.value, room.price_per_night, room.capacity))
            return cur.lastrowid

    def add_guest(self, guest: Guest) -> int:
        with self.connect() as con:
            cur = con.execute("INSERT INTO guests(full_name, phone) VALUES (?, ?)",
                              (guest.full_name, guest.phone))
            return cur.lastrowid

    def get_rooms(self):
        with self.connect() as con:
            rows = con.execute("SELECT * FROM rooms ORDER BY number").fetchall()
        return [Room(r["number"], RoomType(r["room_type"]), r["price_per_night"],
                     r["capacity"], r["id"]) for r in rows]

    def get_room(self, room_id: int):
        with self.connect() as con:
            r = con.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
        if r is None:
            raise ValueError("Номер с таким ID не найден.")
        return Room(r["number"], RoomType(r["room_type"]), r["price_per_night"],
                    r["capacity"], r["id"])

    def get_guest(self, guest_id: int):
        with self.connect() as con:
            r = con.execute("SELECT * FROM guests WHERE id = ?", (guest_id,)).fetchone()
        if r is None:
            raise ValueError("Гость с таким ID не найден.")
        return Guest(r["full_name"], r["phone"], r["id"])

    def add_reservation(self, reservation: Reservation) -> int:
        with self.connect() as con:
            # Пересекающиеся подтверждённые брони одного номера запрещены.
            conflict = con.execute("""
                SELECT COUNT(*) FROM reservations
                WHERE room_id = ? AND status = ?
                  AND date(check_in) < date(?) AND date(check_out) > date(?)
            """, (reservation.room.id, ReservationStatus.CONFIRMED.value,
                  reservation.check_out.isoformat(), reservation.check_in.isoformat())).fetchone()[0]
            if conflict:
                raise ValueError("Этот номер уже забронирован на указанные даты.")
            cur = con.execute("""
                INSERT INTO reservations(
                    room_id, guest_id, check_in, check_out, guests_count, status,
                    accommodation_cost, booking_fee, total_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (reservation.room.id, reservation.guest.id,
                  reservation.check_in.isoformat(), reservation.check_out.isoformat(),
                  reservation.guests_count, reservation.status.value,
                  reservation.accommodation_cost, reservation.BOOKING_FEE,
                  reservation.total_cost))
            return cur.lastrowid

    def get_reservations(self):
        with self.connect() as con:
            rows = con.execute("""
                SELECT b.*, r.number, r.room_type, r.price_per_night, r.capacity,
                       g.full_name, g.phone
                FROM reservations b
                JOIN rooms r ON r.id = b.room_id
                JOIN guests g ON g.id = b.guest_id
                ORDER BY b.id DESC
            """).fetchall()
        result = []
        for row in rows:
            room = Room(row["number"], RoomType(row["room_type"]),
                        row["price_per_night"], row["capacity"], row["room_id"])
            guest = Guest(row["full_name"], row["phone"], row["guest_id"])
            result.append(Reservation(
                room, guest, date.fromisoformat(row["check_in"]),
                date.fromisoformat(row["check_out"]), row["guests_count"],
                row["id"], ReservationStatus(row["status"])))
        return result

    def statistics(self):
        with self.connect() as con:
            rooms = con.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
            guests = con.execute("SELECT COUNT(*) FROM guests").fetchone()[0]
            bookings = con.execute("SELECT COUNT(*) FROM reservations WHERE status = ?",
                                   (ReservationStatus.CONFIRMED.value,)).fetchone()[0]
            revenue = con.execute("SELECT COALESCE(SUM(total_cost), 0) FROM reservations WHERE status = ?",
                                  (ReservationStatus.CONFIRMED.value,)).fetchone()[0]
        return {"rooms": rooms, "guests": guests, "bookings": bookings, "revenue": revenue}
