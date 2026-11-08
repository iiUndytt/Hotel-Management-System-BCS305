# Hotel Management System

This project is a Hotel Management system implemented for the Software Architecture class of BCS 305.

The system assists in the management of hotel rooms, guests and reservations. It enables employees to check booking, book a room, process guests' check-in/out and cancel reservations.

## Main Features

Add and view Hotel Rooms.
- Assist in Standard, Deluxe and Suite rooms.
- Reserve spaces according to the dates.
- Register guests.
- Make room reservations.
- Prevent double bookings.
- Calculate reservation prices.
- Confirm guests' identities at check in/out.
- Cancel reservations.
- Select pricing options.

## Project Structure

- `models.py` – This holds the primary classes like Room, Guest and Reservation.
- `services.py` – manages the rooms, make reservations, price and hotel operation.
This includes all the menus and demonstration code in 'main.py'.
- `tests.py` – Tests to check the system's functionality.

## Design Patterns

The project implements three design patterns in this way:

**1. Factory Pattern**

Standard, Deluxe and Suite are used to create room types to choose from.

**2. Strategy Pattern**

Used in making an estimation of the reservation prices. You can set flat, weekend (holiday) or long-stay discounts.

**3. Observer Pattern**

Communicated to inform other components of the system of certain reservation related events, such as guest checkout/cancelling a reservation.

## How to Run

Ensure the package Python is installed (version 3.8 or later).

From the project folder, execute the commands below:

Press 1 at anytime to begin the interactive menu.

```bash
python main.py
```

Run the demonstration:

```bash
python main.py demo
```

Run the tests:

```bash
python tests.py
```

## Notes

The system is configured with the sample rooms first to enable immediate testing of the features of the system.

The project will be a mini-working-prototype of hotel systems to show some concepts of operations and software architecture.
