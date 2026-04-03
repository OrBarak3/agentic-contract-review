from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    runtime_dir: Path
    audit_dir: Path
    reports_dir: Path
    audit_db_path: Path
    audit_log_path: Path
    default_policy_path: Path


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_paths() -> AppPaths:
    root = get_repo_root()
    runtime_dir = root / "runtime"
    audit_dir = runtime_dir / "audit"
    reports_dir = runtime_dir / "reports"
    return AppPaths(
        root=root,
        runtime_dir=runtime_dir,
        audit_dir=audit_dir,
        reports_dir=reports_dir,
        audit_db_path=audit_dir / "audit.sqlite3",
        audit_log_path=audit_dir / "events.jsonl",
        default_policy_path=root / "policies" / "default_policy.yaml",
    )


def ensure_runtime_dirs() -> AppPaths:
    paths = get_paths()
    for directory in (paths.runtime_dir, paths.audit_dir, paths.reports_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return paths


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

