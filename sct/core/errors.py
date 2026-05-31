from __future__ import annotations

# Exit codes for scripting (documented in README).
EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_STALE = 2
EXIT_IO = 3
EXIT_USAGE = 4


class SctError(Exception):
    """Base error with optional exit code."""

    exit_code: int = EXIT_IO

    def __init__(self, message: str, exit_code: int | None = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class NotFoundError(SctError):
    exit_code = EXIT_NOT_FOUND


class StaleLineError(SctError):
    exit_code = EXIT_STALE


class DuplicateTaskError(SctError):
    exit_code = EXIT_IO
