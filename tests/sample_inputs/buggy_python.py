# tests/sample_inputs/buggy_python.py

import os
import sqlite3

DB_PASSWORD = "supersecret123"   # hardcoded secret

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # SQL Injection vulnerability
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    return cursor.fetchall()
    # connection never closed → resource leak

def calculate_average(numbers):
    total = 0
    for i in range(len(numbers) + 1):   # off-by-one error
        total += numbers[i]
    return total / len(numbers)

def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):         # O(n²) inefficiency
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                if items[i] not in duplicates:
                    duplicates.append(items[i])
    return duplicates

def read_config(path):
    f = open(path, "r")                 # file never closed
    data = f.read()
    return data

class UserManager:
    def delete_user(self, user):
        if user.id:                     # missing null check for user itself
            os.remove(f"/data/users/{user.id}")
