import unittest
from datetime import date, timedelta

from models import HotelError
from services import (RoomService, ReservationService, RoomFactory,
                      FlatRate, WeekendRate, LongStayDiscount)
from models import Suite, StandardRoom

TODAY = date.today()


def days(n):
    return TODAY + timedelta(days=n)


class HotelTests(unittest.TestCase):
    def setUp(self):
        self.rooms = RoomService()
        self.rooms.add_room("101", "Standard", 450)
        self.rooms.add_room("102", "Standard", 450)
        self.hotel = ReservationService(self.rooms)
        self.sara = self.hotel.add_guest("Sara")
        self.tariq = self.hotel.add_guest("Tariq")

    def test_double_booking_is_refused(self):
        self.hotel.reserve(self.sara.id, "101", days(0), days(3))
        with self.assertRaises(HotelError):
            self.hotel.reserve(self.tariq.id, "101", days(2), days(4))

    def test_back_to_back_stays_are_fine(self):
        self.hotel.reserve(self.sara.id, "101", days(0), days(2))
        self.hotel.reserve(self.tariq.id, "101", days(2), days(4))  # leaves the day Sara checks out

    def test_checkout_must_be_after_checkin(self):
        with self.assertRaises(HotelError):
            self.hotel.reserve(self.sara.id, "101", days(2), days(2))

    def test_available_rooms(self):
        self.hotel.reserve(self.sara.id, "101", days(0), days(2))
        free = [r.number for r in self.rooms.available_rooms(days(0), days(1))]
        self.assertEqual(free, ["102"])

    def test_cancel_frees_the_room(self):
        res = self.hotel.reserve(self.sara.id, "101", days(0), days(2))
        self.hotel.cancel(res.id)
        self.hotel.reserve(self.tariq.id, "101", days(0), days(2))  # works now

    def test_checkout_frees_the_room(self):
        res = self.hotel.reserve(self.sara.id, "101", days(0), days(2))
        self.hotel.check_in(res.id)
        self.hotel.check_out(res.id)
        self.assertEqual(len(self.rooms.available_rooms(days(0), days(2))), 2)

    def test_check_in_and_out_order(self):
        res = self.hotel.reserve(self.sara.id, "101", days(0), days(2))
        with self.assertRaises(HotelError):
            self.hotel.check_out(res.id)       # not checked in yet
        self.hotel.check_in(res.id)
        with self.assertRaises(HotelError):
            self.hotel.check_in(res.id)        # already checked in
        with self.assertRaises(HotelError):
            self.hotel.cancel(res.id)          # too late to cancel

    def test_total_price(self):
        res = self.hotel.reserve(self.sara.id, "101", days(0), days(3))
        self.assertEqual(res.total_price(), 1350)

    # ---- Factory ----
    def test_factory_builds_the_right_room(self):
        self.assertIsInstance(RoomFactory.create("301", "suite"), Suite)
        self.assertIsInstance(RoomFactory.create("105", "STANDARD"), StandardRoom)

    def test_factory_uses_default_price_unless_given(self):
        self.assertEqual(RoomFactory.create("301", "Suite").rate, 1200)
        self.assertEqual(RoomFactory.create("301", "Suite", 999).rate, 999)

    def test_factory_rejects_unknown_type(self):
        with self.assertRaises(HotelError):
            RoomFactory.create("999", "Penthouse")

    # ---- Strategy ----
    def test_pricing_plans(self):
        room = self.rooms.get_room("101")                  # 450 per night
        monday = date(2026, 11, 9)                          # a Monday
        week = monday + timedelta(days=7)
        self.assertEqual(FlatRate().total(room, monday, week), 3150)
        self.assertEqual(WeekendRate().total(room, monday, week), 3150 + 2 * 450 * 0.25)
        self.assertEqual(LongStayDiscount().total(room, monday, week), 3150 * 0.9)
        self.assertEqual(LongStayDiscount().total(room, monday, monday + timedelta(days=2)), 900)

    def test_reservation_keeps_the_plan_it_was_booked_with(self):
        res = self.hotel.reserve(self.sara.id, "101", days(0), days(2))
        self.hotel.pricing = LongStayDiscount()            # changed later
        self.assertIsInstance(res.pricing, FlatRate)

    # ---- Observer ----
    def test_listener_hears_events(self):
        heard = []
        self.hotel.add_listener(lambda event, res: heard.append(event))
        res = self.hotel.reserve(self.sara.id, "101", days(0), days(2))
        self.hotel.check_in(res.id)
        self.hotel.check_out(res.id)
        self.assertEqual(heard, ["reserved", "checked in", "checked out"])

    def test_broken_listener_does_not_stop_a_reservation(self):
        def broken(event, res):
            raise RuntimeError("oops")
        self.hotel.add_listener(broken)
        res = self.hotel.reserve(self.sara.id, "101", days(0), days(2))
        self.assertEqual(res.status, "Booked")


if __name__ == "__main__":
    unittest.main()
