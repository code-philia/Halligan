"""
Runtime utilities for Halligan.

This package contains the safe execution path that replaces `exec()`/`eval()` usage
in the original research prototype. The goal is to keep the system runnable while
eliminating Remote Code Execution (RCE) primitives when processing model outputs.
"""
