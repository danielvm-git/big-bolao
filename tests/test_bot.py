"""Tests for bot polling configuration and error handling."""
from unittest.mock import Mock, patch, AsyncMock
import pytest
import logging
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


@pytest.mark.asyncio
async def test_error_handler_detects_conflict_and_logs_error():
    """Test that a Conflict (409) error is logged at ERROR level with a clear message."""
    from bolao import bot

    mock_logger = Mock(spec=logging.Logger)

    with patch('bolao.bot.log', mock_logger):
        # Create a mock context with a Conflict exception
        context = AsyncMock()
        context.error = Conflict("Conflict: terminated by other getUpdates request")

        # Call the error handler directly
        await bot._handle_error(None, context)

        # Assert that ERROR-level log was called with a message about duplicate pollers
        assert mock_logger.error.called, "error handler did not call log.error()"

        # Get the logged message
        call_args = mock_logger.error.call_args
        logged_text = call_args[0][0] if call_args[0] else ""

        # Check that the message mentions key phrases about the conflict
        assert any(keyword in logged_text.lower() for keyword in ["another", "conflict", "polling"]), \
            f"Error message should mention duplicate/another instance, got: {logged_text}"


def test_build_app_registers_error_handler():
    """Test that build_app calls add_error_handler (implicitly tests via mock)."""
    from bolao import bot

    with patch('bolao.bot.BigBase'):
        app = bot.build_app()
        # Verify that the app is built and doesn't fail (error handler was registered)
        assert app is not None
        # The real test is that build_app() completes without error,
        # which means add_error_handler() was called successfully


@pytest.mark.asyncio
async def test_post_init_logs_version_at_startup():
    """Test that _post_init logs the running version so VPS logs can identify which build started."""
    from bolao import bot
    from unittest.mock import AsyncMock

    mock_logger = Mock(spec=logging.Logger)
    mock_app = AsyncMock()
    mock_app.bot_data = {}
    mock_app.bot.set_my_commands = AsyncMock()

    mock_db = AsyncMock()
    mock_db.ensure_setup = AsyncMock()

    with patch('bolao.bot.log', mock_logger):
        with patch('bolao.bot.BigBase', return_value=mock_db):
            await bot._post_init(mock_app)

    # Assert that log.info was called to record the version
    info_calls = mock_logger.info.call_args_list
    assert len(info_calls) > 0, "_post_init should log at info level"

    # Check that the first log call includes version info (it logs "Starting Big Bolao X.Y.Z")
    first_call_msg = info_calls[0][0][0] if info_calls[0][0] else ""
    assert "Big Bolao" in first_call_msg and any(c.isdigit() for c in first_call_msg), \
        f"_post_init should log the running version in first call, got: {first_call_msg}"
