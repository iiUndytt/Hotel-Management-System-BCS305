# models.py - the basic classes for the hotel system


class HotelError(Exception):
    """Raised when someone tries to do something the hotel rules don't allow."""


class Room:
    room_type = "Room"
    default_rate = 400
    beds = 1

    def __init__(self, number, rate=None):
        self.number = number
        self.rate = rate or self.default_rate  # price per night
        self.reservations = []  # every reservation ever made for this room

    def is_free(self, start, end):
        # a room is taken if an active reservation overlaps the dates we want
        for res in self.reservations:
            if res.is_active() and res.check_in < end and start < res.check_out:
                return False
        return True


# The different kinds of room (RoomFactory in services.py decides which one to build)

class StandardRoom(Room):
    room_type = "Standard"
    default_rate = 450
    beds = 1


class DeluxeRoom(Room):
    room_type = "Deluxe"
    default_rate = 750
    beds = 2


class Suite(Room):
    room_type = "Suite"
    default_rate = 1200
    beds = 3


class Guest:
    def __init__(self, guest_id, name, email):
        self.id = guest_id
        self.name = name
        self.email = email


class Reservation:
    def __init__(self, reservation_id, guest, room, check_in, check_out, pricing):
        self.id = reservation_id
        self.guest = guest
        self.room = room
        self.check_in = check_in    # a date
        self.check_out = check_out  # a date
        self.pricing = pricing      # the pricing plan that was active when it was booked
        self.status = "Booked"      # Booked -> Checked in -> Checked out (or Cancelled)

    def is_active(self):
        # cancelled and checked-out reservations no longer block the room
        return self.status in ("Booked", "Checked in")

    def nights(self):
        return (self.check_out - self.check_in).days

    def total_price(self):
        return self.pricing.total(self.room, self.check_in, self.check_out)
