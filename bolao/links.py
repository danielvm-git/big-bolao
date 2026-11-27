"""Signed per-user site links.

The bot sends each user a link with ?uid=<telegram id>&sig=<HMAC>. The server
accepts a bet from the site only when the signature matches, so changing the
uid in the URL no longer lets anyone bet as someone else.
"""
from __future__ import annotations

import hashlib
import hmac

from bolao import config


def sign(uid: int, secret: str | None = None) -> str:
    key = (secret if secret is not None else config.LINK_SECRET).encode()
    if not key:
        raise RuntimeError("BOLAO_LINK_SECRET is not set")
    return hmac.new(key, str(int(uid)).encode(), hashlib.sha256).hexdigest()[:32]


def verify(uid: object, sig: object, secret: str | None = None) -> bool:
    key = secret if secret is not None else config.LINK_SECRET
    if not key or not sig:
        return False
    try:
        expected = sign(int(uid), key)
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(expected, str(sig))
