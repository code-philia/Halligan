from __future__ import annotations

import pytest

from halligan.runtime.config import RuntimeConfig
from halligan.runtime.errors import UnsafeTargetError


def test_local_benchmark_allowed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BENCHMARK_URL", "http://127.0.0.1:3334")
    monkeypatch.delenv("HALLIGAN_ALLOW_NONLOCAL_BENCHMARK", raising=False)
    cfg = RuntimeConfig.from_env()
    cfg.validate()


def test_nonlocal_benchmark_blocked(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BENCHMARK_URL", "http://example.com")
    monkeypatch.delenv("HALLIGAN_ALLOW_NONLOCAL_BENCHMARK", raising=False)
    cfg = RuntimeConfig.from_env()
    with pytest.raises(UnsafeTargetError):
        cfg.validate()


def test_nonlocal_benchmark_allowed_with_override(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BENCHMARK_URL", "http://example.com")
    monkeypatch.setenv("HALLIGAN_ALLOW_NONLOCAL_BENCHMARK", "1")
    cfg = RuntimeConfig.from_env()
    cfg.validate()


def test_local_browser_allowed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BROWSER_URL", "ws://127.0.0.1:5001/")
    monkeypatch.delenv("HALLIGAN_ALLOW_NONLOCAL_BROWSER", raising=False)
    cfg = RuntimeConfig.from_env()
    cfg.validate()


def test_nonlocal_browser_blocked(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BROWSER_URL", "ws://example.com:5001/")
    monkeypatch.delenv("HALLIGAN_ALLOW_NONLOCAL_BROWSER", raising=False)
    cfg = RuntimeConfig.from_env()
    with pytest.raises(UnsafeTargetError):
        cfg.validate()


def test_nonlocal_browser_allowed_with_override(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BROWSER_URL", "ws://example.com:5001/")
    monkeypatch.setenv("HALLIGAN_ALLOW_NONLOCAL_BROWSER", "1")
    cfg = RuntimeConfig.from_env()
    cfg.validate()
