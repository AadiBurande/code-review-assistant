# github_integration.py
"""
GitHub Integration Module
Fetches repository files via GitHub REST API (no git clone needed).
Supports:
  - Full repo URL:        https://github.com/owner/repo
  - Branch URL:          https://github.com/owner/repo/tree/branch-name
  - Single file URL:     https://github.com/owner/repo/blob/main/path/to/file.py
  - Subfolder URL:       https://github.com/owner/repo/tree/main/src/folder
"""

import os
import re
import base64
import requests
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# ── Result Schema ─────────────────────────────────────────────────────────────

@dataclass
class GitHubFetchResult:
    success:          bool
    local_path:       str
    repo_name:        str
    owner:            str
    branch:           str
    detected_language: str
    file_count:       int
    total_bytes:      int
    files_fetched:    list = field(default_factory=list)
    error:            str  = ""


# ── Language Detection ─────────────────────────────────────────────────────────

EXT_TO_LANGUAGE = {
    ".py":    "python",
    ".js":    "javascript",
    ".jsx":   "javascript",
    ".ts":    "typescript",
    ".tsx":   "typescript",
    ".java":  "java",
    ".cpp":   "cpp",
    ".cc":    "cpp",
    ".cxx":   "cpp",
    ".c":     "c",
    ".h":     "c",
    ".go":    "go",
    ".rb":    "ruby",
    ".rs":    "rust",
    ".php":   "php",
    ".cs":    "csharp",
    ".swift": "swift",
    ".kt":    "kotlin",
    ".scala": "scala",
}

SUPPORTED_EXTENSIONS = set(EXT_TO_LANGUAGE.keys())

# Files/dirs to always skip
SKIP_PATTERNS = {
    ".git", ".github", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", ".tox", "eggs", ".eggs", "*.egg-info",
    ".DS_Store", "Thumbs.db", "*.min.js", "*.min.css",
    "package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock",
}

MAX_FILE_SIZE_BYTES = 150_000   # 150 KB per file
MAX_TOTAL_FILES     = 60        # max files to fetch from one repo
MAX_TOTAL_BYTES     = 3_000_000 # 3 MB total


def _should_skip(path: str) -> bool:
    parts = Path(path).parts
    for part in parts:
        if part in SKIP_PATTERNS:
            return True
        if part.startswith(".") and part not in {".env"}:
            return True
    return False


def _detect_language(files: list) -> str:
    """Detect the dominant language by counting file extensions."""
    counts: dict = {}
    for f in files:
        ext = Path(f).suffix.lower()
        lang = EXT_TO_LANGUAGE.get(ext)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return max(counts, key=counts.get) if counts else "python"


# ── URL Parser ────────────────────────────────────────────────────────────────

def _parse_github_url(url: str) -> dict:
    """
    Parse a GitHub URL into its components.

    Returns dict with keys:
        owner, repo, type (repo|blob|tree), branch, path
    """
    url = url.strip().rstrip("/")

    # Remove trailing .git
    if url.endswith(".git"):
        url = url[:-4]

    # Pattern: https://github.com/owner/repo[/tree|blob/branch[/path]]
    pattern = r"https?://github\.com/([^/]+)/([^/]+)(?:/(tree|blob)/([^/]+)(?:/(.+))?)?"
    match = re.match(pattern, url)

    if not match:
        raise ValueError(
            f"Invalid GitHub URL: '{url}'. "
            "Expected format: https://github.com/owner/repo"
        )

    owner  = match.group(1)
    repo   = match.group(2)
    kind   = match.group(3) or "repo"
    branch = match.group(4) or "main"
    path   = match.group(5) or ""

    return {"owner": owner, "repo": repo, "type": kind, "branch": branch, "path": path}


# ── GitHub API Client ─────────────────────────────────────────────────────────

class GitHubAPIClient:
    BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept":               "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def _get(self, url: str, params: dict = None) -> requests.Response:
        resp = self.session.get(url, params=params, timeout=20)
        return resp

    def get_repo(self, owner: str, repo: str) -> dict:
        """Get repo metadata — also resolves default branch."""
        resp = self._get(f"{self.BASE}/repos/{owner}/{repo}")
        if resp.status_code == 404:
            raise ValueError(f"Repository '{owner}/{repo}' not found or is private.")
        if resp.status_code == 403:
            raise ValueError("GitHub API rate limit reached. Provide a GITHUB_TOKEN.")
        resp.raise_for_status()
        return resp.json()

    def get_tree(self, owner: str, repo: str, branch: str) -> list:
        """Get full recursive file tree for a branch."""
        # First get the branch SHA
        resp = self._get(f"{self.BASE}/repos/{owner}/{repo}/branches/{branch}")
        if resp.status_code == 404:
            # Try 'master' fallback if 'main' not found
            if branch == "main":
                resp = self._get(f"{self.BASE}/repos/{owner}/{repo}/branches/master")
                if resp.status_code == 404:
                    raise ValueError(f"Branch '{branch}' not found in '{owner}/{repo}'.")
            else:
                raise ValueError(f"Branch '{branch}' not found in '{owner}/{repo}'.")
        resp.raise_for_status()
        sha = resp.json()["commit"]["commit"]["tree"]["sha"]

        # Now get the full recursive tree
        tree_resp = self._get(
            f"{self.BASE}/repos/{owner}/{repo}/git/trees/{sha}",
            params={"recursive": "1"},
        )
        tree_resp.raise_for_status()
        data = tree_resp.json()

        if data.get("truncated"):
            print("  [GitHub] Warning: repository tree was truncated by GitHub API (very large repo).")

        return [item for item in data.get("tree", []) if item["type"] == "blob"]

    def get_file_content(self, owner: str, repo: str, path: str, branch: str) -> Optional[bytes]:
        """Download a single file's content."""
        resp = self._get(
            f"{self.BASE}/repos/{owner}/{repo}/contents/{path}",
            params={"ref": branch},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        # API returns base64-encoded content
        if isinstance(data, dict) and data.get("encoding") == "base64":
            return base64.b64decode(data["content"])

        # Fallback: use download_url
        dl_url = data.get("download_url")
        if dl_url:
            dl = self.session.get(dl_url, timeout=20)
            dl.raise_for_status()
            return dl.content

        return None

    def get_rate_limit(self) -> dict:
        resp = self._get(f"{self.BASE}/rate_limit")
        if resp.ok:
            return resp.json().get("resources", {}).get("core", {})
        return {}


# ── Main Fetcher ──────────────────────────────────────────────────────────────

def fetch_github_repo(
    url:          str,
    token:        Optional[str]  = None,
    temp_base:    Optional[str]  = None,
    session_id:   Optional[str]  = None,
    file_filter:  Optional[list] = None,   # e.g. ["*.py"] — future use
) -> GitHubFetchResult:
    """
    Fetch a GitHub repository (or single file) to a local temp directory.

    Args:
        url:        GitHub URL (repo, branch, file, or subfolder)
        token:      GitHub Personal Access Token (for private repos / higher rate limits)
        temp_base:  Base directory for temp files (defaults to ../temp_uploads)
        session_id: Job ID to use as subfolder name
        file_filter: Reserved for future extension filtering

    Returns:
        GitHubFetchResult with local_path pointing to the downloaded files.
    """
    import uuid

    # ── Setup temp directory ──────────────────────────────────────────────────
    if temp_base is None:
        temp_base = str(Path(__file__).resolve().parent.parent / "temp_uploads")

    sid         = session_id or str(uuid.uuid4())
    local_root  = Path(temp_base) / sid
    local_root.mkdir(parents=True, exist_ok=True)

    # ── Parse URL ─────────────────────────────────────────────────────────────
    try:
        parts = _parse_github_url(url)
    except ValueError as e:
        return GitHubFetchResult(
            success=False, local_path="", repo_name="", owner="",
            branch="", detected_language="python", file_count=0,
            total_bytes=0, error=str(e),
        )

    owner  = parts["owner"]
    repo   = parts["repo"]
    branch = parts["branch"]
    kind   = parts["type"]
    subpath = parts["path"]

    print(f"  [GitHub] Fetching {owner}/{repo} @ {branch} (type={kind}, path='{subpath}')")

    client = GitHubAPIClient(token=token)

    # ── Resolve default branch if needed ─────────────────────────────────────
    try:
        repo_meta = client.get_repo(owner, repo)
        if branch == "main" and kind == "repo":
            branch = repo_meta.get("default_branch", "main")
            print(f"  [GitHub] Default branch resolved to: '{branch}'")
    except ValueError as e:
        return GitHubFetchResult(
            success=False, local_path="", repo_name=repo, owner=owner,
            branch=branch, detected_language="python", file_count=0,
            total_bytes=0, error=str(e),
        )
    except Exception as e:
        return GitHubFetchResult(
            success=False, local_path="", repo_name=repo, owner=owner,
            branch=branch, detected_language="python", file_count=0,
            total_bytes=0, error=f"GitHub API error: {e}",
        )

    # ── Single file download ──────────────────────────────────────────────────
    if kind == "blob":
        try:
            content = client.get_file_content(owner, repo, subpath, branch)
            if content is None:
                return GitHubFetchResult(
                    success=False, local_path="", repo_name=repo, owner=owner,
                    branch=branch, detected_language="python", file_count=0,
                    total_bytes=0, error=f"File not found: {subpath}",
                )
            dest = local_root / Path(subpath).name
            dest.write_bytes(content)
            lang = EXT_TO_LANGUAGE.get(Path(subpath).suffix.lower(), "python")
            print(f"  [GitHub] Single file downloaded: {dest.name} ({len(content)} bytes)")
            return GitHubFetchResult(
                success=True, local_path=str(dest), repo_name=repo, owner=owner,
                branch=branch, detected_language=lang, file_count=1,
                total_bytes=len(content), files_fetched=[str(dest)],
            )
        except Exception as e:
            return GitHubFetchResult(
                success=False, local_path="", repo_name=repo, owner=owner,
                branch=branch, detected_language="python", file_count=0,
                total_bytes=0, error=f"Failed to download file: {e}",
            )

    # ── Full repo / subfolder download ────────────────────────────────────────
    try:
        print(f"  [GitHub] Fetching file tree for '{owner}/{repo}' @ '{branch}'...")
        all_blobs = client.get_tree(owner, repo, branch)
    except Exception as e:
        return GitHubFetchResult(
            success=False, local_path="", repo_name=repo, owner=owner,
            branch=branch, detected_language="python", file_count=0,
            total_bytes=0, error=f"Failed to fetch repo tree: {e}",
        )

    # Filter to subfolder if URL pointed to one
    if subpath:
        all_blobs = [b for b in all_blobs if b["path"].startswith(subpath + "/") or b["path"] == subpath]
        print(f"  [GitHub] Subfolder filter '{subpath}': {len(all_blobs)} files")

    # Filter to supported source code extensions only
    source_blobs = [
        b for b in all_blobs
        if Path(b["path"]).suffix.lower() in SUPPORTED_EXTENSIONS
        and not _should_skip(b["path"])
        and b.get("size", 0) <= MAX_FILE_SIZE_BYTES
    ]

    print(f"  [GitHub] {len(all_blobs)} total blobs → {len(source_blobs)} source files to fetch")

    if not source_blobs:
        return GitHubFetchResult(
            success=False, local_path="", repo_name=repo, owner=owner,
            branch=branch, detected_language="python", file_count=0,
            total_bytes=0,
            error="No supported source files found. Supported: .py .js .ts .java .cpp .go .rb .rs .php .cs",
        )

    # Sort by size ascending so small files come first (faster for rate-limited API)
    source_blobs.sort(key=lambda b: b.get("size", 0))
    source_blobs = source_blobs[:MAX_TOTAL_FILES]

    # Download each file
    files_fetched  = []
    total_bytes    = 0
    skipped        = 0

    for blob in source_blobs:
        if total_bytes >= MAX_TOTAL_BYTES:
            print(f"  [GitHub] Total size limit reached ({MAX_TOTAL_BYTES // 1024}KB). Stopping.")
            break

        file_path = blob["path"]
        try:
            content = client.get_file_content(owner, repo, file_path, branch)
            if content is None:
                skipped += 1
                continue

            dest = local_root / file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            files_fetched.append(str(dest))
            total_bytes += len(content)

        except Exception as e:
            print(f"  [GitHub] ✗ Could not fetch {file_path}: {e}")
            skipped += 1
            continue

    if not files_fetched:
        return GitHubFetchResult(
            success=False, local_path="", repo_name=repo, owner=owner,
            branch=branch, detected_language="python", file_count=0,
            total_bytes=0, error="All files failed to download. Check your token or try again.",
        )

    detected_lang = _detect_language(files_fetched)

    print(f"  [GitHub] ✓ Done: {len(files_fetched)} files, "
          f"{total_bytes // 1024}KB, lang={detected_lang}, skipped={skipped}")

    # Check API rate limit and warn
    try:
        rl = client.get_rate_limit()
        remaining = rl.get("remaining", "?")
        print(f"  [GitHub] API rate limit remaining: {remaining}/5000")
        if isinstance(remaining, int) and remaining < 50:
            print("  [GitHub] ⚠️  Rate limit low! Provide GITHUB_TOKEN for 5000 req/hr.")
    except Exception:
        pass

    return GitHubFetchResult(
        success=True,
        local_path=str(local_root),
        repo_name=repo,
        owner=owner,
        branch=branch,
        detected_language=detected_lang,
        file_count=len(files_fetched),
        total_bytes=total_bytes,
        files_fetched=files_fetched,
    )


# ── URL Validator (used by /analyze/github/validate endpoint) ─────────────────

def validate_github_url(url: str, token: Optional[str] = None) -> dict:
    """
    Quickly validates a GitHub URL without downloading files.
    Returns: { valid, owner, repo, branch, type, message }
    """
    try:
        parts  = _parse_github_url(url)
        client = GitHubAPIClient(token=token)
        meta   = client.get_repo(parts["owner"], parts["repo"])
        rl     = client.get_rate_limit()

        return {
            "valid":        True,
            "owner":        parts["owner"],
            "repo":         parts["repo"],
            "branch":       meta.get("default_branch", parts["branch"]),
            "type":         parts["type"],
            "description":  meta.get("description", ""),
            "stars":        meta.get("stargazers_count", 0),
            "language":     (meta.get("language") or "unknown").lower(),
            "private":      meta.get("private", False),
            "rate_limit_remaining": rl.get("remaining", "unknown"),
            "message":      "Repository found and accessible.",
        }
    except ValueError as e:
        return {"valid": False, "message": str(e)}
    except Exception as e:
        return {"valid": False, "message": f"Could not reach GitHub API: {e}"}
