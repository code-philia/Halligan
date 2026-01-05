from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from halligan.runtime.errors import ConfigError, UnsafeTargetError

_DEFAULT_ALLOWED_BENCHMARK_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "host.docker.internal",
}

_DEFAULT_ALLOWED_BROWSER_HOSTS = set(_DEFAULT_ALLOWED_BENCHMARK_HOSTS)


def _is_local_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    host = (parsed.hostname or "").strip().lower()
    return host in _DEFAULT_ALLOWED_BENCHMARK_HOSTS


def _is_local_ws_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in {"ws", "wss"}:
        return False

    host = (parsed.hostname or "").strip().lower()
    return host in _DEFAULT_ALLOWED_BROWSER_HOSTS


@dataclass(frozen=True)
class RuntimeConfig:
    """
    Centralized runtime configuration.

    Notes
    - Network access is not restricted by the code itself; therefore we enforce a
      conservative default: only allow local benchmark endpoints unless explicitly
      overridden by the user.
    - This project is a research prototype. Enforcing safer defaults helps prevent
      accidental misuse and reduces blast radius of bugs.
    """

    openai_api_key: str | None
    browser_url: str | None
    benchmark_url: str | None
    benchmark_http_url: str | None
    allow_nonlocal_benchmark: bool = False
    allow_nonlocal_browser: bool = False

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        allow_nonlocal = os.getenv("HALLIGAN_ALLOW_NONLOCAL_BENCHMARK", "").strip()
        # Backward/alternate naming support
        if not allow_nonlocal:
            allow_nonlocal = os.getenv("ALLOW_NONLOCAL_BENCHMARK", "").strip()

        allow_nonlocal_benchmark = allow_nonlocal in {"1", "true", "True", "yes", "YES"}

        allow_nonlocal_browser = os.getenv("HALLIGAN_ALLOW_NONLOCAL_BROWSER", "").strip()
        if not allow_nonlocal_browser:
            allow_nonlocal_browser = os.getenv("ALLOW_NONLOCAL_BROWSER", "").strip()
        allow_nonlocal_browser = allow_nonlocal_browser in {"1", "true", "True", "yes", "YES"}

        benchmark_url = os.getenv("BENCHMARK_URL")
        benchmark_http_url = os.getenv("BENCHMARK_HTTP_URL", benchmark_url)

        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            browser_url=os.getenv("BROWSER_URL"),
            benchmark_url=benchmark_url,
            benchmark_http_url=benchmark_http_url,
            allow_nonlocal_benchmark=allow_nonlocal_benchmark,
            allow_nonlocal_browser=allow_nonlocal_browser,
        )

    def validate(self) -> None:
        """Validate presence and safety of the runtime configuration."""
        if self.browser_url and not self.allow_nonlocal_browser:
            if not _is_local_ws_url(self.browser_url):
                raise UnsafeTargetError(
                    "Detected non-local `BROWSER_URL`. For safety, Halligan only allows local "
                    "Playwright websocket endpoints by default.\n"
                    f"- Current: {self.browser_url!r}\n"
                    "- To override intentionally, set `HALLIGAN_ALLOW_NONLOCAL_BROWSER=1`."
                )

        if self.benchmark_url and not self.allow_nonlocal_benchmark:
            if not _is_local_http_url(self.benchmark_url):
                raise UnsafeTargetError(
                    "Detected non-local `BENCHMARK_URL`. For safety, Halligan only allows local "
                    "benchmark endpoints by default.\n"
                    f"- Current: {self.benchmark_url!r}\n"
                    "- To override intentionally, set `HALLIGAN_ALLOW_NONLOCAL_BENCHMARK=1`."
                )

        if self.benchmark_http_url and not self.allow_nonlocal_benchmark:
            if not _is_local_http_url(self.benchmark_http_url):
                raise UnsafeTargetError(
                    "Detected non-local `BENCHMARK_HTTP_URL`. For safety, Halligan only allows local "
                    "benchmark endpoints by default.\n"
                    f"- Current: {self.benchmark_http_url!r}\n"
                    "- To override intentionally, set `HALLIGAN_ALLOW_NONLOCAL_BENCHMARK=1`."
                )

        # We don't hard-fail on missing keys here because some unit tests and workflows
        # intentionally skip agent/model integration. Call sites should validate their needs.

    def require(self, *, browser: bool = False, benchmark: bool = False, openai: bool = False) -> None:
        """Require specific settings for a given command."""
        missing: list[str] = []
        if browser and not self.browser_url:
            missing.append("BROWSER_URL")
        if benchmark and not self.benchmark_url:
            missing.append("BENCHMARK_URL")
        if openai and not self.openai_api_key:
            missing.append("OPENAI_API_KEY")

        if missing:
            raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")
