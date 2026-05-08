# backend/database.py
"""
Database layer using Supabase.
All functions are fail-safe — DB errors are logged but never crash the app.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Lazy client with connection guard ─────────────────────────────────────────

_client = None
_db_available = None   # None = untested, True = ok, False = unavailable


def _get_client():
    """
    Returns Supabase client or None if unavailable.
    Caches availability so we don't retry on every request.
    """
    global _client, _db_available

    # Already confirmed unavailable — skip immediately
    if _db_available is False:
        return None

    # Already connected
    if _client is not None:
        return _client

    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_ANON_KEY", "").strip()

        if not url or not key:
            print("[DB] ⚠️  SUPABASE_URL or SUPABASE_ANON_KEY not set — running without DB.")
            _db_available = False
            return None

        _client = create_client(url, key)
        _db_available = True
        print("[DB] ✅ Supabase connected.")
        return _client

    except Exception as e:
        print(f"[DB] ⚠️  Could not connect to Supabase: {e}")
        _db_available = False
        return None


def is_available() -> bool:
    """Returns True if DB is reachable."""
    return _get_client() is not None


# ── Save report ───────────────────────────────────────────────────────────────


def save_report(report: dict) -> bool:
    """
    Upsert a report into the 'reports' table.
    Returns True on success, False if DB is down or save fails.
    Never raises — always safe to call.
    """
    client = _get_client()
    if client is None:
        return False   # silently skip — DB unavailable

    try:
        client.table("reports").upsert({
            "job_id":         report["job_id"],
            "filename":       report.get("filename", "unknown"),
            "language":       report.get("language", "python"),
            "score":          report.get("overall_score", 0),
            "verdict":        report.get("verdict", "needs_changes"),
            "total_findings": report.get("total_findings", 0),
            "report_json":    report,
        }).execute()
        print(f"[DB] ✅ Report saved → {report['job_id']}")
        return True

    except Exception as e:
        print(f"[DB] Failed to save report: {e}")
        return False


# ── Fetch single report ───────────────────────────────────────────────────────


def get_report(job_id: str) -> dict | None:
    """
    Fetch full report JSON by job_id.
    Returns None if DB is down or record not found.
    """
    client = _get_client()
    if client is None:
        return None

    try:
        res = (
            client.table("reports")
            .select("report_json")
            .eq("job_id", job_id)
            .single()
            .execute()
        )
        return res.data["report_json"] if res.data else None

    except Exception as e:
        print(f"[DB] Failed to fetch report {job_id}: {e}")
        return None


# ── Fetch history list ────────────────────────────────────────────────────────


def get_history(limit: int = 50) -> list:
    """
    Returns list of recent reports (summary only, no full JSON).
    Returns empty list if DB is down.
    """
    client = _get_client()
    if client is None:
        return []

    try:
        res = (
            client.table("reports")
            .select("job_id, filename, language, score, verdict, total_findings, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    except Exception as e:
        print(f"[DB] Failed to fetch history: {e}")
        return []


# ── Delete report ─────────────────────────────────────────────────────────────


def delete_report(job_id: str) -> bool:
    """
    Delete a report by job_id.
    Returns True on success, False otherwise.
    """
    client = _get_client()
    if client is None:
        return False

    try:
        client.table("reports").delete().eq("job_id", job_id).execute()
        print(f"[DB] 🗑️  Report deleted → {job_id}")
        return True

    except Exception as e:
        print(f"[DB] Failed to delete report {job_id}: {e}")
        return False


# ── Health check ──────────────────────────────────────────────────────────────


def health_check() -> dict:
    """
    Returns DB status — used by /health endpoint.
    """
    client = _get_client()
    if client is None:
        return {"database": "unavailable", "reason": "No credentials or connection failed"}

    try:
        # Lightweight ping — fetch 1 row
        client.table("reports").select("job_id").limit(1).execute()
        return {"database": "connected"}
    except Exception as e:
        return {"database": "error", "reason": str(e)}