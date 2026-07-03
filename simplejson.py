"""Minimal fallback shim for environments without the external simplejson package.

The project code imports `simplejson` directly. This local module provides the
subset used in the codebase by delegating to Python's stdlib `json` module.
"""

from __future__ import annotations

import json as _json
from typing import Any, IO

JSONDecodeError = _json.JSONDecodeError


def load(fp: IO[str], *args: Any, **kwargs: Any) -> Any:
    return _json.load(fp, *args, **kwargs)


def loads(s: str | bytes | bytearray, *args: Any, **kwargs: Any) -> Any:
    return _json.loads(s, *args, **kwargs)


def dump(obj: Any, fp: IO[str], *args: Any, **kwargs: Any) -> None:
    _json.dump(obj, fp, *args, **kwargs)


def dumps(obj: Any, *args: Any, **kwargs: Any) -> str:
    return _json.dumps(obj, *args, **kwargs)

