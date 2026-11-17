"""Модели предметной области и ООП-компоненты приложения."""
from abc import ABC, abstractmethod
from datetime import date
from enum import Enum


class RoomType(Enum):
    STANDARD = "Стандарт"
    COMFORT = "Комфорт"
    LUX = "Люкс"


class ReservationStatus(Enum):
    CONFIRMED = "Подтверждено"
    CANCELLED = "Отменено"


class Entity(ABC):
    """Абстрактная базовая сущность с общим идентификатором."""

    def __init__(self, entity_id: int | None = None):
        self._id = entity_id

    @property
    def id(self):
        """Managed-атрибут: идентификатор доступен только для чтения."""
        return self._id

    @abstractmethod
    def validate(self):
        """Проверка корректности состояния объекта."""

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id})"

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id!r})"

    def __eq__(self, other):
        return type(self) is type(other) and self.id == other.id


class Room(Entity):
    """Номер отеля."""

    def __init__(self, number: int, room_type: RoomType, price_per_night: float,
                 capacity: int, entity_id: int | None = None):
        super().__init__(entity_id)
        self.number = number
        self.room_type = room_type
        self.price_per_night = price_per_night
        self.capacity = capacity
        self.validate()

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Номер комнаты должен быть положительным целым числом.")
        self._number = value

    @property
    def price_per_night(self):
        return self._price_per_night

    @price_per_night.setter
    def price_per_night(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError("Цена за ночь должна быть больше нуля.")
        self._price_per_night = value

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Вместимость должна быть положительным целым числом.")
        self._capacity = value

    def validate(self):
        if not isinstance(self.room_type, RoomType):
            raise ValueError("Некорректная категория номера.")
        if self.capacity < 1 or self.price_per_night <= 0:
            raise ValueError("Некорректные параметры номера.")

    def __str__(self):
        return (f"Номер {self.number} | {self.room_type.value} | "
                f"{self.price_per_night:.2f} руб./ночь | мест: {self.capacity}")

    def __repr__(self):
        return (f"Room(number={self.number!r}, room_type={self.room_type!r}, "
                f"price_per_night={self.price_per_night!r}, capacity={self.capacity!r})")

    def __lt__(self, other):
        if not isinstance(other, Room):
            return NotImplemented
        return self.number < other.number


class Guest(Entity):
    """Гость отеля."""

    def __init__(self, full_name: str, phone: str, entity_id: int | None = None):
        super().__init__(entity_id)
        self.full_name = full_name
        self.phone = phone
        self.validate()

    @property
    def full_name(self):
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        value = str(value).strip()
        if len(value) < 2:
            raise ValueError("Укажите полное имя гостя.")
        self._full_name = value

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value):
        value = str(value).strip()
        if len(value) < 5:
            raise ValueError("Укажите корректный номер телефона.")
        self._phone = value

    def validate(self):
        if not self.full_name or not self.phone:
            raise ValueError("Имя и телефон гостя обязательны.")

    def __str__(self):
        return f"Гость: {self.full_name} | телефон: {self.phone}"

    def __repr__(self):
        return f"Guest(full_name={self.full_name!r}, phone={self.phone!r}, id={self.id!r})"

    def __len__(self):
        return len(self.full_name)


class Reservation(Entity):
    """Бронирование номера. Сумма включает проживание и фиксированный сбор."""

    BOOKING_FEE = 500.0

    def __init__(self, room: Room, guest: Guest, check_in: date, check_out: date,
                 guests_count: int, entity_id: int | None = None,
                 status: ReservationStatus = ReservationStatus.CONFIRMED):
        super().__init__(entity_id)
        self.room = room
        self.guest = guest
        self.check_in = check_in
        self.check_out = check_out
        self.guests_count = guests_count
        self.status = status
        self.validate()

    @property
    def guests_count(self):
        return self._guests_count

    @guests_count.setter
    def guests_count(self, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Количество гостей должно быть положительным целым числом.")
        self._guests_count = value

    @property
    def nights(self):
        return (self.check_out - self.check_in).days

    @property
    def accommodation_cost(self):
        return self.nights * self.room.price_per_night

    @property
    def total_cost(self):
        return self.accommodation_cost + self.BOOKING_FEE

    def validate(self):
        if not isinstance(self.room, Room) or not isinstance(self.guest, Guest):
            raise ValueError("Для бронирования нужны корректные номер и гость.")
        if self.check_out <= self.check_in:
            raise ValueError("Дата выезда должна быть позже даты заезда.")
        if self.guests_count > self.room.capacity:
            raise ValueError("Количество гостей превышает вместимость номера.")
        if not isinstance(self.status, ReservationStatus):
            raise ValueError("Некорректный статус бронирования.")

    def __str__(self):
        return (f"Бронь #{self.id or 'новая'}: {self.guest.full_name}, номер "
                f"{self.room.number}, {self.nights} ноч., итого {self.total_cost:.2f} руб.")

    def __repr__(self):
        return (f"Reservation(room={self.room!r}, guest={self.guest!r}, "
                f"check_in={self.check_in!r}, check_out={self.check_out!r}, "
                f"guests_count={self.guests_count!r}, id={self.id!r})")

    def __bool__(self):
        return self.status is ReservationStatus.CONFIRMED
