import threading
from unittest.mock import AsyncMock, patch

import pytest

from kwtsms import AsyncKwtSMS, _async
# 2026-11-05 07:08 +03: tests that send take the num fixture (KWTSMS_TEST_NUMBER, conftest.py) and skip
# when it is unset; no phone number is written here (int-testnumber).

def _async_client(**kwargs) -> AsyncKwtSMS:
    defaults = dict(username="python_username", password="python_password",
                    sender_id="TEST", log_file="")
    defaults.update(kwargs)
    return AsyncKwtSMS(**defaults)

OK_VERIFY = {"result": "OK", "available": 150.0, "purchased": 200.0}
OK_SEND   = {"result": "OK", "msg-id": "abc123", "numbers": 1,
             "points-charged": 1, "balance-after": 149.0}

class TestAsyncKwtSMS:
    def test_constructor_requires_username_and_password(self):
        with pytest.raises(ValueError):
            AsyncKwtSMS(username="", password="x")

    @pytest.mark.asyncio
    async def test_verify_ok(self):
        with patch("kwtsms._async._async_request", new_callable=AsyncMock,
                   return_value=OK_VERIFY):
            ok, balance, error = await _async_client().verify()
        assert ok is True
        assert balance == 150.0
        assert error is None

    @pytest.mark.asyncio
    async def test_send_ok(self, num):
        with patch("kwtsms._async._async_request", new_callable=AsyncMock,
                   return_value=OK_SEND):
            result = await _async_client().send(num, "Hello")
        assert result["result"] == "OK"
        assert result["msg-id"] == "abc123"

    @pytest.mark.asyncio
    async def test_send_invalid_phone_returns_error_without_api_call(self):
        result = await _async_client().send("abc", "Hello")
        assert result["result"] == "ERROR"
        assert result["code"] == "ERR_INVALID_INPUT"

    @pytest.mark.asyncio
    async def test_send_emoji_only_returns_err009_without_api_call(self, num):
        result = await _async_client().send(num, "👋🔥")
        assert result["result"] == "ERROR"
        assert result["code"] == "ERR009"

    @pytest.mark.asyncio
    async def test_verify_network_error_returns_false(self):
        with patch("kwtsms._async._async_request", new_callable=AsyncMock,
                   side_effect=RuntimeError("Timeout")):
            ok, balance, error = await _async_client().verify()
        assert ok is False
        assert "Timeout" in error

    @pytest.mark.asyncio
    async def test_send_too_many_numbers_returns_err007(self):
        numbers = [f"9659{i:07d}" for i in range(201)]
        result = await _async_client().send(numbers, "Hello")
        assert result["result"] == "ERROR"
        assert result["code"] == "ERR007"


# 2026-11-07 01:56 +03: the async log write must leave the event loop thread (task py-async-log-blocking).
@pytest.mark.asyncio
async def test_async_log_write_runs_off_the_event_loop_thread(tmp_path):
    seen = []
    with patch.object(_async, "_write_log", side_effect=lambda f, e: seen.append(threading.get_ident())):
        await _async._awrite_log(str(tmp_path / "k.log"), {"x": 1})
    assert seen and seen[0] != threading.get_ident()


@pytest.mark.asyncio
async def test_async_log_write_skipped_when_logging_off():
    with patch.object(_async, "_write_log") as w:
        await _async._awrite_log("", {"x": 1})
    w.assert_not_called()
