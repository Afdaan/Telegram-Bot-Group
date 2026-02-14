from __future__ import annotations

from typing import Optional

from telegram import User


_USERNAME_TO_ID: dict[str, int] = {}


def remember_user(user: Optional[User]) -> None:
    if not user:
        return

    username = getattr(user, "username", None)
    user_id = getattr(user, "id", None)
    if not username or not user_id:
        return

    _USERNAME_TO_ID[username.lower()] = int(user_id)


def get_user_id_by_username(username: str) -> int | None:
    if not username:
        return None
    return _USERNAME_TO_ID.get(username.lower())
