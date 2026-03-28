import os
import pickle
import hashlib
import sqlite3

# Hardcoded credentials
SECRET_KEY = "hardcoded_secret_key_123"
DB_PASSWORD = "admin@1234"

# SQL Injection
def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Direct string formatting - SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchall()

# Insecure deserialization
def load_user_data(data: bytes):
    return pickle.loads(data)  # Arbitrary code execution risk

# Weak hashing
def hash_password(password: str):
    return hashlib.md5(password.encode()).hexdigest()  # MD5 is broken

# Path traversal
def read_file(filename: str):
    base_dir = "/var/app/uploads"
    # No path sanitization
    with open(os.path.join(base_dir, filename), "r") as f:
        return f.read()

# OS command injection
def run_report(report_name: str):
    os.system(f"python reports/{report_name}.py")  # Command injection

# Broad exception handling
def divide(a, b):
    try:
        return a / b
    except:  # Catches everything including KeyboardInterrupt
        pass

# Mutable default argument bug
def append_item(item, lst=[]):
    lst.append(item)
    return lst

# Infinite recursion
def factorial(n):
    return n * factorial(n - 1)  # Missing base case

# Resource leak
def write_log(message: str):
    f = open("app.log", "a")  # Never closed
    f.write(message + "\n")

if __name__ == "__main__":
    print(get_user("admin' OR '1'='1' --"))
    print(hash_password("mypassword"))
    print(append_item(1))
    print(append_item(2))  # Bug: returns [1, 2] not [2]
