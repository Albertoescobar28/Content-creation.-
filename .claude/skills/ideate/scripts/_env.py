"""Tiny .env loader shared by the ideate scripts, so /ideate works
without the student having to manually export environment variables.
No external dependency (python-dotenv) required.
"""
import os
from pathlib import Path


def load_dotenv():
    # Walk up from this file to find a .env at the repo root.
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        env_path = parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
            return


load_dotenv()
