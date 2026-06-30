"""Tests for bot polling configuration and error handling."""
from unittest.mock import Mock, patch, AsyncMock
import pytest
from telegram.error import Conflict


def test_run_polling_called_with_drop_pending_updates():
    """Test that run_polling is invoked with drop_pending_updates=True to prevent stale instance conflicts."""
    from bolao import bot

    with patch('bolao.bot.Application') as MockApp:
        mock_app_instance = Mock()
        MockApp.builder.return_value.token.return_value.post_init.return_value.post_shutdown.return_value.build.return_value = mock_app_instance
        mock_app_instance.run_polling = Mock()

        # Call main (which calls build_app and run_polling)
        bot.main()

        # Assert run_polling was called with drop_pending_updates=True
        mock_app_instance.run_polling.assert_called_once()
        call_kwargs = mock_app_instance.run_polling.call_args.kwargs
        assert call_kwargs.get('drop_pending_updates') is True, \
            f"run_polling must be called with drop_pending_updates=True, got {call_kwargs}"


def test_polling_includes_allowed_updates():
    """Test that run_polling still includes the allowed_updates parameter."""
    from bolao import bot

    with patch('bolao.bot.Application') as MockApp:
        mock_app_instance = Mock()
        MockApp.builder.return_value.token.return_value.post_init.return_value.post_shutdown.return_value.build.return_value = mock_app_instance
        mock_app_instance.run_polling = Mock()

        bot.main()

        call_kwargs = mock_app_instance.run_polling.call_args.kwargs
        assert call_kwargs.get('allowed_updates') == ["message", "callback_query"], \
            f"run_polling must allow message and callback_query updates, got {call_kwargs}"
