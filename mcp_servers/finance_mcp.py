import sqlite3
import random
import string
from datetime import datetime

DB_PATH = "finance.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'unpaid',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            due_date TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            paid_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def generate_invoice_id():
    chars = string.ascii_uppercase + string.digits
    return "INV-" + "".join(random.choices(chars, k=8))

def generate_invoice(user_id: str, amount: float = None) -> dict:
    init_db()
    
    if amount is None:
        amount = round(random.uniform(99, 299), 2)
    
    invoice_id = generate_invoice_id()
    now = datetime.now()
    due_date = now.replace(day=min(now.day + 7, 28)).strftime("%Y-%m-%d")
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO invoices (invoice_id, user_id, amount, due_date, created_at) VALUES (?, ?, ?, ?, ?)",
        (invoice_id, user_id, amount, due_date, created_at)
    )
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "invoice_id": invoice_id,
        "user_id": user_id,
        "amount": amount,
        "status": "unpaid",
        "created_at": created_at,
        "due_date": due_date,
        "message": f"Invoice {invoice_id} generated for ${amount}. Due by {due_date}."
    }

def fetch_payment_status(user_id: str) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT invoice_id, amount, status, due_date, created_at FROM invoices WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    invoices = cursor.fetchall()
    conn.close()
    
    if not invoices:
        return {
            "success": False,
            "message": f"No invoices found for user {user_id}"
        }
    
    invoice_list = []
    for inv in invoices:
        invoice_list.append({
            "invoice_id": inv[0],
            "amount": inv[1],
            "status": inv[2],
            "due_date": inv[3],
            "created_at": inv[4]
        })
    
    unpaid = [i for i in invoice_list if i["status"] == "unpaid"]
    paid = [i for i in invoice_list if i["status"] == "paid"]
    
    return {
        "success": True,
        "user_id": user_id,
        "total_invoices": len(invoice_list),
        "unpaid_count": len(unpaid),
        "paid_count": len(paid),
        "invoices": invoice_list,
        "message": f"You have {len(unpaid)} unpaid and {len(paid)} paid invoice(s)."
    }

def download_invoice(invoice_id: str) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT invoice_id, user_id, amount, status, due_date, created_at FROM invoices WHERE invoice_id = ?",
        (invoice_id,)
    )
    invoice = cursor.fetchone()
    conn.close()
    
    if not invoice:
        return {
            "success": False,
            "message": f"Invoice {invoice_id} not found"
        }
    
    return {
        "success": True,
        "invoice": {
            "invoice_id": invoice[0],
            "user_id": invoice[1],
            "amount": invoice[2],
            "status": invoice[3],
            "due_date": invoice[4],
            "created_at": invoice[5]
        },
        "message": f"Invoice {invoice_id} details retrieved successfully."
    }

def mark_invoice_paid(invoice_id: str, user_id: str) -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, status, amount FROM invoices WHERE invoice_id = ? AND user_id = ?",
        (invoice_id, user_id)
    )
    invoice = cursor.fetchone()
    
    if not invoice:
        conn.close()
        return {"success": False, "message": f"Invoice {invoice_id} not found"}
    
    if invoice[1] == "paid":
        conn.close()
        return {"success": False, "message": f"Invoice {invoice_id} is already paid"}
    
    cursor.execute(
        "UPDATE invoices SET status = 'paid' WHERE invoice_id = ?",
        (invoice_id,)
    )
    cursor.execute(
        "INSERT INTO payments (invoice_id, user_id, amount) VALUES (?, ?, ?)",
        (invoice_id, user_id, invoice[2])
    )
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"Invoice {invoice_id} marked as paid successfully!"
    }