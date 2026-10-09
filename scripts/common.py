"""Shared helpers: paths, typed failures, provenance hash, cached HTTP through curl, budget counters."""
import hashlib, json, os, subprocess, time, urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_AGENT = "accel-trends/1.0"


def _load_config():
    """Machine-specific paths live in config.local.json (not committed); see config.example.json."""
    path = os.path.join(REPO, "config.local.json")
    if not os.path.exists(path):
        raise SystemExit(f"missing {path}: copy config.example.json and set data_dir and corpus_index")
    return json.load(open(path))


CONFIG = _load_config()
DATA = CONFIG["data_dir"]            # private material: API caches, abstracts, idea cards
CORPUS_INDEX = CONFIG["corpus_index"]  # the four-venue index built by the eda_paper scripts


class TypedFailure(Exception):
    """A result that must not be read as a number. `kind` is the typed reason (VF-2)."""

    def __init__(self, kind, detail=""):
        super().__init__(f"{kind}: {detail}")
        self.kind, self.detail = kind, detail


def code_hash():
    """sha256 over the scripts that produce results: identifies the code even when the tree is dirty or uncommitted."""
    digest = hashlib.sha256()
    script_dir = os.path.join(REPO, "scripts")
    for name in sorted(os.listdir(script_dir)):
        if name.endswith(".py"):
            digest.update(name.encode())
            digest.update(open(f"{script_dir}/{name}", "rb").read())
    return digest.hexdigest()[:12]


def spend(counter, amount=1):
    """Budgets are caps: exceeding one is an error, not a warning."""
    path = os.path.join(DATA, "data", "budget.json")
    budget = json.load(open(path))
    entry = budget[counter]
    if entry["used"] + amount > entry["cap"]:
        raise TypedFailure("BUDGET_EXCEEDED", f"{counter}: {entry['used']}+{amount} > {entry['cap']}")
    entry["used"] += amount
    json.dump(budget, open(path, "w"), indent=1)


def get_json(base_url, params, cache_name=None, pause=0.25, attempts=6):
    """GET through curl (urllib is refused by some hosts) with an on-disk cache and backoff.

    curl's exit code is checked as well as the HTTP status: a timed-out transfer still prints 200.
    """
    if cache_name:
        cache_path = os.path.join(DATA, "raw", "openalex", f"{cache_name}.json")
        if os.path.exists(cache_path):
            return json.load(open(cache_path))
    url = base_url + "?" + urllib.parse.urlencode(params)
    for attempt in range(attempts):
        result = subprocess.run(["curl", "-sL", "--max-time", "120", "-A", USER_AGENT, "-w", "\n%{http_code}", url],
                                capture_output=True, timeout=150)
        body, _, status = result.stdout.decode(errors="replace").rpartition("\n")
        if result.returncode == 0 and status == "200":
            payload = json.loads(body)
            if cache_name:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                json.dump(payload, open(cache_path + ".tmp", "w"))
                os.replace(cache_path + ".tmp", cache_path)
            spend("api_calls")
            time.sleep(pause)
            return payload
        if status in ("429", "500", "502", "503", "504") or result.returncode != 0:
            time.sleep(4 * (attempt + 1))
            continue
        raise TypedFailure("HTTP_ERROR", f"{status} for {url[:160]}")
    raise TypedFailure("HTTP_RETRIES_EXHAUSTED", url[:160])


def wilson(successes, total, z=1.96):
    """Wilson 95% interval for a share; (None, None) when the arm-year is empty."""
    if total == 0:
        return None, None
    p = successes / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / (1 + z * z / total)
    return max(0.0, centre - half), min(1.0, centre + half)
