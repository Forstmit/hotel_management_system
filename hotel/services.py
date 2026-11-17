"""Прикладная логика, экспорт отчёта и консольный интерфейс."""
from datetime import date
from docx import Document
from .models import Room, Guest, Reservation, RoomType


class HotelService:
    def __init__(self, database):
        self.db = database

    def create_room(self, number, room_type, price, capacity):
        room = Room(int(number), RoomType(room_type), float(price), int(capacity))
        room_id = self.db.add_room(room)
        return self.db.get_room(room_id)

    def create_guest(self, full_name, phone):
        guest = Guest(full_name, phone)
        guest_id = self.db.add_guest(guest)
        return self.db.get_guest(guest_id)

    def create_reservation(self, room_id, guest_id, check_in, check_out, guests_count):
        room = self.db.get_room(int(room_id))
        guest = self.db.get_guest(int(guest_id))
        reservation = Reservation(room, guest, date.fromisoformat(check_in),
                                  date.fromisoformat(check_out), int(guests_count))
        reservation_id = self.db.add_reservation(reservation)
        return Reservation(room, guest, reservation.check_in, reservation.check_out,
                           reservation.guests_count, reservation_id)

    def export_report(self, filename="hotel_report.docx"):
        doc = Document()
        doc.add_heading("Отчёт по системе управления отелем", 0)
        stats = self.db.statistics()
        doc.add_heading("Статистика", level=1)
        for label, key in [("Количество номеров", "rooms"), ("Количество гостей", "guests"),
                           ("Подтверждённые бронирования", "bookings")]:
            doc.add_paragraph(f"{label}: {stats[key]}")
        doc.add_paragraph(f"Сумма бронирований: {stats['revenue']:.2f} руб.")
        doc.add_heading("Список бронирований", level=1)
        table = doc.add_table(rows=1, cols=6)
        table.style = "Table Grid"
        headers = ["ID", "Гость", "Номер", "Заезд", "Выезд", "Итого, руб."]
        for cell, value in zip(table.rows[0].cells, headers):
            cell.text = value
        for item in self.db.get_reservations():
            cells = table.add_row().cells
            values = [str(item.id), item.guest.full_name, str(item.room.number),
                      item.check_in.isoformat(), item.check_out.isoformat(),
                      f"{item.total_cost:.2f}"]
            for cell, value in zip(cells, values):
                cell.text = value
        doc.save(filename)
        return filename


def run_console():
    from .database import Database
    db = Database()
    service = HotelService(db)
    while True:
        print("\n" + "=" * 46)
        print("       HOTEL MANAGEMENT SYSTEM")
        print("=" * 46)
        print("1. Добавить номер")
        print("2. Просмотреть номера")
        print("3. Зарегистрировать гостя")
        print("4. Создать бронирование")
        print("5. Просмотреть бронирования")
        print("6. Статистика отеля")
        print("7. Экспортировать отчёт DOCX")
        print("0. Выход")
        choice = input("Выберите действие: ").strip()
        try:
            if choice == "1":
                print("Типы: " + ", ".join(x.value for x in RoomType))
                kind = input("Тип номера: ").strip()
                service.create_room(input("Номер комнаты: "), kind,
                                    input("Цена за ночь (руб.): "),
                                    input("Количество мест: "))
                print("Номер успешно добавлен.")
            elif choice == "2":
                rooms = db.get_rooms()
                print("\n".join(f"ID {r.id}: {r}" for r in rooms) or "Номеров пока нет.")
            elif choice == "3":
                guest = service.create_guest(input("ФИО гостя: "), input("Телефон: "))
                print(f"Гость добавлен. ID: {guest.id}")
            elif choice == "4":
                print("Доступные номера:")
                for room in db.get_rooms():
                    print(f"ID {room.id}: {room}")
                guest_id = input("ID гостя: ")
                room_id = input("ID номера: ")
                start = input("Дата заезда (ГГГГ-ММ-ДД): ")
                end = input("Дата выезда (ГГГГ-ММ-ДД): ")
                count = input("Количество гостей: ")
                booking = service.create_reservation(room_id, guest_id, start, end, count)
                print("Бронирование создано:")
                print(booking)
            elif choice == "5":
                items = db.get_reservations()
                print("\n".join(map(str, items)) or "Бронирований пока нет.")
            elif choice == "6":
                s = db.statistics()
                print(f"Номеров: {s['rooms']} | Гостей: {s['guests']} | "
                      f"Броней: {s['bookings']} | Выручка: {s['revenue']:.2f} руб.")
            elif choice == "7":
                path = service.export_report()
                print(f"Отчёт сохранён: {path}")
            elif choice == "0":
                print("До свидания!")
                break
            else:
                print("Неизвестный пункт меню.")
        except (ValueError, TypeError) as error:
            print(f"Ошибка: {error}")
        except Exception as error:
            print(f"Не удалось выполнить операцию: {error}")
