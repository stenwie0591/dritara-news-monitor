from pydantic import SecretStr

from src.bot import is_authorized_admin
from src.config import RuntimeSettings


def settings() -> RuntimeSettings:
    return RuntimeSettings(
        _env_file=None,
        telegram_bot_token=SecretStr("token"),
        telegram_admin_chat_id=100,
        telegram_admin_user_id=200,
        telegram_community_chat_id=-1000,
        telegram_news_thread_id=2,
    )


def message_update(*, chat_id=100, user_id=200, chat_type="private") -> dict:
    return {
        "message": {
            "chat": {"id": chat_id, "type": chat_type},
            "from": {"id": user_id},
            "text": "/status",
        }
    }


def callback_update(*, chat_id=100, user_id=200, chat_type="private") -> dict:
    return {
        "callback_query": {
            "from": {"id": user_id},
            "message": {"chat": {"id": chat_id, "type": chat_type}},
        }
    }


def test_authorizes_expected_user_in_expected_private_chat() -> None:
    assert is_authorized_admin(message_update(), settings())


def test_rejects_same_chat_with_different_user() -> None:
    assert not is_authorized_admin(message_update(user_id=999), settings())


def test_rejects_expected_user_in_different_chat() -> None:
    assert not is_authorized_admin(message_update(chat_id=999), settings())


def test_rejects_group_even_when_ids_match() -> None:
    assert not is_authorized_admin(message_update(chat_type="group"), settings())


def test_callback_uses_same_principal_policy() -> None:
    assert is_authorized_admin(callback_update(), settings())
    assert not is_authorized_admin(callback_update(user_id=999), settings())
