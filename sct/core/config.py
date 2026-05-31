from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_INCLUDE_SUFFIXES = (
    ".py",
    ".pyi",
    ".rs",
    ".go",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".java",
    ".kt",
    ".lua",
    ".vim",
    ".sh",
    ".bash",
    ".zsh",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".sql",
    ".rb",
    ".php",
    ".swift",
    ".scala",
    ".cs",
    ".html",
    ".css",
    ".scss",
)

DEFAULT_EXCLUDE_DIRS = (
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".sct",
)


@dataclass
class Config:
    root: Path
    cache_path: Path = field(default_factory=lambda: Path(".sct/cache.json"))
    config_path: Path = field(default_factory=lambda: Path(".sct/config.json"))
    include_suffixes: tuple[str, ...] = DEFAULT_INCLUDE_SUFFIXES
    exclude_dirs: tuple[str, ...] = DEFAULT_EXCLUDE_DIRS

    @classmethod
    def discover(cls, root: Path | None = None) -> Config:
        root = (root or Path.cwd()).resolve()
        cfg = cls(root=root, cache_path=root / ".sct" / "cache.json", config_path=root / ".sct" / "config.json")
        if cfg.config_path.is_file():
            cfg._load_file()
        return cfg

    def _load_file(self) -> None:
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        if "include_suffixes" in data:
            self.include_suffixes = tuple(data["include_suffixes"])
        if "exclude_dirs" in data:
            self.exclude_dirs = tuple(data["exclude_dirs"])
        if "cache_path" in data:
            p = Path(data["cache_path"])
            self.cache_path = p if p.is_absolute() else self.root / p

    def ensure_dirs(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
