# backend/database.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None

def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_ANON_KEY", "")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
        _client = create_client(url, key)
    return _client


def save_report(report: dict) -> bool:
    try:
        get_client().table("reports").upsert({
            "job_id":         report["job_id"],
            "filename":       report.get("filename", "unknown"),
            "language":       report.get("language", "python"),
            "score":          report.get("overall_score", 0),
            "verdict":        report.get("verdict", "needs_changes"),
            "total_findings": report.get("total_findings", 0),
            "report_json":    report,
        }).execute()
        print(f"[DB] Report saved → {report['job_id']}")
        return True
    except Exception as e:
        print(f"[DB] Failed to save report: {e}")
        return False


def get_report(job_id: str) -> dict | None:
    try:
        res = get_client().table("reports") \
            .select("report_json") \
            .eq("job_id", job_id) \
            .single() \
            .execute()
        return res.data["report_json"] if res.data else None
    except Exception as e:
        print(f"[DB] Failed to fetch report {job_id}: {e}")
        return None


def get_history(limit: int = 50) -> list:
    try:
        res = get_client().table("reports") \
            .select("job_id, filename, language, score, verdict, total_findings, created_at") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return res.data or []
    except Exception as e:
        print(f"[DB] Failed to fetch history: {e}")
        return []