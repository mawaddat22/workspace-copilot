import sqlite3

DB_PATH = "bookings.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            room_id TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def check_availability(date: str, room_type: str) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE date = ? AND room_id LIKE ? AND status = 'confirmed'",
        (date, f"{room_type}%")
    )
    count = cursor.fetchone()[0]
    conn.close()
    capacity = {"meeting_room": 5, "desk": 20}.get(room_type, 10)
    available = capacity - count
    return {
        "date": date,
        "room_type": room_type,
        "available_slots": available,
        "is_available": available > 0
    }

def create_booking(user_id: str, room_id: str, date: str, time: str) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM bookings WHERE room_id = ? AND date = ? AND time = ? AND status = 'confirmed'",
        (room_id, date, time)
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return {"success": False, "message": f"{room_id} is already booked at {time} on {date}"}
    cursor.execute(
        "INSERT INTO bookings (user_id, room_id, date, time) VALUES (?, ?, ?, ?)",
        (user_id, room_id, date, time)
    )
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "success": True,
        "booking_id": booking_id,
        "message": f"Booking confirmed! Room {room_id} on {date} at {time}",
        "details": {"user_id": user_id, "room_id": room_id, "date": date, "time": time}
    }

def cancel_booking(booking_id: int) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, status FROM bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        conn.close()
        return {"success": False, "message": f"Booking #{booking_id} not found"}
    if booking[1] == "cancelled":
        conn.close()
        return {"success": False, "message": f"Booking #{booking_id} is already cancelled"}
    cursor.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Booking #{booking_id} has been cancelled"}