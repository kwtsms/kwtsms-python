"""
FILE:      tests/test_user_agent.py
CREATED:   2026-11-05 14:14 +03
TASK:      Vikunja #939 (int-measure-signups)
AUTHOR:    M Alhassoun
WHAT:      Unit tests for the User-Agent kwtsms-python/<version> and the optional app token.
WHY:       kwtSMS counts accounts per integration from the User-Agent; it must be exact and header-safe.
USAGE:     .venv/bin/python -m pytest tests/test_user_agent.py
DEPENDS:   pytest, pytest-asyncio and aiohttp for the async test; no network (urlopen and aiohttp are mocked).
"""

import json
import re
from unittest.mock import MagicMock, patch

import pytest

import kwtsms
from kwtsms import AsyncKwtSMS, KwtSMS
from kwtsms._core import _build_user_agent

LIB = "kwtsms-python/" + kwtsms.__version__
OK_BALANCE = {"result": "OK", "available": 1, "purchased": 1}


def _client(**kwargs) -> KwtSMS:
    return KwtSMS("python_username", "python_password", log_file="", **kwargs)


def test_default_user_agent_is_library_token():
    ua = _client().user_agent
    assert ua == LIB
    assert re.fullmatch(r"kwtsms-python/[0-9][0-9A-Za-z.+-]*", ua)


def test_app_token_is_prepended():
    assert _client(app_name="kwtsms-wordpress/3.5.2").user_agent == "kwtsms-wordpress/3.5.2 " + LIB
    assert AsyncKwtSMS("python_username", "python_password", log_file="",
                       app_name="my-shop/2.1.0").user_agent == "my-shop/2.1.0 " + LIB


def test_app_token_is_sanitized():
    ua = _build_user_agent("my app\r\nX-Injected: 1")
    assert "\r" not in ua and "\n" not in ua
    assert " X-Injected" not in ua
    assert ua.endswith(" " + LIB)
    assert _build_user_agent("  - -  ") == LIB
    assert len(_build_user_agent("a" * 200).split(" ")[0]) == 64


def test_header_is_sent_on_request():
    resp = MagicMock()
    resp.read.return_value = json.dumps(OK_BALANCE).encode("utf-8")
    resp.__enter__.return_value = resp
    with patch("kwtsms._core.urlopen", return_value=resp) as mock_open:
        ok, _, _ = _client(app_name="my-shop/2.1.0").verify()
    assert ok is True
    req = mock_open.call_args.args[0]
    assert req.get_header("User-agent") == "my-shop/2.1.0 " + LIB


@pytest.mark.asyncio
async def test_header_is_sent_on_async_request():
    sent = {}

    class _Resp:
        async def text(self):
            return json.dumps(OK_BALANCE)

    class _Ctx:
        def __init__(self, obj):
            self.obj = obj

        async def __aenter__(self):
            return self.obj

        async def __aexit__(self, *exc):
            return False

    class _Session:
        def post(self, url, **kwargs):
            sent.update(kwargs.get("headers") or {})
            return _Ctx(_Resp())

    with patch("kwtsms._async.aiohttp.ClientSession", return_value=_Ctx(_Session())):
        ok, _, _ = await AsyncKwtSMS("python_username", "python_password", log_file="").verify()
    assert ok is True
    assert sent.get("User-Agent") == LIB
