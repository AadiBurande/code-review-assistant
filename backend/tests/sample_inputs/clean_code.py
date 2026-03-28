# clean_code.py
# Well-structured, secure, performant, and correctly typed Python module.
# Pipeline should return score >= 85 and verdict = 'accept'.

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS: int = 3
LOCKOUT_THRESHOLD:  int = 10
UPLOAD_DIR:         Path = Path("/var/app/uploads").resolve()


# ── User lookup — parameterized query, None-safe ──────────────────────────────

def get_user_email(conn, username: str) -> Optional[str]:
    """
    Fetch the email for a given username using a parameterized query.
    Returns None if the user does not exist.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    return row[0] if row else None


# ── Password hashing — bcrypt-safe wrapper ────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a random salt.
    Returns a hex-encoded digest.
    """
    salt = os.urandom(32)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + digest.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash."""
    try:
        salt_hex, digest_hex = stored_hash.split(":")
        salt   = bytes.fromhex(salt_hex)
        digest = bytes.fromhex(digest_hex)
        new_digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return hmac.compare_digest(new_digest, digest)
    except (ValueError, AttributeError):
        logger.error("Invalid stored hash format")
        return False


# ── Safe file read — path traversal prevented ─────────────────────────────────

def read_upload(filename: str) -> Optional[str]:
    """
    Read a file from the uploads directory.
    Raises ValueError if the resolved path escapes the upload directory.
    """
    full_path = (UPLOAD_DIR / filename).resolve()
    if not str(full_path).startswith(str(UPLOAD_DIR)):
        raise ValueError(f"Invalid path: '{filename}' escapes upload directory.")
    try:
        return full_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to read file %s: %s", filename, exc)
        return None


# ── Config parser — typed, explicit exception ─────────────────────────────────

def parse_config(raw: str) -> Optional[dict]:
    """
    Parse a JSON config string.
    Returns None and logs on failure — never silently swallows errors.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse config JSON: %s", exc)
        return None


# ── Login guard — named constants, no magic numbers ───────────────────────────

def check_login_attempts(attempts: int) -> bool:
    """
    Return False if the attempt count exceeds the allowed maximum.
    Raises RuntimeError if the lockout threshold is exceeded.
    """
    if attempts > LOCKOUT_THRESHOLD:
        raise RuntimeError("Account locked: too many failed login attempts.")
    return attempts <= MAX_LOGIN_ATTEMPTS


# ── Bulk email — batched query, no N+1 ────────────────────────────────────────

def get_user_emails(conn, user_ids: List[int]) -> List[str]:
    """
    Fetch emails for a list of user IDs in a single batched query.
    Returns a list of email strings.
    """
    if not user_ids:
        return []
    placeholders = ", ".join("?" * len(user_ids))
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT email FROM users WHERE id IN ({placeholders})",
        tuple(user_ids),
    )
    return [row[0] for row in cursor.fetchall()]


# ── Duplicate detection — O(n) using set ──────────────────────────────────────

def find_duplicates(items: List[str]) -> List[str]:
    """
    Return a list of items that appear more than once.
    Runs in O(n) time using a set-based approach.
    """
    seen:  set  = set()
    dupes: list = []
    for item in items:
        if item in seen:
            dupes.append(item)
        else:
            seen.add(item)
    return dupes


# ── Discount calculator — typed, documented ───────────────────────────────────

def calculate_discount(price: float, discount_rate: float) -> float:
    """
    Apply a fractional discount rate to a price.
    Example: calculate_discount(100.0, 0.10) → 90.0
    """
    if not 0.0 <= discount_rate <= 1.0:
        raise ValueError(                          # split long line
             f"discount_rate must be between 0.0 and 1.0, got {discount_rate}"
       )
    return round(price * (1.0 - discount_rate), 2)


# ── Sum items — correct bounds ─────────────────────────────────────────────────

def sum_items(items: List[float]) -> float:
    """Return the sum of all items in the list."""
    return sum(items)


# ── Factorial — correct base case ─────────────────────────────────────────────

def factorial(n: int) -> int:
    """Return n! for non-negative integers."""
    if n < 0:
        raise ValueError("factorial() not defined for negative values")
    if n == 0:
        return 1
    return n * factorial(n - 1)


# ── Append item — immutable default argument ──────────────────────────────────

def append_item(item: str, lst: Optional[List[str]] = None) -> List[str]:
    """Append item to lst and return it. Creates a new list if none provided."""
    if lst is None:
        lst = []
    lst.append(item)
    return lst


# ── Log writer — context manager, no resource leak ────────────────────────────

def write_log(message: str, log_path: str = "app.log") -> None:
    """Append a message to the log file using a context manager."""
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")


if __name__ == "__main__":
    print(hash_password("securepassword"))
    print(find_duplicates(["a", "b", "a", "c", "b"]))
    print(calculate_discount(100.0, 0.15))
    print(factorial(5))
    print(sum_items([1.0, 2.0, 3.0]))