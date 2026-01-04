import pytest
from unittest.mock import MagicMock
from src.user_manager import UserManager


@pytest.fixture
def user_manager():
    manager = UserManager()
    manager.users = {}
    return manager

def test_user_manager_is_singleton():
    manager1 = UserManager()
    manager2 = UserManager()
    assert manager1 is manager2

def test_add_and_get_user(user_manager):
    mock_session = MagicMock()
    user_manager.add_user("Wojtek", mock_session)

    assert "wojtek" in user_manager.users
    assert user_manager.get_session("wojtek") == mock_session

def test_is_nick_taken(user_manager):
    mock_session = MagicMock()
    user_manager.add_user("Hubert", mock_session)

    assert user_manager.is_nick_taken("Hubert") is True
    assert user_manager.is_nick_taken("Zdzislaw") is False

def test_nick_case_insensitivity(user_manager):
    mock_session = MagicMock()
    user_manager.add_user("Wojtek", mock_session)

    assert user_manager.is_nick_taken("wojtek") is True
    assert user_manager.is_nick_taken("WOJTEK") is True
    assert user_manager.get_session("wOjTeK") == mock_session

def test_change_nick(user_manager):
    mock_session = MagicMock()
    user_manager.add_user("OldNickname", mock_session)

    user_manager.change_nick("OldNickname", "NewNickname")

    assert user_manager.get_session("NewNickname") == mock_session
    assert user_manager.get_session("OldNickname") is None
    assert user_manager.is_nick_taken("OldNickname") is False

def test_remove_user(user_manager):
    mock_session = MagicMock()
    user_manager.add_user("Wojtek", mock_session)
    user_manager.remove_user("Wojtek")

    assert user_manager.get_session("Wojtek") is None
    assert len(user_manager.users) == 0

def test_add_duplicate_user_raises_error(user_manager):
    session1 = MagicMock()
    session2 = MagicMock()

    user_manager.add_user("Wojtek", session1)

    with pytest.raises(ValueError, match="already in use"):
        user_manager.add_user("WOJTEK", session2)

    assert user_manager.get_session("wojtek") == session1
