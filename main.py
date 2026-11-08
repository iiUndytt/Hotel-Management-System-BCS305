# main.py - console menu for the hotel system
# Run it with:  python main.py        (menu)
#               python main.py demo   (quick scripted walkthrough)

import sys
from datetime import date, datetime, timedelta

from models import HotelError
from services import RoomService, ReservationService, PRICING_PLANS

room_service = RoomService()
reservation_service = ReservationService(room_service)


def housekeeping(event, reservation):
    # gets called by ReservationService whenever something happens to a reservation
    if event == "checked out":
        print(f"  [Housekeeping] please clean room {reservation.room.number}")
    elif event == "cancelled":
        print(f"  [Front desk] {reservation.id} cancelled, room {reservation.room.number} is free again")


def load_sample_data():
    for number, room_type in [("101", "Standard"), ("102", "Standard"), ("103", "Standard"),
                              ("201", "Deluxe"), ("202", "Deluxe"), ("301", "Suite")]:
        room_service.add_room(number, room_type)


def ask(question, default=""):
    shown = f"{question} [{default}]: " if default else f"{question}: "
    return input(shown).strip() or default


def ask_dates():
    # start date (today if left empty) + number of nights
    start_text = ask("Check-in date (YYYY-MM-DD)", str(date.today()))
    start = datetime.strptime(start_text, "%Y-%m-%d").date()
    nights = int(ask("Number of nights", "1"))
    return start, start + timedelta(days=nights)


# ---------- menu actions ----------

def show_room(room):
    print(f"  {room.number}  {room.room_type:<9} {room.beds} bed(s)  {room.rate:.0f} per night")


def add_room():
    number = ask("Room number")
    room_type = ask("Room type (Standard, Deluxe or Suite)")
    rate = ask("Price per night (leave empty for the normal price)")
    room = room_service.add_room(number, room_type, float(rate) if rate else None)
    print(f"Added {room.room_type} room {room.number} at {room.rate:.0f} per night.")


def view_rooms():
    for room in room_service.list_rooms():
        show_room(room)


def view_available_rooms():
    start, end = ask_dates()
    rooms = room_service.available_rooms(start, end)
    if not rooms:
        print("No rooms are free for those dates.")
    for room in rooms:
        show_room(room)


def add_guest():
    guest = reservation_service.add_guest(ask("Guest name"), ask("Email (optional)"))
    print(f"Added {guest.name}, guest id {guest.id}.")


def reserve_room():
    guest_id = ask("Guest id")
    room_number = ask("Room number")
    start, end = ask_dates()
    res = reservation_service.reserve(guest_id, room_number, start, end)
    print(f"Reserved! {res.id}: {res.guest.name}, room {res.room.number}, "
          f"{res.nights()} night(s), total {res.total_price():.0f}.")


def view_reservations():
    if not reservation_service.reservations:
        print("No reservations yet.")
    for res in reservation_service.list_reservations():
        print(f"  {res.id}  {res.guest.name:<14} room {res.room.number}  "
              f"{res.check_in:%d %b} -> {res.check_out:%d %b}  {res.status}")


def check_in():
    res = reservation_service.check_in(ask("Reservation id"))
    print(f"{res.guest.name} is checked in to room {res.room.number}.")


def check_out():
    res = reservation_service.check_out(ask("Reservation id"))
    print(f"{res.guest.name} is checked out. Total to pay: {res.total_price():.0f}.")


def change_pricing():
    print(f"Current plan: {reservation_service.pricing.name}")
    for number, plan in enumerate(PRICING_PLANS, start=1):
        print(f"  {number}. {plan.name}")
    choice = int(ask("Pick a plan"))
    if not 1 <= choice <= len(PRICING_PLANS):
        raise ValueError("that plan number doesn't exist")
    reservation_service.pricing = PRICING_PLANS[choice - 1]
    print("New reservations will use this plan.")


def cancel_reservation():
    res = reservation_service.cancel(ask("Reservation id"))
    print(f"{res.id} cancelled. Room {res.room.number} is free again.")


MENU = [
    ("Add room", add_room),
    ("View all rooms", view_rooms),
    ("View available rooms", view_available_rooms),
    ("Add guest", add_guest),
    ("Reserve a room", reserve_room),
    ("View reservations", view_reservations),
    ("Check in guest", check_in),
    ("Check out guest", check_out),
    ("Cancel reservation", cancel_reservation),
    ("Change pricing plan", change_pricing),
]


def run_menu():
    while True:
        print("\n=== Hotel Management System ===")
        for number, (label, _) in enumerate(MENU, start=1):
            print(f"{number:>2}. {label}")
        print(" 0. Exit")

        choice = input("Choose: ").strip()
        if choice == "0":
            print("Bye!")
            break
        if not choice.isdigit() or not 1 <= int(choice) <= len(MENU):
            print("Please type one of the numbers above.")
            continue
        try:
            MENU[int(choice) - 1][1]()
        except (HotelError, ValueError) as error:
            print(f"Error: {error}")


# ---------- scripted demo ----------

def try_it(description, action, *args):
    # runs one step of the demo and shows the error if the rules say no
    try:
        result = action(*args)
        print(f"OK   - {description}")
        return result
    except HotelError as error:
        print(f"FAIL - {description}: {error}")


def run_demo():
    today = date.today()
    sara = reservation_service.add_guest("Sara Ali")
    tariq = reservation_service.add_guest("Tariq Noor")

    print("--- Reservations and double booking ---")
    first = try_it("Sara reserves room 201 for 2 nights", reservation_service.reserve,
                   sara.id, "201", today, today + timedelta(days=2))
    try_it("Tariq tries room 201 for tonight", reservation_service.reserve,
           tariq.id, "201", today, today + timedelta(days=1))
    print("     free rooms tonight:",
          [r.number for r in room_service.available_rooms(today, today + timedelta(days=1))])

    print("\n--- Cancel ---")
    try_it("Sara cancels", reservation_service.cancel, first.id)
    print("     free rooms tonight:",
          [r.number for r in room_service.available_rooms(today, today + timedelta(days=1))])
    second = try_it("Tariq tries room 201 again", reservation_service.reserve,
                    tariq.id, "201", today, today + timedelta(days=1))

    print("\n--- Check-in and check-out ---")
    try_it("Tariq checks out before checking in", reservation_service.check_out, second.id)
    try_it("Tariq checks in", reservation_service.check_in, second.id)
    try_it("Tariq cancels after check-in", reservation_service.cancel, second.id)
    try_it("Tariq checks out", reservation_service.check_out, second.id)

    print("\n--- Same 7-night stay in room 201 under each pricing plan ---")
    room = room_service.get_room("201")
    monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)  # next Monday
    for plan in PRICING_PLANS:
        print(f"     {plan.name}: {plan.total(room, monday, monday + timedelta(days=7)):.0f}")

    print("\n--- Reservations now ---")
    view_reservations()


if __name__ == "__main__":
    reservation_service.add_listener(housekeeping)
    load_sample_data()
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
    else:
        run_menu()
