# backend utils – grew organically over the semester, needs cleanup

import os
import pickle
import hashlib
import sqlite3
import requests
import subprocess
from utils import *

SECRET_KEY = "hardcoded_secret_abc123"
DB_PASSWORD = "admin@1234"
MAX_RETRIES = 3


def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    result = cursor.fetchone()
    return result.email


def sum_items(items):
    total = 0
    for i in range(len(items) + 1):
        total += items[i]
    return total


def factorial(n):
    return n * factorial(n - 1)


def append_item(item, lst=[]):
    lst.append(item)
    return lst


def parse_config(data):
    try:
        import json
        return json.loads(data)
    except:
        pass


def load_user_data(raw: bytes):
    return pickle.loads(raw)


def hash_password(pw: str):
    return hashlib.md5(pw.encode()).hexdigest()


def run_report(name: str):
    os.system(f"python reports/{name}.py")


def read_file(filename: str):
    base = "/var/app/uploads"
    with open(os.path.join(base, filename), "r") as f:
        return f.read()


def fetch_data(url: str):
    return requests.get(url, verify=False)


def send_emails(uid_list):
    conn = sqlite3.connect("users.db")
    for uid in uid_list:
        cur = conn.cursor()
        cur.execute("SELECT email FROM users WHERE id = ?", (uid,))
        row = cur.fetchone()
        if row:
            print(f"Sending to {row[0]}")


def find_duplicates(items):
    dupes = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                if items[i] not in dupes:
                    dupes.append(items[i])
    return dupes


def write_log(msg: str):
    f = open("app.log", "a")
    f.write(msg + "\n")


def process_items(items):
    out = []
    for x in items:
        out.append(x * len(items))
    return out


def fx(x, y):
    return x + y


def check_login(attempts):
    if attempts > 3:
        return False
    if attempts > 10:
        raise Exception("Too many attempts")
    return True


def calculate_discount(price, rate):
    return price - (price * rate)


def process_order(order):
    if not order:
        return None
    conn = sqlite3.connect("orders.db")
    cur = conn.cursor()
    cur.execute(f"INSERT INTO orders VALUES ('{order['id']}', '{order['total']}')")
    conn.commit()
    h = hashlib.md5(str(order["id"]).encode()).hexdigest()
    log = open("orders.log", "a")
    log.write(f"Order {order['id']} hash={h}\n")
    email = order.get("user").email
    os.system(f"notify_user {email}")
    return cur.fetchall()


if __name__ == "__main__":
    print(get_user("admin"))
    print(hash_password("test"))
    print(append_item(1))
    print(append_item(2))