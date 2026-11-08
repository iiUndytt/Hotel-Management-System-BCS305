# services.py - the actual hotel logic

from datetime import timedelta

from models import HotelError, Reservation, Guest
from models import StandardRoom, DeluxeRoom, Suite


# ---- Factory pattern: builds the right kind of room from a type name ----

class RoomFactory:
    room_types = {"standard": StandardRoom, "deluxe": DeluxeRoom, "suite": Suite}

    @staticmethod
    def create(number, room_type, rate=None):
        room_class = RoomFactory.room_types.get(room_type.lower())
        if room_class is None:
            allowed = ", ".join(c.room_type for c in RoomFactory.room_types.values())
            raise HotelError(f"Unknown room type '{room_type}'. Use one of: {allowed}")
        return room_class(number, rate)


# ---- Strategy pattern: different ways to work out the price of a stay ----
# Every plan has a name and a total(room, check_in, check_out) method.

class FlatRate:
    name = "Flat rate"

    def total(self, room, check_in, check_out):
        return (check_out - check_in).days * room.rate


class WeekendRate:
    name = "Weekend rate (+25% on Friday and Saturday nights)"

    def total(self, room, check_in, check_out):
        total = 0
        for i in range((check_out - check_in).days):
            night = check_in + timedelta(days=i)
            price = room.rate
            if night.weekday() in (4, 5):  # Friday, Saturday
                price = price * 1.25
            total += price
        return total


class LongStayDiscount:
    name = "Long stay (10% off when staying 7 nights or more)"

    def total(self, room, check_in, check_out):
        nights = (check_out - check_in).days
        total = nights * room.rate
        if nights >= 7:
            total = total * 0.9
        return total


PRICING_PLANS = [FlatRate(), WeekendRate(), LongStayDiscount()]


class RoomService:
    """Looks after the rooms."""

    def __init__(self):
        self.rooms = {}

    def add_room(self, number, room_type, rate=None):
        number = str(number)
        if number in self.rooms:
            raise HotelError(f"Room {number} already exists")
        if rate is not None and rate <= 0:
            raise HotelError("The rate must be more than 0")
        self.rooms[number] = RoomFactory.create(number, room_type, rate)
        return self.rooms[number]

    def get_room(self, number):
        room = self.rooms.get(str(number))
        if room is None:
            raise HotelError(f"There is no room {number}")
        return room

    def list_rooms(self):
        return sorted(self.rooms.values(), key=lambda r: r.number)

    def available_rooms(self, start, end):
        return [room for room in self.list_rooms() if room.is_free(start, end)]


class ReservationService:
    """Looks after guests and their reservations."""

    def __init__(self, room_service, pricing=None):
        self.room_service = room_service
        self.pricing = pricing or FlatRate()  # used for new reservations
        self.guests = {}
        self.reservations = {}
        self.listeners = []  # functions that want to hear about reservation events (Observer)

    # ---- guests ----

    def add_guest(self, name, email=""):
        if not name.strip():
            raise HotelError("A guest needs a name")
        guest_id = f"G{len(self.guests) + 1:03d}"
        self.guests[guest_id] = Guest(guest_id, name.strip(), email)
        return self.guests[guest_id]

    def get_guest(self, guest_id):
        guest = self.guests.get(guest_id.upper())
        if guest is None:
            raise HotelError(f"There is no guest {guest_id.upper()}")
        return guest

    # ---- reservations ----

    def reserve(self, guest_id, room_number, check_in, check_out):
        guest = self.get_guest(guest_id)
        room = self.room_service.get_room(room_number)

        if check_out <= check_in:
            raise HotelError("Check-out must be after check-in")
        if not room.is_free(check_in, check_out):
            raise HotelError(f"Room {room.number} is already booked for those dates")

        reservation_id = f"RS{len(self.reservations) + 1:03d}"
        reservation = Reservation(reservation_id, guest, room, check_in, check_out, self.pricing)
        self.reservations[reservation_id] = reservation
        room.reservations.append(reservation)
        self.tell_listeners("reserved", reservation)
        return reservation

    def get_reservation(self, reservation_id):
        reservation = self.reservations.get(reservation_id.upper())
        if reservation is None:
            raise HotelError(f"There is no reservation {reservation_id.upper()}")
        return reservation

    def list_reservations(self):
        return list(self.reservations.values())

    def check_in(self, reservation_id):
        reservation = self.get_reservation(reservation_id)
        if reservation.status != "Booked":
            raise HotelError(f"Can't check in, this reservation is {reservation.status}")
        reservation.status = "Checked in"
        self.tell_listeners("checked in", reservation)
        return reservation

    def check_out(self, reservation_id):
        reservation = self.get_reservation(reservation_id)
        if reservation.status != "Checked in":
            raise HotelError(f"Can't check out, this reservation is {reservation.status}")
        reservation.status = "Checked out"
        self.tell_listeners("checked out", reservation)
        return reservation

    def cancel(self, reservation_id):
        reservation = self.get_reservation(reservation_id)
        if reservation.status != "Booked":
            raise HotelError(f"Can't cancel, this reservation is {reservation.status}")
        # nothing else to do: the room counts as free again because
        # Room.is_free() ignores reservations that aren't active
        reservation.status = "Cancelled"
        self.tell_listeners("cancelled", reservation)
        return reservation

    # ---- Observer pattern ----

    def add_listener(self, listener):
        self.listeners.append(listener)

    def tell_listeners(self, event, reservation):
        for listener in self.listeners:
            try:
                listener(event, reservation)
            except Exception as error:
                # a broken listener should never stop a reservation from going through
                print(f"(a listener failed: {error})")
