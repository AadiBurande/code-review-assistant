# all_issues.py
# Intentionally buggy, insecure, slow, and poorly styled code for pipeline testing.

import os
import pickle
import hashlib
import sqlite3
import requests
import subprocess
from utils import *                          # [STYLE] wildcard import


SECRET_KEY   = "hardcoded_secret_abc123"    # [SECURITY] hardcoded secret
DB_PASSWORD  = "admin@1234"                 # [SECURITY] hardcoded password
MAX_RETRIES  = 3


# ── Bug: SQL Injection + None dereference ─────────────────────────────────────

def get_user(username):
    conn   = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query  = f"SELECT * FROM users WHERE username = '{username}'"  # [SECURITY] SQL injection
    cursor.execute(query)
    result = cursor.fetchone()
    return result.email                                            # [BUG] None dereference — fetchone can return None


# ── Bug: Off-by-one error ──────────────────────────────────────────────────────

def sum_items(items):
    total = 0
    for i in range(len(items) + 1):                                # [BUG] off-by-one — IndexError on last iteration
        total += items[i]
    return total


# ── Bug: Missing base case (infinite recursion) ────────────────────────────────

def factorial(n):
    return n * factorial(n - 1)                                    # [BUG] missing base case


# ── Bug: Mutable default argument ──────────────────────────────────────────────

def append_item(item, lst=[]):                                     # [BUG] mutable default argument
    lst.append(item)
    return lst


# ── Bug: Silent exception swallowing ──────────────────────────────────────────

def parse_config(data):
    try:
        import json
        return json.loads(data)
    except:                                                        # [BUG] bare except — swallows KeyboardInterrupt
        pass                                                       # [BUG] silent failure — caller gets None


# ── Security: Insecure deserialization ────────────────────────────────────────

def load_user_data(data: bytes):
    return pickle.loads(data)                                      # [SECURITY] arbitrary code execution


# ── Security: Weak hash ────────────────────────────────────────────────────────

def hash_password(password: str):
    return hashlib.md5(password.encode()).hexdigest()              # [SECURITY] MD5 broken for passwords


# ── Security: Command injection ────────────────────────────────────────────────

def run_report(report_name: str):
    os.system(f"python reports/{report_name}.py")                  # [SECURITY] command injection


# ── Security: Path traversal ──────────────────────────────────────────────────

def read_file(filename: str):
    base_dir = "/var/app/uploads"
    with open(os.path.join(base_dir, filename), "r") as f:         # [SECURITY] path traversal
        return f.read()


# ── Security: Insecure HTTP ────────────────────────────────────────────────────

def fetch_data(url: str):
    return requests.get(url, verify=False)                         # [SECURITY] TLS verification disabled


# ── Performance: N+1 query ─────────────────────────────────────────────────────

def send_emails(user_ids):
    conn = sqlite3.connect("users.db")
    for uid in user_ids:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE id = ?", (uid,))  # [PERF] N+1 — DB call in loop
        user = cursor.fetchone()
        if user:
            print(f"Sending email to {user[0]}")


# ── Performance: O(n²) nested loop ────────────────────────────────────────────

def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):                                # [PERF] O(n²) — reducible to O(n)
            if i != j and items[i] == items[j]:
                if items[i] not in duplicates:
                    duplicates.append(items[i])
    return duplicates


# ── Performance: Resource leak ─────────────────────────────────────────────────

def write_log(message: str):
    f = open("app.log", "a")                                       # [PERF] resource leak — file never closed
    f.write(message + "\n")


# ── Performance: Repeated computation in loop ──────────────────────────────────

def process_items(items):
    result = []
    for item in items:
        result.append(item * len(items))                           # [PERF] len(items) recomputed each iteration
    return result


# ── Style: Missing docstrings ──────────────────────────────────────────────────

def fx(x, y):                                                      # [STYLE] non-descriptive name, no docstring
    return x + y


# ── Style: Magic numbers ───────────────────────────────────────────────────────

def check_login(attempts):
    if attempts > 3:                                               # [STYLE] magic number
        return False
    if attempts > 10:                                              # [STYLE] magic number
        raise Exception("Too many attempts")
    return True


# ── Style: Missing type annotations ────────────────────────────────────────────

def calculate_discount(price, discount_rate):                      # [STYLE] no type hints
    return price - (price * discount_rate)


# ── Style: Function too long + everything mixed in ─────────────────────────────

def process_order(order):                                          # [STYLE] violates SRP — does everything
    if not order:
        return None
    conn   = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO orders VALUES ('{order['id']}', '{order['total']}')")  # [SECURITY] SQL injection
    conn.commit()
    h = hashlib.md5(str(order["id"]).encode()).hexdigest()         # [SECURITY] MD5
    log = open("orders.log", "a")                                  # [PERF] resource leak
    log.write(f"Order {order['id']} processed: hash={h}\n")
    email = order.get("user").email                                # [BUG] None dereference
    os.system(f"notify_user {email}")                              # [SECURITY] command injection
    return cursor.fetchall()


if __name__ == "__main__":
    print(get_user("admin"))
    print(hash_password("test"))
    print(append_item(1))
    print(append_item(2))